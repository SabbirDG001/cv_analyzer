"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { en } from "@/i18n/en";
import { ApiError, apiFetch } from "@/lib/api";
import { TRACKS, type Field, type Profile } from "@/lib/types";
import {
  toProfileInput,
  validateProfile,
  type ProfileErrors,
  type ProfileForm,
} from "@/lib/validation";

const EMPTY: ProfileForm = {
  name: "",
  university: "",
  year: "",
  department: "",
  cgpa: "",
  fieldId: "",
  track: "",
};

const selectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

export default function OnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState<ProfileForm>(EMPTY);
  const [errors, setErrors] = useState<ProfileErrors>({});
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setFields(await apiFetch<Field[]>("/fields"));
        const existing = await apiFetch<Profile>("/me/profile").catch((e: unknown) => {
          if (e instanceof ApiError && e.status === 404) return null;
          throw e;
        });
        if (existing) {
          setForm({
            name: existing.name,
            university: existing.university,
            year: String(existing.year),
            department: existing.department,
            cgpa: existing.cgpa,
            fieldId: String(existing.field_id),
            track: existing.track,
          });
        }
      } catch {
        setFailure(en.common.genericError);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  function update(key: keyof ProfileForm, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = validateProfile(form);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    setFailure(null);
    try {
      await apiFetch<Profile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify(toProfileInput(form)),
      });
      router.push("/skills");
    } catch (e) {
      setFailure(e instanceof ApiError ? e.message : en.common.genericError);
      setSaving(false);
    }
  }

  if (loading) return <p className="p-8">{en.common.loading}</p>;

  const text = (key: "name" | "university" | "department", label: string) => (
    <div className="flex flex-col gap-2">
      <Label htmlFor={key}>{label}</Label>
      <Input id={key} value={form[key]} onChange={(e) => update(key, e.target.value)} />
      {errors[key] && <p className="text-xs text-red-600">{errors[key]}</p>}
    </div>
  );

  return (
    <main className="p-4">
      <Card className="mx-auto mt-8 w-full max-w-xl">
        <CardHeader>
          <CardTitle>{en.onboarding.title}</CardTitle>
          <p className="text-sm text-muted-foreground">{en.onboarding.subtitle}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
            {text("name", en.onboarding.name)}
            {text("university", en.onboarding.university)}
            {text("department", en.onboarding.department)}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="year">{en.onboarding.year}</Label>
                <Input
                  id="year"
                  type="number"
                  min={1}
                  max={8}
                  value={form.year}
                  onChange={(e) => update("year", e.target.value)}
                />
                {errors.year && <p className="text-xs text-red-600">{errors.year}</p>}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="cgpa">{en.onboarding.cgpa}</Label>
                <Input
                  id="cgpa"
                  inputMode="decimal"
                  value={form.cgpa}
                  onChange={(e) => update("cgpa", e.target.value)}
                />
                {errors.cgpa && <p className="text-xs text-red-600">{errors.cgpa}</p>}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="field">{en.onboarding.field}</Label>
              <select
                id="field"
                className={selectClass}
                value={form.fieldId}
                onChange={(e) => update("fieldId", e.target.value)}
              >
                <option value="">{en.onboarding.fieldPlaceholder}</option>
                {fields.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
              {errors.fieldId && <p className="text-xs text-red-600">{errors.fieldId}</p>}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="track">{en.onboarding.track}</Label>
              <select
                id="track"
                className={selectClass}
                value={form.track}
                onChange={(e) => update("track", e.target.value)}
              >
                <option value="">{en.onboarding.trackPlaceholder}</option>
                {TRACKS.map((t) => (
                  <option key={t} value={t}>
                    {en.onboarding.tracks[t]}
                  </option>
                ))}
              </select>
              {errors.track && <p className="text-xs text-red-600">{errors.track}</p>}
            </div>
            {failure && (
              <p role="alert" className="text-sm text-red-600">
                {failure}
              </p>
            )}
            <Button type="submit" disabled={saving}>
              {saving ? en.common.saving : en.onboarding.submit}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
