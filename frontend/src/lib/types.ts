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
