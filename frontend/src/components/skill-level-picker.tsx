"use client";

import { en } from "@/i18n/en";
import { cn } from "@/lib/utils";

interface SkillLevelPickerProps {
  value: number | null;
  onChange: (level: number) => void;
  disabled?: boolean;
}

export function SkillLevelPicker({ value, onChange, disabled }: SkillLevelPickerProps) {
  return (
    <div role="group" aria-label={en.skills.levelLabel} className="flex flex-wrap gap-1">
      {en.skills.levels.map((label, level) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          aria-pressed={value === level}
          title={label}
          aria-label={`${level} - ${label}`}
          onClick={() => onChange(level)}
          className={cn(
            "h-8 min-w-8 rounded-md border px-2 text-sm transition-colors",
            value === level
              ? "border-primary bg-primary text-primary-foreground"
              : "hover:bg-muted",
          )}
        >
          {level}
        </button>
      ))}
    </div>
  );
}
