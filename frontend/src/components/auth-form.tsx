"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { en } from "@/i18n/en";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const supabase = createClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const isSignup = mode === "signup";

  if (!supabase) {
    return <p className="p-8 text-center text-sm">{en.auth.notConfigured}</p>;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!supabase) return;
    setError(null);
    if (!email.trim() || !password) return setError(en.auth.errors.missingFields);
    if (isSignup && password.length < 8) return setError(en.auth.errors.shortPassword);

    setBusy(true);
    const credentials = { email: email.trim(), password };
    const { data, error: authError } = isSignup
      ? await supabase.auth.signUp({
          ...credentials,
          options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
        })
      : await supabase.auth.signInWithPassword(credentials);
    setBusy(false);

    if (authError) return setError(authError.message);
    if (isSignup && !data.session) return setNotice(en.auth.checkEmail);
    router.replace("/dashboard");
    router.refresh();
  }

  async function googleSignIn() {
    if (!supabase) return;
    setError(null);
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (oauthError) setError(oauthError.message);
  }

  return (
    <Card className="mx-auto mt-16 w-full max-w-sm">
      <CardHeader>
        <CardTitle>{isSignup ? en.auth.signupTitle : en.auth.loginTitle}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
          <div className="flex flex-col gap-2">
            <Label htmlFor="email">{en.auth.email}</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="password">{en.auth.password}</Label>
            <Input
              id="password"
              type="password"
              autoComplete={isSignup ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {isSignup && <p className="text-xs text-muted-foreground">{en.auth.passwordHint}</p>}
          </div>
          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}
          {notice && <p className="text-sm text-green-700">{notice}</p>}
          <Button type="submit" disabled={busy}>
            {isSignup ? en.auth.signup : en.auth.login}
          </Button>
        </form>
        <p className="text-center text-xs text-muted-foreground">{en.auth.or}</p>
        <Button variant="outline" type="button" onClick={googleSignIn}>
          {en.auth.google}
        </Button>
        <p className="text-center text-sm">
          {isSignup ? en.auth.haveAccount : en.auth.noAccount}{" "}
          <Link className="underline" href={isSignup ? "/login" : "/signup"}>
            {isSignup ? en.auth.login : en.auth.signup}
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
