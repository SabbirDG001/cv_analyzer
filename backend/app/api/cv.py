from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.db.session import get_db
from app.llm import LLMError, LLMProvider, get_llm
from app.models import Profile
from app.schemas.cv import CvConfirmIn, CvReview
from app.services import cv as service
from app.services import profile as profile_service
from app.services.cv_text import MAX_BYTES, CvFileError
from app.services.storage import CvStorage, StorageError, get_storage

router = APIRouter(prefix="/me", tags=["cv"])

_FILE_ERROR_STATUS = {"too_large": status.HTTP_413_CONTENT_TOO_LARGE}


def _profile(db: Session, user: AuthUser) -> Profile:
    profile = profile_service.get_profile(db, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Complete onboarding first")
    return profile


def _error(code: str, message: str, http: int) -> HTTPException:
    return HTTPException(http, {"code": code, "message": message})


@router.post("/consent", status_code=status.HTTP_204_NO_CONTENT)
def give_consent(
    user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    service.record_consent(db, _profile(db, user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/cv", response_model=CvReview, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    storage: CvStorage = Depends(get_storage),
) -> CvReview:
    profile = _profile(db, user)
    data = await file.read(MAX_BYTES + 1)  # never buffer more than the limit + 1 byte
    try:
        return service.upload_cv(db, profile, data, llm, storage)
    except service.ConsentRequiredError as exc:
        raise _error("consent_required", str(exc), status.HTTP_403_FORBIDDEN) from exc
    except CvFileError as exc:
        http = _FILE_ERROR_STATUS.get(exc.code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        raise _error(exc.code, exc.message, http) from exc
    except LLMError as exc:
        raise _error("parse_failed", str(exc), status.HTTP_502_BAD_GATEWAY) from exc
    except StorageError as exc:
        raise _error("storage_failed", str(exc), status.HTTP_502_BAD_GATEWAY) from exc


@router.get("/cv/latest", response_model=CvReview)
def latest_cv(
    user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> CvReview:
    upload = service.latest_upload(db, user.id)
    if upload is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No CV uploaded yet")
    return service.review_for(db, upload)


@router.get("/cv/latest/url")
def latest_cv_url(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: CvStorage = Depends(get_storage),
) -> dict[str, str]:
    upload = service.latest_upload(db, user.id)
    if upload is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No CV uploaded yet")
    try:
        return {"url": storage.signed_url(upload.storage_path)}
    except StorageError as exc:
        raise _error("storage_failed", str(exc), status.HTTP_502_BAD_GATEWAY) from exc


@router.post("/cv/confirm")
def confirm_cv(
    body: CvConfirmIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    _profile(db, user)
    return {"saved": service.confirm_skills(db, user.id, body.skills)}


@router.delete("/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_data(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: CvStorage = Depends(get_storage),
) -> Response:
    try:
        service.delete_all_user_data(db, user.id, storage)
    except StorageError as exc:
        raise _error("storage_failed", str(exc), status.HTTP_502_BAD_GATEWAY) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
