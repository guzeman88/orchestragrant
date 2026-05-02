"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider } from "next-themes";
import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { initAuth, getAccessToken, authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function Providers({ children }: { children: React.ReactNode }) {
  const setAuth = useAuthStore((s) => s.setAuth);
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: (failureCount, error: any) => {
              if (error?.status === 401 || error?.status === 403) return false;
              return failureCount < 2;
            },
          },
        },
      })
  );

  useEffect(() => {
    initAuth().then(async () => {
      // If silent refresh failed, auto-login with demo admin to restore session
      if (!getAccessToken()) {
        try {
          const data = await authApi.login({
            email: "admin@orchestragrant.dev",
            password: "SecureDemo123!",
          });
          setAuth(data.user, data.org, data.access_token, data.refresh_token);
        } catch {
          // Could not restore session — queries will remain empty
        }
      }
      queryClient.invalidateQueries();
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
        {children}
        <Toaster />
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
