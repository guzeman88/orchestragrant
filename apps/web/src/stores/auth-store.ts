import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Organization } from "@orchestragrant/types";
import { setAccessToken } from "@/lib/api";

interface AuthState {
  user: User | null;
  org: Organization | null;
  isAuthenticated: boolean;
  setAuth: (user: User, org: Organization, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      org: null,
      isAuthenticated: false,
      setAuth: (user, org, accessToken, refreshToken) => {
        setAccessToken(accessToken);
        if (typeof localStorage !== "undefined") {
          localStorage.setItem("og_refresh_token", refreshToken);
        }
        set({ user, org, isAuthenticated: true });
      },
      clearAuth: () => {
        setAccessToken(null);
        if (typeof localStorage !== "undefined") {
          localStorage.removeItem("og_refresh_token");
        }
        set({ user: null, org: null, isAuthenticated: false });
      },
    }),
    {
      name: "og-auth",
      partialize: (state) => ({ user: state.user, org: state.org }),
      onRehydrateStorage: () => (state) => {
        // Re-hydrate access token from refresh on page load
        if (state?.user) {
          state.isAuthenticated = true;
        }
      },
    }
  )
);
