import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <main className="p-4">
      <AuthForm mode="login" />
    </main>
  );
}
