import { en } from "@/i18n/en";
import { TRACKS, type ProfileInput, type Track } from "@/lib/types";

export interface ProfileForm {
  name: string;
  university: string;
  year: string;
  department: string;
  cgpa: string;
  fieldId: string;
  track: string;
}

export type ProfileErrors = Partial<Record<keyof ProfileForm, string>>;

const errors = en.onboarding.errors;

export function validateProfile(form: ProfileForm): ProfileErrors {
  const result: ProfileErrors = {};
  for (const key of ["name", "university", "department", "fieldId", "track"] as const) {
    if (!form[key].trim()) result[key] = errors.required;
  }
  const year = Number(form.year);
  if (!Number.isInteger(year) || year < 1 || year > 8) result.year = errors.year;
  const cgpa = Number(form.cgpa);
  if (form.cgpa.trim() === "" || Number.isNaN(cgpa) || cgpa < 0 || cgpa > 4) {
    result.cgpa = errors.cgpa;
  }
  if (form.track && !TRACKS.includes(form.track as Track)) result.track = errors.required;
  return result;
}

/** Only call after validateProfile returned no errors. */
export function toProfileInput(form: ProfileForm): ProfileInput {
  return {
    name: form.name.trim(),
    university: form.university.trim(),
    year: Number(form.year),
    department: form.department.trim(),
    cgpa: Number(form.cgpa).toFixed(2),
    track: form.track as Track,
    field_id: Number(form.fieldId),
  };
}
