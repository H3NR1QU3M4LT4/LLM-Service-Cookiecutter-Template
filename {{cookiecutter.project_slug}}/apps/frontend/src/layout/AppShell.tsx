import type { ReactNode } from "react";

import Footer from "./Footer";
import type { Environment } from "./Footer";
import Navbar from "./Navbar";
import type { NavItem } from "./Navbar";

interface AppShellProps {
  title: string;
  navItems?: NavItem[];
  activeNav?: string;
  onNavSelect?: (key: string) => void;
  navRight?: ReactNode;
  footerVersion?: string;
  footerEnvironment?: Environment;
  footerInfo?: string;
  children: ReactNode;
}

/** Page chrome shared by every Leica app: navbar, centred content column with fixed margins, footer. */
export default function AppShell({ title, navItems, activeNav, onNavSelect, navRight, footerVersion, footerEnvironment, footerInfo, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar title={title} items={navItems} active={activeNav} onSelect={onNavSelect} right={navRight} />
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-5 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      <Footer version={footerVersion} environment={footerEnvironment} info={footerInfo} />
    </div>
  );
}
