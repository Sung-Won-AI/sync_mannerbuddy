"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { CategoryTag } from "./category-tag";

const MODES = [
  { id: "realtime", label: "실시간 교정" },
  { id: "before-send", label: "발송 전 검토" },
] as const;

export function GmailComposeMock() {
  const [mode, setMode] = useState<(typeof MODES)[number]["id"]>("realtime");

  return (
    <div className="grid gap-5 lg:grid-cols-[1.15fr_1fr] lg:items-start">
      {/* compose window */}
      <div className="overflow-hidden rounded-xl border border-border bg-white shadow-[0_1px_2px_rgba(16,27,45,0.04),0_16px_40px_-24px_rgba(16,27,45,0.25)]">
        <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
          <span className="h-2 w-2 rounded-full bg-red-600/60" />
          <span className="h-2 w-2 rounded-full bg-amber-600/60" />
          <span className="h-2 w-2 rounded-full bg-green-600/60" />
          <span className="ml-2 font-mono text-[11px] tracking-wide text-ink-400">
            mail.google.com/mail — 새 메일
          </span>
        </div>

        <div className="space-y-2.5 border-b border-border px-5 py-3 text-sm">
          <div className="flex items-center gap-3">
            <span className="w-14 shrink-0 text-ink-400">받는사람</span>
            <span className="font-medium text-ink-900">tanaka@partner-kk.co.jp</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-14 shrink-0 text-ink-400">제목</span>
            <span className="font-medium text-ink-900">Re: Partnership Timeline</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 px-5 pt-4">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              className={cn(
                "rounded-full border px-3 py-1 text-[12px] font-medium tracking-wide transition-colors",
                mode === m.id
                  ? "border-blue-700 bg-blue-50 text-blue-700"
                  : "border-border text-ink-400 hover:bg-muted"
              )}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="px-5 py-5 text-[15px] leading-[1.85] text-ink-900">
          <p>Hi Tanaka-san,</p>
          <p className="mt-3">
            Thanks for the update on the shipment schedule.{" "}
            <span className="cursor-pointer rounded-[2px] bg-red-50 px-0.5 underline decoration-red-600/40 decoration-2 underline-offset-2 hover:bg-red-600/10">
              You need to sign this by Friday.
            </span>{" "}
            Let&apos;s finalize the contract soon.
          </p>
          <p className="mt-3 text-ink-400">Best,</p>
        </div>
      </div>

      {/* correction popover */}
      <div className="relative mt-2 lg:mt-10">
        <div className="absolute -top-[7px] left-6 hidden h-3.5 w-3.5 rotate-45 rounded-[2px] bg-white shadow-[-2px_-2px_4px_rgba(16,27,45,0.05)] lg:block" />
        <div className="rounded-xl border border-border bg-white shadow-[0_1px_2px_rgba(16,27,45,0.04),0_16px_40px_-24px_rgba(16,27,45,0.3)]">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <span aria-hidden className="text-base">
              💡
            </span>
            <span className="flex-1 text-sm font-semibold text-blue-700">
              더 예의바르게 표현해볼까요?
            </span>
            <button
              type="button"
              aria-label="닫기"
              className="rounded-full p-1 text-ink-400 hover:bg-muted"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3 px-4 py-4">
            <CategoryTag country="JP" label="TONE" tone="red" />

            <div className="rounded-lg border-l-[3px] border-blue-700 bg-blue-50 px-3 py-2.5 text-[13px] font-medium leading-relaxed text-blue-700">
              &quot;It would really help if this could be signed by Friday —
              happy to adjust if that&apos;s tight.&quot;
            </div>

            <p className="text-[12.5px] leading-relaxed text-ink-600">
              지시형 문장은 상대를 압박하는 것으로 읽힐 수 있어요. 선택지를
              남기는 완곡한 표현이 일본 비즈니스 관례에서 더 안전합니다.
            </p>

            <div className="flex flex-col gap-2 pt-1">
              <button
                type="button"
                className="rounded-lg bg-blue-700 px-3 py-2 text-[12.5px] font-medium text-white hover:bg-blue-600"
              >
                ✎ 원문 수정하기
              </button>
              <button
                type="button"
                className="rounded-lg border border-border px-3 py-2 text-[12.5px] font-medium text-ink-600 hover:bg-muted"
              >
                ✓ 괜찮아요
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
