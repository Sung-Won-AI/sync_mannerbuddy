const AXES = [
  { label: "어휘", key: "VOCAB", value: 88 },
  { label: "어조", key: "TONE", value: 71 },
  { label: "금기", key: "TABOO", value: 90 },
  { label: "매너", key: "MANNERS", value: 79 },
] as const;

export function ScorePanel() {
  return (
    <div className="grid gap-8 rounded-xl border border-border bg-card p-6 sm:p-8 md:grid-cols-[auto_1fr] md:items-center md:gap-12">
      <div className="flex flex-col items-center gap-2 justify-self-center">
        <div className="flex h-28 w-28 flex-col items-center justify-center rounded-full border-[6px] border-blue-100 bg-blue-50">
          <span className="text-3xl font-semibold leading-none text-blue-700">
            82°
          </span>
          <span className="mt-1.5 font-mono text-[9px] uppercase tracking-[0.16em] text-ink-400">
            manner temp
          </span>
        </div>
        <p className="max-w-[11rem] text-center text-xs leading-relaxed text-muted-foreground">
          무난하게 통과 · 어조 표현 1건 재검토 권장
        </p>
      </div>

      <div className="space-y-5">
        {AXES.map((axis) => (
          <div key={axis.key}>
            <div className="mb-1.5 flex items-baseline justify-between">
              <span className="text-sm text-foreground">
                {axis.label}
                <span className="ml-1.5 font-mono text-[10px] tracking-wider text-muted-foreground">
                  {axis.key}
                </span>
              </span>
              <span className="font-mono text-sm text-ink-600">{axis.value}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-blue-700"
                style={{ width: `${axis.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
