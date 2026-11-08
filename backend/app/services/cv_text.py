import io

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_BYTES = 5 * 1024 * 1024
MIN_TEXT_CHARS = 80  # below this a PDF is almost certainly a scan or empty

PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"


class CvFileError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def detect_kind(data: bytes) -> str:
    """Sniff the real type from content, not from the filename or client header."""
    if data.startswith(PDF_MAGIC):
        return "pdf"
    if data.startswith(DOCX_MAGIC):
        return "docx"
    raise CvFileError("wrong_file_type", "Upload a PDF or DOCX file.")


def _pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise CvFileError("unreadable", "This PDF is password protected.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except PyPdfError as exc:
        raise CvFileError("unreadable", "We could not read this PDF.") from exc


def _docx_text(data: bytes) -> str:
    try:
        doc = Document(io.BytesIO(data))
    except Exception as exc:  # python-docx raises assorted zip/xml errors
        raise CvFileError("unreadable", "We could not read this DOCX file.") from exc
    parts = [p.text for p in doc.paragraphs]
    parts += [cell.text for t in doc.tables for row in t.rows for cell in row.cells]
    return "\n".join(parts)


def extract_text(data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise CvFileError("too_large", "The file is larger than 5 MB.")
    if not data:
        raise CvFileError("empty", "The file is empty.")
    kind = detect_kind(data)
    text = _pdf_text(data) if kind == "pdf" else _docx_text(data)
    text = text.strip()
    if len(text) < MIN_TEXT_CHARS:
        if kind == "pdf":
            raise CvFileError(
                "no_text",
                "This PDF has no readable text (it may be scanned or blurry). "
                "Export a text-based PDF or upload a DOCX.",
            )
        raise CvFileError("empty", "This CV has almost no text.")
    return text
