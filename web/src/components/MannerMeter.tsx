import { temperatureTone } from "../lib/constants";
import type { ScoreTrendPoint } from "../shared/dashboardTypes";
import { TrendSparkline } from "./TrendSparkline";

interface MannerMeterProps {
  value: number;
  trend: ScoreTrendPoint[];
}

export function MannerMeter({ value, trend }: MannerMeterProps) {
  const tone = temperatureTone(value);
  const fillPct = Math.min(100, Math.max(0, value));

  return (
    <div className="meter-card">
      <span className="meter-card__label">비즈니스 매너 온도</span>
      <span className={`meter-card__value meter-card__value--${tone}`}>{value}°</span>
      <div
        className="meter-card__track"
        role="meter"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="비즈니스 매너 온도"
      >
        <div className={`meter-card__fill meter-card__fill--${tone}`} style={{ width: `${fillPct}%` }} />
      </div>
      {trend.length > 1 && (
        <div className="meter-card__trend">
          <span className="meter-card__trend-label">최근 추이</span>
          <TrendSparkline points={trend} />
        </div>
      )}
    </div>
  );
}
