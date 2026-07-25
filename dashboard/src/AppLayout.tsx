// 페이지 간 이동용 최소 네비게이션 (디자인 검토/QA 편의 목적)

import { NavLink, Outlet } from "react-router-dom";
import "./AppLayout.css";

const NAV_ITEMS = [
  { to: "/", label: "대시보드", end: true },
  { to: "/review", label: "복습·퀴즈", end: false },
  { to: "/meeting-summary", label: "회의 요약", end: false }
];

export function AppLayout() {
  return (
    <div className="app-layout">
      <nav className="app-nav">
        <span className="app-nav__brand">MannerBuddy</span>
        <div className="app-nav__links">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `app-nav__link${isActive ? " app-nav__link--active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <Outlet />
    </div>
  );
}
