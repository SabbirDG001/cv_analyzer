"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CvReviewForm } from "@/components/cv-review";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { en, format } from "@/i18n/en";
import { ApiError, apiFetch } from "@/lib/api";
import type { CvReview, Profile } from "@/lib/types";

function describe(e: unknown): string {
  if (e instanceof ApiError) return (e.code && en.cv.errors[e.code]) || e.message;
  return en.common.genericError;
}

export default function CvPage() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [consented, setConsented] = useState(false);
  const [alreadyConsented, setAlreadyConsented] = useState(false);
  const [review, setReview] = useState<CvReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [savedCount, setSavedCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Profile>("/me/profile")
      .then((p) => setAlreadyConsented(p.consent_at !== null))
      .catch((e: unknown) => {
        if (e instanceof ApiError && e.status === 404) router.replace("/onboarding");
      });
  }, [router]);

  async function upload() {
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await apiFetch<void>("/me/consent", { method: "POST" });
      const form = new FormData();
      form.append("file", file);
      setReview(await apiFetch<CvReview>("/me/cv", { method: "POST", body: form }));
    } catch (e) {
      setError(describe(e));
    } finally {
      setBusy(false);
    }
  }

  async function confirm(skills: { skill_id: number; level: number }[]) {
    setBusy(true);
    setError(null);
    try {
      const res = await apiFetch<{ saved: number }>("/me/cv/confirm", {
        method: "POST",
        body: JSON.stringify({ skills }),
      });
      setSavedCount(res.saved);
      setReview(null);
    } catch (e) {
      setError(describe(e));
    } finally {
      setBusy(false);
    }
  }

  const canUpload = (consented || alreadyConsented) && !busy;

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-4 pt-8">
      <div>
        <h1 className="text-2xl font-bold">{en.cv.title}</h1>
        <p className="text-sm text-muted-foreground">{en.cv.subtitle}</p>
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
      {savedCount !== null && (
        <p role="status" className="text-sm text-green-700">
          {format(en.cv.saved, { count: savedCount })}
        </p>
      )}
      {review ? (
        <CvReviewForm review={review} busy={busy} onConfirm={(s) => void confirm(s)} />
      ) : (
        <Card>
          <CardContent className="flex flex-col gap-4 pt-6">
            {!alreadyConsented && (
              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={consented}
                  onChange={(e) => setConsented(e.target.checked)}
                />
                <span>{en.cv.consent}</span>
              </label>
            )}
            <Label htmlFor="cv-file">{en.cv.chooseFile}</Label>
            <input
              id="cv-file"
              ref={fileInput}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            />
            <Button className="self-start" disabled={!canUpload} onClick={() => void upload()}>
              {busy ? en.cv.uploading : en.cv.upload}
            </Button>
          </CardContent>
        </Card>
      )}
      <Link
        href="/dashboard"
        className={buttonVariants({ variant: "outline", className: "self-start" })}
      >
        {en.skills.next}
      </Link>
    </main>
  );
}
