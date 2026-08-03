import { Button } from "@/components/ui/button";

export function ExtensionPopupMock() {
  return (
    <div className="mx-auto w-full max-w-[300px] overflow-hidden rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(16,27,45,0.04),0_16px_40px_-24px_rgba(16,27,45,0.3)]">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-sm font-semibold text-foreground">
          이번 주 검토 기록
        </span>
        <span className="rounded-md bg-green-50 px-2 py-0.5 font-mono text-[10px] font-medium text-green-600">
          ON
        </span>
      </div>

      <div className="space-y-4 px-4 py-4">
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-muted-foreground">검토한 문장</span>
          <span className="font-mono text-lg text-foreground">12건</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-muted-foreground">매너 온도 변화</span>
          <span className="font-mono text-lg text-green-600">+6°</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-muted-foreground">자주 걸리는 유형</span>
          <span className="font-mono text-xs tracking-wide text-blue-700">TONE · JP</span>
        </div>
      </div>

      <div className="border-t border-border px-4 py-3">
        <Button className="w-full bg-blue-700 text-white hover:bg-blue-600" size="sm">
          대시보드에서 자세히 보기
        </Button>
      </div>
    </div>
  );
}
