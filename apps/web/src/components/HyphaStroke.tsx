type HyphaStrokeProps = {
  className?: string;
};

/**
 * Decorative branching-stem background, echoing the logo mark.
 * Paths start fully drawn (dashoffset 0) for reduced-motion / no-JS;
 * useScrollTheater animates strokeDashoffset length→0 when data-motion="full".
 */
export function HyphaStroke({ className }: HyphaStrokeProps) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 1200 800"
      preserveAspectRatio="xMidYMid slice"
      className={className}
    >
      <g
        fill="none"
        stroke="var(--color-teal)"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.3"
      >
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M120,760 L120,560 L40,420" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M120,560 L220,440" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M120,560 L150,380" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M1080,60 L1080,240 L1160,360" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M1080,240 L980,340" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M1080,240 L1050,400" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M600,-20 L600,140 L520,240" />
        <path data-hypha-path strokeDasharray="700" strokeDashoffset="0" d="M600,140 L700,220" />
      </g>
      <g
        fill="none"
        stroke="var(--color-fg)"
        strokeWidth="1"
        strokeLinecap="round"
        opacity="0.12"
      >
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M300,820 L300,600 L220,470" />
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M300,600 L400,500" />
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M900,820 L900,620 L820,480" />
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M900,620 L1000,520" />
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M950,-20 L950,120 L1040,200" />
        <path data-hypha-path strokeDasharray="900" strokeDashoffset="0" d="M950,120 L860,190" />
      </g>
      <g fill="var(--color-teal)" opacity="0.5">
        <circle cx="40" cy="420" r="4" />
        <circle cx="1160" cy="360" r="4" />
        <circle cx="520" cy="240" r="4" />
      </g>
    </svg>
  );
}
