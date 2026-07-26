import type { HTMLAttributes } from "react";

type StatusPillProps = HTMLAttributes<HTMLDivElement> & {
  label?: string;
  connected?: boolean;
};

export function StatusPill({
  label = "Core · Connected",
  connected = true,
  className = "",
  ...rest
}: StatusPillProps) {
  return (
    <div
      className={`flex items-center gap-xs px-sm py-[2px] rounded-full border border-border bg-surface-container-low ${className}`.trim()}
      {...rest}
    >
      <div
        className={`w-2 h-2 rounded-full ${connected ? "bg-primary" : "bg-muted"}`}
      />
      <span className="font-technical-mono-sm text-technical-mono-sm text-on-surface">
        {label}
      </span>
    </div>
  );
}
