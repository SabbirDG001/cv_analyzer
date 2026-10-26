"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { SkillLevelPicker } from "@/components/skill-level-picker";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { en } from "@/i18n/en";
import { ApiError, apiFetch } from "@/lib/api";
import type { ProfileSkill, Skill } from "@/lib/types";

export default function SkillsPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Skill[]>([]);
  const [mine, setMine] = useState<ProfileSkill[]>([]);
  const [error, setError] = useState<string | null>(null);

  const levelOf = (skillId: number): number | null =>
    mine.find((s) => s.skill_id === skillId)?.level ?? null;

  const loadMine = useCallback(async () => {
    setMine(await apiFetch<ProfileSkill[]>("/me/skills"));
  }, []);

  useEffect(() => {
    loadMine().catch(() => setError(en.common.genericError));
  }, [loadMine]);

  useEffect(() => {
    const timer = setTimeout(() => {
      apiFetch<Skill[]>(`/skills?q=${encodeURIComponent(query)}`)
        .then(setResults)
        .catch(() => setError(en.common.genericError));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      await loadMine();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : en.common.genericError);
    }
  }

  const setLevel = (skillId: number, level: number) =>
    run(() =>
      apiFetch<void>(`/me/skills/${skillId}`, { method: "PUT", body: JSON.stringify({ level }) }),
    );
  const removeSkill = (skillId: number) =>
    run(() => apiFetch<void>(`/me/skills/${skillId}`, { method: "DELETE" }));

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-4 pt-8">
      <div>
        <h1 className="text-2xl font-bold">{en.skills.title}</h1>
        <p className="text-sm text-muted-foreground">{en.skills.subtitle}</p>
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
      <Card>
        <CardContent className="flex flex-col gap-4 pt-6">
          <Label htmlFor="skill-search">{en.skills.searchLabel}</Label>
          <Input
            id="skill-search"
            value={query}
            placeholder={en.skills.searchPlaceholder}
            onChange={(e) => setQuery(e.target.value)}
          />
          {results.length === 0 && <p className="text-sm">{en.skills.noResults}</p>}
          <ul className="flex flex-col divide-y">
            {results.map((skill) => (
              <li key={skill.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span>{skill.name}</span>
                <SkillLevelPicker
                  value={levelOf(skill.id)}
                  onChange={(level) => void setLevel(skill.id, level)}
                />
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{en.skills.yourSkills}</CardTitle>
        </CardHeader>
        <CardContent>
          {mine.length === 0 && <p className="text-sm">{en.skills.empty}</p>}
          <ul className="flex flex-col divide-y">
            {mine.map((skill) => (
              <li
                key={skill.skill_id}
                className="flex flex-wrap items-center justify-between gap-2 py-2"
              >
                <span>
                  {skill.name}{" "}
                  <span className="text-xs text-muted-foreground">
                    {en.skills.levels[skill.level]}
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  <SkillLevelPicker
                    value={skill.level}
                    onChange={(level) => void setLevel(skill.skill_id, level)}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => void removeSkill(skill.skill_id)}
                  >
                    {en.common.remove}
                  </Button>
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
      <Link
        href="/dashboard"
        className={buttonVariants({ variant: "outline", className: "self-start" })}
      >
        {en.skills.next}
      </Link>
    </main>
  );
}
