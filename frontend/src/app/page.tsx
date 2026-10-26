import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { fetchHealth } from "@/lib/api";
import { en } from "@/i18n/en";

export const dynamic = "force-dynamic";

async function getBackendStatus(): Promise<string> {
  try {
    const health = await fetchHealth();
    return health.status === "ok" ? en.home.backendOk : en.home.backendDown;
  } catch {
    return en.home.backendDown;
  }
}

export default async function Home() {
  const status = await getBackendStatus();
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-4 p-8">
      <h1 className="text-4xl font-bold">{en.home.title}</h1>
      <p className="text-muted-foreground">{en.home.tagline}</p>
      <div className="flex gap-2">
        <Link href="/login" className={buttonVariants()}>
          {en.home.signIn}
        </Link>
        <Link href="/signup" className={buttonVariants({ variant: "outline" })}>
          {en.home.signUp}
        </Link>
      </div>
      <p data-testid="backend-status" className="font-mono text-sm">
        {en.home.backendLabel}: {status}
      </p>
    </main>
  );
}
