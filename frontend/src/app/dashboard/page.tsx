"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DeleteDataButton } from "@/components/delete-data-button";
import { SignOutButton } from "@/components/sign-out-button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { en, format } from "@/i18n/en";
import { ApiError, apiFetch } from "@/lib/api";
import type { Field, Profile, ProfileSkill } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [fieldName, setFieldName] = useState("");
  const [skills, setSkills] = useState<ProfileSkill[]>([]);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<Profile>("/me/profile");
        const [fields, mine] = await Promise.all([
          apiFetch<Field[]>("/fields"),
          apiFetch<ProfileSkill[]>("/me/skills"),
        ]);
        setProfile(me);
        setSkills(mine);
        setFieldName(fields.find((f) => f.id === me.field_id)?.name ?? "");
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) router.replace("/onboarding");
        else setFailed(true);
      }
    }
    void load();
  }, [router]);

  if (failed) return <p className="p-8 text-red-600">{en.common.genericError}</p>;
  if (!profile) return <p className="p-8">{en.common.loading}</p>;

  const rows: [string, string][] = [
    [en.dashboard.university, profile.university],
    [en.dashboard.department, profile.department],
    [en.dashboard.year, String(profile.year)],
    [en.dashboard.cgpa, profile.cgpa],
    [en.dashboard.track, en.onboarding.tracks[profile.track]],
    [en.onboarding.field, fieldName],
  ];

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-4 pt-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          {format(en.dashboard.welcome, { name: profile.name })}
        </h1>
        <SignOutButton />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{en.dashboard.profile}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {rows.map(([label, value]) => (
              <div key={label} className="contents">
                <dt className="text-muted-foreground">{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <p className="text-sm">{format(en.dashboard.skillsCount, { count: skills.length })}</p>
          <div className="flex gap-2">
            <Link href="/onboarding" className={buttonVariants({ variant: "outline" })}>
              {en.dashboard.editProfile}
            </Link>
            <Link href="/cv" className={buttonVariants()}>
              {en.dashboard.uploadCv}
            </Link>
            <Link href="/skills" className={buttonVariants({ variant: "outline" })}>
              {en.dashboard.manageSkills}
            </Link>
          </div>
          <DeleteDataButton />
        </CardContent>
      </Card>
      <p className="text-sm text-muted-foreground">{en.dashboard.comingSoon}</p>
    </main>
  );
}
