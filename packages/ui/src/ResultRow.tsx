import type { HTMLAttributes, ReactNode } from "react";
import { ProvenanceChip, type ProvenanceKind } from "./ProvenanceChip";

export type ResultRowProps = HTMLAttributes<HTMLButtonElement> & {
  title: string;
  snippet: string;
  kind: ProvenanceKind | string;
  selected?: boolean;
  meta?: { icon: string; text: string }[];
  icon?: string;
};

export function ResultRow({
  title,
  snippet,
  kind,
  selected = false,
  meta = [],
  icon = "description",
  className = "",
  ...rest
}: ResultRowProps) {
  return (
    <button
      type="button"
      className={
        selected
          ? `group relative flex w-full min-w-0 flex-col gap-1 overflow-hidden p-4 rounded-lg bg-accent-dim/60 border border-primary cursor-pointer transition-colors duration-150 text-left ${className}`.trim()
          : `group relative flex w-full min-w-0 flex-col gap-1 overflow-hidden p-4 rounded-lg bg-surface-container-low border border-transparent hover:border-border hover:bg-surface-container cursor-pointer transition-colors duration-150 text-left ${className}`.trim()
      }
      {...rest}
    >
      {selected && (
        <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary rounded-l" />
      )}
      <div className="flex justify-between items-start mb-1 gap-2 min-w-0">
        <h3
          className={`font-body-md text-body-md text-on-surface group-hover:text-primary transition-colors flex items-center gap-2 min-w-0 flex-1 ${
            selected ? "font-semibold" : "font-medium"
          }`}
        >
          <span
            className={`material-symbols-outlined text-[16px] shrink-0 ${
              selected ? "text-primary" : "text-muted"
            }`}
          >
            {icon}
          </span>
          <span className="truncate min-w-0">{title}</span>
        </h3>
        <ProvenanceChip kind={kind} className="shrink-0 max-w-[40%] truncate" />
      </div>
      <p
        className={`font-body-sm text-body-sm line-clamp-2 break-words ${
          selected ? "text-on-surface-variant" : "text-muted"
        }`}
      >
        {snippet}
      </p>
      {meta.length > 0 && (
        <div className="flex items-center gap-3 mt-2 min-w-0 overflow-hidden">
          {meta.map((m: { icon: string; text: string }) => (
            <span
              key={`${m.icon}-${m.text}`}
              title={m.text}
              className="font-technical-mono-sm text-technical-mono-sm text-muted flex items-center gap-1 min-w-0 max-w-full"
            >
              <span className="material-symbols-outlined text-[12px] shrink-0">
                {m.icon}
              </span>
              <span className="truncate">{m.text}</span>
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

export type NoteLinkChipProps = {
  target: string;
  resolved?: boolean;
  children?: ReactNode;
  className?: string;
  onClick?: () => void;
};

export function NoteLinkChip({
  target,
  resolved = true,
  children,
  className = "",
  onClick,
}: NoteLinkChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={target}
      className={
        resolved
          ? `note-link inline font-technical-mono-sm text-technical-mono-sm text-primary underline-offset-2 hover:underline ${className}`.trim()
          : `inline font-technical-mono-sm text-technical-mono-sm text-muted/70 border-b border-dashed border-muted ${className}`.trim()
      }
    >
      {children ?? `[[${target}]]`}
    </button>
  );
}
