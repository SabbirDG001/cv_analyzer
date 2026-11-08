export type Track = "job" | "research" | "scholarship";

export const TRACKS: readonly Track[] = ["job", "research", "scholarship"];

export interface Field {
  id: number;
  slug: string;
  name: string;
}

export interface Skill {
  id: number;
  name: string;
  category: string;
  aliases: string[];
}

export interface ProfileInput {
  name: string;
  university: string;
  year: number;
  department: string;
  cgpa: string;
  track: Track;
  field_id: number;
}

export interface Profile extends ProfileInput {
  id: string;
  consent_at: string | null;
}

export type SkillSource = "cv" | "manual" | "quiz";

export interface ProfileSkill {
  skill_id: number;
  name: string;
  level: number;
  source: SkillSource;
}

export interface CvSkillMatch {
  skill_id: number;
  name: string;
  level: number;
  evidence: string;
}

export interface CvSkillUnmatched {
  name: string;
  level: number;
  evidence: string;
}

export interface ParsedCv {
  cgpa: number | null;
  projects: { title: string; summary: string }[];
  experience: { role: string; organization: string; summary: string }[];
  languages: string[];
  test_scores: { test: string; score: string }[];
  interests: string[];
}

export interface CvReview {
  cv_id: string;
  parsed: ParsedCv;
  matched: CvSkillMatch[];
  unmatched: CvSkillUnmatched[];
}
