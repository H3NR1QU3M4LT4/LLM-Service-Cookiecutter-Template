import { brand } from "./brand";

export type Environment = "local" | "dev" | "uat" | "prod";

const ENV_STYLE: Record<Environment, string> = {
  local: "bg-gray-200 text-gray-800",
  dev: "bg-sky-100 text-sky-800",
  uat: "bg-amber-100 text-amber-800",
  prod: "bg-leica-100 text-leica-800",
};

interface FooterProps {
  /** App/API version, e.g. the backend's APP_VERSION. */
  version?: string;
  environment?: Environment;
  info?: string;
}

/** Same footer in every Leica app: which environment and which version you are looking at. */
export default function Footer({ version, environment, info }: FooterProps) {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-gray-500 sm:px-6 lg:px-8">
        <span>
          © {new Date().getFullYear()} {brand.name}
        </span>
        <span className="flex flex-wrap items-center gap-3">
          {info && <span className="font-mono">{info}</span>}
          <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-gray-700">{version ? (/^\d/.test(version) ? `v${version}` : version) : "version unknown"}</span>
          {environment && <span className={`badge uppercase ${ENV_STYLE[environment]}`}>{environment}</span>}
        </span>
      </div>
    </footer>
  );
}
