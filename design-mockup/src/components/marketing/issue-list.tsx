import { CategoryTag } from "./category-tag";

interface Issue {
  country: "US" | "JP" | "CN";
  category: string;
  tone: "red" | "amber" | "blue";
  severity: "상" | "중";
  original: string;
  suggestion: string;
  reason: string;
}

const ISSUES: Issue[] = [
  {
    country: "JP",
    category: "TONE",
    tone: "red",
    severity: "상",
    original: "You need to sign this by Friday.",
    suggestion:
      "It would really help if this could be signed by Friday — happy to adjust if that's tight.",
    reason:
      "지시형 문장은 강압적으로 읽힐 수 있어요. 상대에게 여지를 남기는 표현이 더 안전합니다.",
  },
  {
    country: "US",
    category: "VOCAB",
    tone: "amber",
    severity: "중",
    original: "Please advise.",
    suggestion: "Let me know your thoughts whenever you get a chance.",
    reason:
      "지나치게 사무적인 상투어는 무성의하게 느껴질 수 있어요. 구체적인 요청으로 바꾸는 걸 권장해요.",
  },
  {
    country: "CN",
    category: "TABOO",
    tone: "red",
    severity: "상",
    original: "Let's cut to the chase — the deadline is non-negotiable.",
    suggestion:
      "This timeline is tight on our side too, but let's find a way through it together.",
    reason:
      "체면을 상하게 하는 단정적 표현은 관계 자체에 영향을 줄 수 있어요. 협의의 여지를 보여주는 게 중요해요.",
  },
];

export function IssueList() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {ISSUES.map((issue) => (
        <div
          key={issue.category + issue.country}
          className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5"
        >
          <div className="flex items-center justify-between">
            <CategoryTag country={issue.country} label={issue.category} tone={issue.tone} />
            <span className="font-mono text-[10px] tracking-widest text-muted-foreground">
              심각도 {issue.severity}
            </span>
          </div>

          <p className="text-sm text-muted-foreground line-through decoration-red-600/40">
            {issue.original}
          </p>
          <p className="text-sm font-medium leading-relaxed text-foreground">
            {issue.suggestion}
          </p>
          <p className="mt-auto border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
            {issue.reason}
          </p>
        </div>
      ))}
    </div>
  );
}
