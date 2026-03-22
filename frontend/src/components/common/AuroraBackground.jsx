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
            25% { transform: translate(5%, -8%) scale(1.15); }
            50% { transform: translate(-3%, 5%) scale(0.95); }
            75% { transform: translate(8%, 3%) scale(1.1); }
          }
          @keyframes auroraShift2 {
            0%, 100% { transform: translate(0%, 0%) scale(1.05); }
            25% { transform: translate(-8%, 6%) scale(0.9); }
            50% { transform: translate(6%, -8%) scale(1.15); }
            75% { transform: translate(-5%, -3%) scale(1); }
          }
          @keyframes auroraShift3 {
            0%, 100% { transform: translate(0%, 0%) scale(0.95); }
            33% { transform: translate(10%, 7%) scale(1.1); }
            66% { transform: translate(-6%, -9%) scale(1); }
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
          background: `linear-gradient(180deg, ${aurora[0]}60 0%, #0c1222 40%, #0f172a 60%, ${aurora[2]}50 100%)`,
        }}
      >
        {/* Aurora blob 1 — top left, large & bright */}
        <div
          style={{
            position: "absolute",
            top: "-15%",
            left: "-5%",
            width: "75%",
            height: "65%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[0]}80 0%, ${aurora[0]}35 40%, transparent 70%)`,
            filter: "blur(40px)",
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
            top: "15%",
            right: "-10%",
            width: "65%",
            height: "60%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[1]}70 0%, ${aurora[1]}2A 40%, transparent 70%)`,
            filter: "blur(45px)",
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
            bottom: "-10%",
            left: "15%",
            width: "70%",
            height: "55%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[2]}65 0%, ${aurora[2]}25 40%, transparent 70%)`,
            filter: "blur(40px)",
            animation: prefersReducedMotion
              ? "none"
              : "auroraShift3 18s ease-in-out infinite",
            willChange: "transform",
          }}
        />
        {/* Aurora blob 4 — accent top right */}
        <div
          style={{
            position: "absolute",
            top: "5%",
            right: "5%",
            width: "45%",
            height: "40%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${aurora[3] || aurora[0]}50 0%, transparent 65%)`,
            filter: "blur(50px)",
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
