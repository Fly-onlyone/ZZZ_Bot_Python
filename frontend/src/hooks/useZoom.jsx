import { createContext, useCallback, useContext, useEffect, useState } from "react";

const ZOOM_KEY = "zzz-bot-zoom";
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 2.0;
const ZOOM_STEP = 0.1;

const clamp = (value) => Math.round(Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value)) * 10) / 10;

const ZoomContext = createContext({
  zoomLevel: 1.0,
  zoomIn: () => {},
  zoomOut: () => {},
  resetZoom: () => {},
});

export function ZoomProvider({ children, containerRef }) {
  const [zoomLevel, setZoomLevel] = useState(() => {
    const stored = localStorage.getItem(ZOOM_KEY);
    return stored ? clamp(parseFloat(stored)) : 1.0;
  });

  useEffect(() => {
    localStorage.setItem(ZOOM_KEY, String(zoomLevel));
  }, [zoomLevel]);

  const zoomIn = useCallback(() => setZoomLevel((z) => clamp(z + ZOOM_STEP)), []);
  const zoomOut = useCallback(() => setZoomLevel((z) => clamp(z - ZOOM_STEP)), []);
  const resetZoom = useCallback(() => setZoomLevel(1.0), []);

  // Ctrl + scroll wheel to zoom
  useEffect(() => {
    const el = containerRef?.current;
    if (!el) return;

    const handleWheel = (e) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      if (e.deltaY < 0) {
        setZoomLevel((z) => clamp(z + ZOOM_STEP));
      } else {
        setZoomLevel((z) => clamp(z - ZOOM_STEP));
      }
    };

    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [containerRef]);

  return (
    <ZoomContext.Provider value={{ zoomLevel, zoomIn, zoomOut, resetZoom }}>
      {children}
    </ZoomContext.Provider>
  );
}

export function useZoom() {
  return useContext(ZoomContext);
}
