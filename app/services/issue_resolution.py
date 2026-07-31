from app.schemas.analysis import AnalysisIssue
from app.services.masking_service import masking_service


def _drop_overlapping_issues(issues: list[AnalysisIssue]) -> list[AnalysisIssue]:
    # AI가 "문장 전체를 다시 쓰는" issue와 그 안에 포함된 단어 단위 issue(예: "pls")를
    # 함께 반환할 때가 있다. 겹치는 채로 둘 다 하이라이트하면 프론트엔드에서 하이라이트
    # span이 서로 안에 중첩되어 오프셋 계산이 깨지므로, 넓은 범위를 우선하고 그 안에
    # 겹치는 좁은 issue는 버린다.
    widest_first = sorted(
        issues,
        key=lambda issue: issue.end_index - issue.start_index,
        reverse=True,
    )
    kept: list[AnalysisIssue] = []
    for issue in widest_first:
        overlaps = any(
            issue.start_index < k.end_index and issue.end_index > k.start_index
            for k in kept
        )
        if not overlaps:
            kept.append(issue)
    return sorted(kept, key=lambda issue: issue.start_index)


def resolve_and_restore_issues(
    *,
    original_text: str,
    replacements: dict[str, str],
    issues: list[AnalysisIssue],
) -> list[AnalysisIssue]:
    """AI가 마스킹된 텍스트를 보고 직접 센 start_index/end_index는 (특히 텍스트가
    길어질수록) 실제 위치와 어긋나기 쉽다. AI가 그대로 베껴 적은 original/suggestion
    문구의 마스킹을 복원한 뒤, 그 문구를 원문에서 다시 찾아 오프셋을 신뢰할 수 있게
    재계산한다. 못 찾으면(패러프레이즈 등) AI가 준 오프셋으로 폴백한다."""
    resolved: list[AnalysisIssue] = []
    for issue in issues:
        restored_original = masking_service.restore(issue.original, replacements)
        restored_suggestion = masking_service.restore(issue.suggestion, replacements)

        found_at = original_text.find(restored_original)
        start_index = found_at if found_at != -1 else issue.start_index
        end_index = (
            found_at + len(restored_original) if found_at != -1 else issue.end_index
        )

        resolved.append(
            AnalysisIssue(
                **{
                    **issue.model_dump(),
                    "original": restored_original,
                    "suggestion": restored_suggestion,
                    "start_index": start_index,
                    "end_index": end_index,
                }
            )
        )

    return _drop_overlapping_issues(resolved)
