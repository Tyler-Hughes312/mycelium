import type { HTMLAttributes } from "react";

type IconProps = HTMLAttributes<HTMLSpanElement> & {
  name: string;
  filled?: boolean;
  size?: number;
};

export function Icon({
  name,
  filled = false,
  size,
  className = "",
  style,
  ...rest
}: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${className}`.trim()}
      style={{
        fontVariationSettings: filled
          ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
          : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24",
        fontSize: size,
        ...style,
      }}
      {...rest}
    >
      {name}
    </span>
  );
}
