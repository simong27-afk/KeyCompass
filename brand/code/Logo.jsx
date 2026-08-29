// KeyCompass logo — mark + wordmark. Ratio is the whole point:
// mark height = cap height of the wordmark; gap = ~0.25 x mark.
export function KeyCompassMark({ size = 32, className = "" }) {
  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      fill="currentColor"
      fillRule="evenodd"
      role="img"
      aria-label="KeyCompass"
      className={className}
    >
      <path d="M4 4h92v92H4z M14 14v72h72V14z" />
      <path d="M32 32h36v36H32z M42 42v16h16V42z" />
      <rect x="44" y="12" width="12" height="22" />
      <rect x="44" y="66" width="12" height="22" />
      <rect x="66" y="44" width="22" height="12" />
      <rect x="12" y="44" width="22" height="12" />
    </svg>
  );
}

// fontSize drives everything: mark = 0.78em (cap height), gap = 0.22em.
export function KeyCompassLockup({ fontSize = 21, color = "#201e1d" }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.22em",
        fontSize,
        color,
        fontFamily: "Archivo, system-ui, sans-serif",
        fontWeight: 800,
        letterSpacing: "-0.035em",
        lineHeight: 1,
      }}
    >
      <KeyCompassMark size="0.78em" />
      KeyCompass
    </span>
  );
}
