import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { supabaseConfig } from "@/lib/supabase/config";

const PROTECTED_PREFIXES = ["/onboarding", "/skills", "/dashboard"];
const AUTH_PAGES = ["/login", "/signup"];

function startsWithAny(pathname: string, prefixes: string[]): boolean {
  return prefixes.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

function redirectTo(request: NextRequest, pathname: string): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  return NextResponse.redirect(url);
}

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;
  const config = supabaseConfig();
  const isProtected = startsWithAny(pathname, PROTECTED_PREFIXES);

  if (!config) {
    return isProtected ? redirectTo(request, "/login") : NextResponse.next();
  }

  let response = NextResponse.next({ request });
  const supabase = createServerClient(config.url, config.anonKey, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (items) => {
        for (const { name, value } of items) request.cookies.set(name, value);
        response = NextResponse.next({ request });
        for (const { name, value, options } of items) response.cookies.set(name, value, options);
      },
    },
  });

  // getUser() revalidates the token with Supabase, unlike reading the cookie alone.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user && isProtected) return redirectTo(request, "/login");
  if (user && startsWithAny(pathname, AUTH_PAGES)) return redirectTo(request, "/dashboard");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
