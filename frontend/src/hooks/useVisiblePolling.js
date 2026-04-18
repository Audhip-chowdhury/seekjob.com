import { useEffect, useRef } from "react";

/**
 * Runs `fn` on an interval while the document tab is visible.
 * Also runs when the tab becomes visible again (catches changes while away).
 */
export function useVisiblePolling(fn, intervalMs = 5000) {
  const ref = useRef(fn);
  ref.current = fn;

  useEffect(() => {
    const tick = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      ref.current();
    };
    const id = setInterval(tick, intervalMs);
    document.addEventListener("visibilitychange", tick);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [intervalMs]);
}
