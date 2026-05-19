"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "견적 입력" },
  { href: "/quote/alternatives", label: "대안 비교" },
  { href: "/quote/archive", label: "보관함" },
];

type Props = {
  children: React.ReactNode;
};

export function DashboardShell({ children }: Props) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <header className="global-nav">
        <Link href="/" className="brand-mark">
          견적내드림
        </Link>

        <nav className="global-nav-links">
          {navItems.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={label} href={href} className={`nav-link${active ? " active" : ""}`}>
                {label}
              </Link>
            );
          })}
        </nav>

        <Link href="/" className="nav-buy">
          새 견적
        </Link>
      </header>

      <div className="main-column">{children}</div>
    </div>
  );
}
