"use client";

import { useEffect, useState } from "react";

import { SkillLevelPicker } from "@/components/skill-level-picker";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { en, format } from "@/i18n/en";
import { apiFetch } from "@/lib/api";
import type { CvReview, CvSkillMatch, CvSkillUnmatched, Skill } from "@/lib/types";

interface CvReviewFormProps {
  review: CvReview;
  busy: boolean;
  onConfirm: (skills: { skill_id: number; level: number }[]) => void;
}

/** Add a skill to the list, keeping the highest level if it is already there. */
export function addMatch(list: CvSkillMatch[], next: CvSkillMatch): CvSkillMatch[] {
  const existing = list.find((s) => s.skill_id === next.skill_id);
  if (!existing) return [...list, next];
  return list.map((s) =>
    s.skill_id === next.skill_id ? { ...s, level: Math.max(s.level, next.level) } : s,
  );
}

function UnmatchedRow({
  item,
  onMap,
  onDismiss,
}: {
  item: CvSkillUnmatched;
  onMap: (skill: Skill) => void;
  onDismiss: () => void;
}) {
  const [query, setQuery] = useState(item.name);
  const [options, setOptions] = useState<Skill[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      apiFetch<Skill[]>(`/skills?q=${encodeURIComponent(query)}`)
        .then((rows) => setOptions(rows.slice(0, 5)))
        .catch(() => setOptions([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <li className="flex flex-col gap-2 py-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">{item.name}</span>
        <Button variant="ghost" size="sm" onClick={onDismiss}>
          {en.cv.dismiss}
        </Button>
      </div>
      <Input
        aria-label={`${en.cv.searchPlaceholder}: ${item.name}`}
        value={query}
        placeholder={en.cv.searchPlaceholder}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="flex flex-wrap gap-2">
        {options.map((skill) => (
          <Button key={skill.id} variant="outline" size="sm" onClick={() => onMap(skill)}>
            {skill.name}
          </Button>
        ))}
      </div>
    </li>
  );
}

function Extras({ review }: { review: CvReview }) {
  const { parsed } = review;
  const groups: [string, string[]][] = [
    [en.cv.projects, parsed.projects.map((p) => p.title)],
    [
      en.cv.experience,
      parsed.experience.map((x) => [x.role, x.organization].filter(Boolean).join(" - ")),
    ],
    [en.cv.languages, parsed.languages],
    [en.cv.testScores, parsed.test_scores.map((t) => `${t.test}: ${t.score}`)],
    [en.cv.interests, parsed.interests],
  ];
  const shown = groups.filter(([, items]) => items.length > 0);
  if (shown.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{en.cv.extras}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 text-sm">
        {shown.map(([label, items]) => (
          <div key={label}>
            <p className="font-medium">{label}</p>
            <p className="text-muted-foreground">{items.join(", ")}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function CvReviewForm({ review, busy, onConfirm }: CvReviewFormProps) {
  const [matched, setMatched] = useState<CvSkillMatch[]>(review.matched);
  const [unmatched, setUnmatched] = useState<CvSkillUnmatched[]>(review.unmatched);

  const setLevel = (id: number, level: number) =>
    setMatched((list) => list.map((s) => (s.skill_id === id ? { ...s, level } : s)));
  const removeMatch = (id: number) => setMatched((list) => list.filter((s) => s.skill_id !== id));
  const mapUnmatched = (index: number, skill: Skill) => {
    const item = unmatched[index];
    setMatched((list) =>
      addMatch(list, {
        skill_id: skill.id,
        name: skill.name,
        level: item.level,
        evidence: item.evidence,
      }),
    );
    setUnmatched((list) => list.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold">{en.cv.reviewTitle}</h2>
        <p className="text-sm text-muted-foreground">{en.cv.reviewSubtitle}</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{en.cv.foundSkills}</CardTitle>
        </CardHeader>
        <CardContent>
          {matched.length === 0 && <p className="text-sm">{en.cv.noneMatched}</p>}
          <ul className="flex flex-col divide-y">
            {matched.map((skill) => (
              <li key={skill.skill_id} className="flex flex-col gap-2 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium">{skill.name}</span>
                  <span className="flex items-center gap-2">
                    <SkillLevelPicker
                      value={skill.level}
                      onChange={(level) => setLevel(skill.skill_id, level)}
                    />
                    <Button variant="ghost" size="sm" onClick={() => removeMatch(skill.skill_id)}>
                      {en.common.remove}
                    </Button>
                  </span>
                </div>
                {skill.evidence && (
                  <p className="text-xs text-muted-foreground">
                    {format(en.cv.evidence, { text: skill.evidence })}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
      {unmatched.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{en.cv.unmatchedTitle}</CardTitle>
            <p className="text-sm text-muted-foreground">{en.cv.unmatchedHelp}</p>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col divide-y">
              {unmatched.map((item, index) => (
                <UnmatchedRow
                  key={`${item.name}-${index}`}
                  item={item}
                  onMap={(skill) => mapUnmatched(index, skill)}
                  onDismiss={() => setUnmatched((list) => list.filter((_, i) => i !== index))}
                />
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      <Extras review={review} />
      <Button
        className="self-start"
        disabled={busy || matched.length === 0}
        onClick={() => onConfirm(matched.map((s) => ({ skill_id: s.skill_id, level: s.level })))}
      >
        {busy ? en.cv.confirming : en.cv.confirm}
      </Button>
    </div>
  );
}
