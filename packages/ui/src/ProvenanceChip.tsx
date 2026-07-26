import type { HTMLAttributes } from "react";

export type ProvenanceKind =
  | "Function"
  | "Method"
  | "Class"
  | "Type"
  | "Const"
  | "Symbol"
  | "Commit"
  | "Note"
  | "File";

type ProvenanceChipProps = HTMLAttributes<HTMLSpanElement> & {
  kind: ProvenanceKind | string;
};

export function ProvenanceChip({
  kind,
  className = "",
  ...rest
}: ProvenanceChipProps) {
  return (
    <span
      className={`font-label-caps text-label-caps bg-surface-container-high border border-border text-muted px-2 py-0.5 rounded-full ${className}`.trim()}
      {...rest}
    >
      {kind}
    </span>
  );
}
