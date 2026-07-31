import { useState } from "react";
import type { AnalysisIssue } from "../shared/meetingTypes";
import { splitLineWithHighlights } from "../lib/highlightLine";
import { TipCard } from "./TipCard";

interface TranscriptLineProps {
  line: string;
  lineStart: number;
  issues: AnalysisIssue[];
}

const SPEAKER_PATTERN = /^([^:：]{1,40})[:：]\s*(.*)$/s;

export function TranscriptLine({ line, lineStart, issues }: TranscriptLineProps) {
  const [openIssueId, setOpenIssueId] = useState<string | null>(null);

  if (line.trim().length === 0) {
    return <div className="transcript-line transcript-line--empty" />;
  }

  const match = line.match(SPEAKER_PATTERN);
  const speaker = match?.[1];
  const bodyText = match ? match[2] : line;
  // "Name: " 접두를 건너뛴, 실제 대사가 시작되는 transcript 전체 기준 offset
  const bodyOffset = match ? line.indexOf(bodyText, match[1].length) : 0;
  const segments = splitLineWithHighlights(bodyText, lineStart + bodyOffset, issues);
  const hasIssue = segments.some((segment) => segment.issue !== null);

  return (
    <div className="transcript-line">
      {hasIssue && (
        <span className="transcript-line__mark" aria-hidden="true">
          ◆
        </span>
      )}
      <p className="transcript-line__text">
        {speaker && <span className="transcript-line__speaker">{speaker}: </span>}
        {segments.map((segment, index) =>
          segment.issue ? (
            <span key={segment.issue.issue_id + index} className="transcript-line__highlight-wrap">
              <mark
                className="transcript-line__highlight"
                role="button"
                tabIndex={0}
                onClick={() =>
                  setOpenIssueId(openIssueId === segment.issue!.issue_id ? null : segment.issue!.issue_id)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setOpenIssueId(openIssueId === segment.issue!.issue_id ? null : segment.issue!.issue_id);
                  }
                }}
              >
                {segment.text}
              </mark>
              {openIssueId === segment.issue.issue_id && (
                <TipCard issue={segment.issue} onClose={() => setOpenIssueId(null)} />
              )}
            </span>
          ) : (
            <span key={index}>{segment.text}</span>
          )
        )}
      </p>
    </div>
  );
}
