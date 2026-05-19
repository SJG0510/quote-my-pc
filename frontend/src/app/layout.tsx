import "./globals.css";
import type { Metadata } from "next";

import { DashboardShell } from "@/components/layout/DashboardShell";


export const metadata: Metadata = {
  title: "견적내드림 MVP",
  description: "예산과 목적 기반 조립 PC 추천 MVP",
};


export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  );
}
