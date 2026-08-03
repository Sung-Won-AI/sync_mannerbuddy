import { cn } from "@/lib/utils";

const TONE_CLASS = {
  red: "bg-red-50 text-red-600",
  amber: "bg-amber-50 text-amber-600",
  blue: "bg-blue-100 text-blue-700",
  green: "bg-green-50 text-green-600",
} as const;

const DOT_CLASS = {
  red: "bg-red-600",
  amber: "bg-amber-600",
  blue: "bg-blue-700",
  green: "bg-green-600",
} as const;

interface CategoryTagProps {
  country: "US" | "JP" | "CN";
  label: string;
  tone?: keyof typeof TONE_CLASS;
  className?: string;
}

export function CategoryTag({ country, label, tone = "blue", className }: CategoryTagProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-1 font-mono text-[11px] font-medium tracking-wide",
        TONE_CLASS[tone],
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT_CLASS[tone])} />
      {country} · {label}
    </span>
  );
}
