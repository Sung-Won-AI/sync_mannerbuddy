import type { ScoreTrendPoint } from "../shared/dashboardTypes";

interface TrendSparklineProps {
  points: ScoreTrendPoint[];
}

const WIDTH = 220;
const HEIGHT = 44;
const PAD = 6;

export function TrendSparkline({ points }: TrendSparklineProps) {
  if (points.length < 2) return null;

  const values = points.map((point) => point.average_score);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = (WIDTH - PAD * 2) / (points.length - 1);

  const coords = values.map((value, index) => {
    const x = PAD + index * stepX;
    const y = PAD + (HEIGHT - PAD * 2) * (1 - (value - min) / range);
    return [x, y] as const;
  });

  const path = coords.map(([x, y], index) => `${index === 0 ? "M" : "L"}${x} ${y}`).join(" ");
  const [lastX, lastY] = coords[coords.length - 1];

  return (
    <svg
      className="trend-sparkline"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={`최근 추이: ${points[0].date}부터 ${points[points.length - 1].date}까지 평균 점수 ${values[0]}에서 ${values[values.length - 1]}로 변화`}
    >
      <path d={path} className="trend-sparkline__line" />
      <circle cx={lastX} cy={lastY} r="4" className="trend-sparkline__dot" />
    </svg>
  );
}
