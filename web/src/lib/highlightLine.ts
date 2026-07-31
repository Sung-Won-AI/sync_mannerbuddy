import type { AnalysisIssue } from "../shared/meetingTypes";

export interface LineSegment {
  text: string;
  issue: AnalysisIssue | null;
}

/**
 * transcript 전체 기준 start_index/end_index로 오는 issue들을, 화면에는 줄 단위로
 * 쪼개서 그리기 위해 한 줄(lineStart~lineStart+line.length) 범위로 다시 잘라준다.
 */
export function splitLineWithHighlights(
  line: string,
  lineStart: number,
  issues: AnalysisIssue[]
): LineSegment[] {
  const lineEnd = lineStart + line.length;
  const relevant = issues
    .filter((issue) => issue.start_index < lineEnd && issue.end_index > lineStart)
    .sort((a, b) => a.start_index - b.start_index);

  if (relevant.length === 0) {
    return [{ text: line, issue: null }];
  }

  const segments: LineSegment[] = [];
  let cursor = lineStart;

  for (const issue of relevant) {
    const start = Math.max(issue.start_index, lineStart);
    const end = Math.min(issue.end_index, lineEnd);
    if (start > cursor) {
      segments.push({ text: line.slice(cursor - lineStart, start - lineStart), issue: null });
    }
    if (end > start) {
      segments.push({ text: line.slice(start - lineStart, end - lineStart), issue });
      cursor = end;
    }
  }
  if (cursor < lineEnd) {
    segments.push({ text: line.slice(cursor - lineStart), issue: null });
  }

  return segments.filter((segment) => segment.text.length > 0);
}
