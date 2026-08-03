import { GmailComposeMock } from "@/components/marketing/gmail-compose-mock";
import { ScorePanel } from "@/components/marketing/score-panel";
import { IssueList } from "@/components/marketing/issue-list";
import { ExtensionPopupMock } from "@/components/marketing/extension-popup-mock";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <span className="flex items-center gap-2 text-sm font-semibold tracking-tight text-foreground">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-700 text-[13px] text-white">
              M
            </span>
            Manner Buddy
          </span>
          <span className="rounded-md bg-blue-50 px-2.5 py-1 font-mono text-[11px] text-blue-700">
            Chrome 확장 프로그램
          </span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 pb-24">
        {/* hero */}
        <section className="pb-14 pt-14">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-blue-700">
            Gmail 실시간 매너 코치
          </p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold leading-[1.35] tracking-tight text-foreground sm:text-[2.75rem]">
            보내기 전에, 상대의 문화로
            <br />
            한 번 더 읽어봅니다.
          </h1>
          <p className="mt-5 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
            미국·일본·중국 파트너에게 보내는 이메일이 그 나라 비즈니스
            문화에서 어떻게 읽힐지, Gmail 안에서 바로 확인하고 다듬습니다.
          </p>

          <div className="mt-12">
            <GmailComposeMock />
          </div>
        </section>

        {/* score panel */}
        <section className="border-t border-border py-14">
          <SectionHeading
            eyebrow="Score"
            title="매너 온도 리포트"
            description="보낸 문장을 국가별 4대 기준으로 채점합니다."
          />
          <div className="mt-8">
            <ScorePanel />
          </div>
        </section>

        {/* issues */}
        <section className="border-t border-border py-14">
          <SectionHeading
            eyebrow="Suggestions"
            title="발견된 표현"
            description="이번 메일에서 걸린 표현과, 왜 그 나라에서 문제가 되는지에 대한 이유입니다."
          />
          <div className="mt-8">
            <IssueList />
          </div>
        </section>

        {/* popup */}
        <section className="border-t border-border py-14">
          <SectionHeading
            eyebrow="Popup"
            title="확장 프로그램 팝업"
            description="브라우저 툴바 아이콘을 누르면 이번 주 검토 기록을 요약해서 보여줍니다."
          />
          <div className="mt-8">
            <ExtensionPopupMock />
          </div>
        </section>
      </main>

      <footer className="mt-auto border-t border-border">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-6 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>Manner Buddy — Gmail 확장 프로그램 UI 디자인 목업</span>
          <span className="font-mono tracking-wide">Next.js · shadcn/ui</span>
        </div>
      </footer>
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-blue-700">
        {eyebrow}
      </p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
        {title}
      </h2>
      <p className="mt-2 max-w-lg text-sm leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
