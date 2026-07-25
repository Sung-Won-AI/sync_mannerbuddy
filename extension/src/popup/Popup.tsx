// 확장 프로그램 툴바 팝업: 이번 주 교정 통계 요약을 대시보드로 연결하는 진입점.

export function Popup() {
  return (
    <div style={{ width: 240, padding: 16, fontFamily: "sans-serif" }}>
      <h1 style={{ fontSize: 16, margin: 0 }}>MannerBuddy</h1>
      <p style={{ fontSize: 12, color: "#666" }}>Gmail에서 실시간 매너 교정이 활성화되었습니다.</p>
    </div>
  );
}
