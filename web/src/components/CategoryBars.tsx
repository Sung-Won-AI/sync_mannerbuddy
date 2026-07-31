import { CATEGORY_LABEL } from "../lib/constants";
import type { AnalysisScores } from "../shared/meetingTypes";
import type { FrequentIssue } from "../shared/dashboardTypes";

interface CategoryBarsProps {
  frequent: FrequentIssue[];
  fixed: FrequentIssue[];
}

export function CategoryBars({ frequent, fixed }: CategoryBarsProps) {
  const fixedByCategory = new Map(fixed.map((item) => [item.category, item.count]));
  const categories = Object.keys(CATEGORY_LABEL) as (keyof AnalysisScores)[];

  const rows = categories
    .map((category) => {
      const total = frequent.find((item) => item.category === category)?.count ?? 0;
      const fixedCount = Math.min(total, fixedByCategory.get(category) ?? 0);
      return { category, total, fixedCount };
    })
    .filter((row) => row.total > 0)
    .sort((a, b) => b.total - a.total);

  if (rows.length === 0) {
    return <p className="category-bars__empty">아직 감지된 이슈가 없어요.</p>;
  }

  const max = Math.max(...rows.map((row) => row.total));

  return (
    <div className="category-bars">
      <div className="category-bars__legend">
        <span className="category-bars__legend-item">
          <i className="category-bars__dot category-bars__dot--fixed" />
          실제로 고침
        </span>
        <span className="category-bars__legend-item">
          <i className="category-bars__dot category-bars__dot--pending" />
          아직 감지만 됨
        </span>
      </div>
      {rows.map(({ category, total, fixedCount }) => (
        <div className="category-bars__row" key={category}>
          <span className="category-bars__label">{CATEGORY_LABEL[category]}</span>
          <div className="category-bars__track">
            <div className="category-bars__total" style={{ width: `${(total / max) * 100}%` }}>
              <div
                className="category-bars__fixed"
                style={{ width: `${(fixedCount / total) * 100}%` }}
              />
            </div>
          </div>
          <span className="category-bars__value">{total}건</span>
        </div>
      ))}
    </div>
  );
}
