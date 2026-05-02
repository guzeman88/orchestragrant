"use client";

import { useState, useCallback } from "react";
import type { ToastProps } from "@/components/ui/toast";

type ToastItem = ToastProps & {
  id: string;
  title?: string;
  description?: string;
  action?: React.ReactElement;
};

let toastListeners: ((toasts: ToastItem[]) => void)[] = [];
let toastList: ToastItem[] = [];

function emitChange() {
  toastListeners.forEach((l) => l([...toastList]));
}

export function toast(props: Omit<ToastItem, "id">) {
  const id = Math.random().toString(36).slice(2);
  const item: ToastItem = { ...props, id, open: true };
  toastList = [...toastList, item];
  emitChange();
  setTimeout(() => {
    toastList = toastList.filter((t) => t.id !== id);
    emitChange();
  }, 5000);
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>(toastList);
  const subscribe = useCallback((listener: (t: ToastItem[]) => void) => {
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  }, []);

  useState(() => {
    const unsub = subscribe(setToasts);
    return unsub;
  });

  return { toasts };
}
