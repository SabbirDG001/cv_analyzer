"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { en } from "@/i18n/en";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

export function DeleteDataButton() {
  const router = useRouter();
  const [error, setError] = useState(false);

  async function deleteData() {
    if (!window.confirm(en.dashboard.deleteConfirm)) return;
    setError(false);
    try {
      await apiFetch<void>("/me/data", { method: "DELETE" });
      await createClient()?.auth.signOut();
      router.replace("/");
      router.refresh();
    } catch {
      setError(true);
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <Button variant="outline" onClick={() => void deleteData()}>
        {en.dashboard.deleteData}
      </Button>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {en.common.genericError}
        </p>
      )}
    </div>
  );
}
