import type { ReactNode } from "react";

import { brand } from "./brand";

export interface NavItem {
  key: string;
  label: string;
}

interface NavbarProps {
  title: string;
  items?: NavItem[];
  active?: string;
  onSelect?: (key: string) => void;
  /** Right-hand slot: version badge, user menu... */
  right?: ReactNode;
}

function Logo() {
  return brand.logo ? (
    <img src={brand.logo} alt={brand.name} className="h-9 w-auto shrink-0" />
  ) : (
    <span className="shrink-0 rounded-sm bg-leica-600 px-2.5 py-1 text-sm font-bold tracking-wide text-white">LEICA</span>
  );
}

/** Same header in every Leica app: logo, app title, section links, right slot. */
export default function Navbar({ title, items = [], active, onSelect, right }: NavbarProps) {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-6 px-4 sm:px-6 lg:px-8">
        <Logo />
        <span className="hidden border-l border-gray-300 pl-6 text-base font-semibold text-gray-900 sm:block">{title}</span>
        <nav aria-label="Sections" className="flex flex-1 items-center gap-1 overflow-x-auto">
          {items.map((item) => (
            <button
              key={item.key}
              type="button"
              aria-current={item.key === active ? "page" : undefined}
              onClick={() => onSelect?.(item.key)}
              className={`whitespace-nowrap border-b-4 px-3 py-5 text-sm transition-colors ${
                item.key === active
                  ? "border-leica-600 font-semibold text-leica-700"
                  : "border-transparent text-gray-700 hover:text-leica-700"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="flex shrink-0 items-center gap-3 text-sm">{right}</div>
      </div>
    </header>
  );
}
