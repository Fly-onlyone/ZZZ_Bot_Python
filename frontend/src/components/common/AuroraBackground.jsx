import React, { memo } from "react";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * AuroraBackground — animated flowing gradient backdrop
 *
 * Renders a full-screen fixed layer with multiple animated radial gradients
 * that slowly shift position, creating a Northern Lights atmosphere.
 * Each theme produces a unique aurora palette.
 */
const AuroraBackground = memo(function AuroraBackground() {
  const { themeColors, prefersReducedMotion } = useThemeContext();
  const aurora = themeColors.aurora;

  return (
    <>
      <style>
        {`
          @keyframes auroraShift1 {
            0%, 100% { transform: translate(0%, 0%) scale(1); }
            25% { transform: translate(5%, -8%) scale(1.1); }
            50% { transform: translate(-3%, 5%) scale(0.95); }
            75% { transform: translate(8%, 3%) scale(1.05); }
          }
          @keyframes auroraShift2 {
            0%, 100% { transform: translate(0%, 0%) scale(1.05); }
            25% { transform: translate(-6%, 4%) scale(0.95); }
            50% { transform: translate(4%, -6%) scale(1.1); }
            75% { transform: translate(-5%, -3%) scale(1); }
          }
          @keyframes auroraShift3 {
            0%, 100% { transform: translate(0%, 0%) scale(0.95); }
            33% { transform: translate(7%, 5%) scale(1.05); }
            66% { transform: translate(-4%, -7%) scale(1); }
          }
        `}
      </style>
      <div
        aria-hidden="true"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
          pointerEvents: "none",
          overflow: "hidden",
          background: `linear-gradient(180deg, ${aurora[0]}15 0%, #0f172a 50%, ${aurora[2]}10 100%)`,
        }}
      >
        {/* Aurora blob 1 — top left */}
        <div
          style={{
            position: "absolute",
            top: "-20%",
            left: "-10%",
            width: "70%",
            height: "60%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[0]}18 0%, transparent 70%)`,
            filter: "blur(60px)",
            animation: prefersReducedMotion
              ? "none"
              : "auroraShift1 12s ease-in-out infinite",
            willChange: "transform",
          }}
        />
        {/* Aurora blob 2 — center right */}
        <div
          style={{
            position: "absolute",
            top: "20%",
            right: "-15%",
            width: "60%",
            height: "55%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[1]}15 0%, transparent 70%)`,
            filter: "blur(80px)",
            animation: prefersReducedMotion
              ? "none"
              : "auroraShift2 15s ease-in-out infinite",
            willChange: "transform",
          }}
        />
        {/* Aurora blob 3 — bottom center */}
        <div
          style={{
            position: "absolute",
            bottom: "-15%",
            left: "20%",
            width: "65%",
            height: "50%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[2]}12 0%, transparent 70%)`,
            filter: "blur(70px)",
            animation: prefersReducedMotion
              ? "none"
              : "auroraShift3 18s ease-in-out infinite",
            willChange: "transform",
          }}
        />
        {/* Aurora blob 4 — accent top right (subtle) */}
        <div
          style={{
            position: "absolute",
            top: "10%",
            right: "10%",
            width: "40%",
            height: "35%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[3] || aurora[0]}0D 0%, transparent 70%)`,
            filter: "blur(90px)",
            animation: prefersReducedMotion
              ? "none"
              : "auroraShift1 20s ease-in-out infinite reverse",
            willChange: "transform",
          }}
        />
      </div>
    </>
  );
});

export default AuroraBackground;
