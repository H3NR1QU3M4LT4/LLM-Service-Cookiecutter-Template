import lbs from "../assets/leica-biosystems.png";
import lms from "../assets/leica-microsystems.png";

export type BrandKey = "lms" | "lbs";

export interface Brand {
  name: string;
  logo: string;
}

export const BRANDS: Record<BrandKey, Brand> = {
  lms: { name: "Leica Microsystems", logo: lms },
  lbs: { name: "Leica Biosystems", logo: lbs },
};

// Set when the project is generated (cookiecutter `brand`). VITE_BRAND=lms|lbs at build time overrides it.
const DEFAULT_BRAND: BrandKey = "lms";

/** Drives the navbar logo and the footer name. */
export const brand: Brand =
  BRANDS[(import.meta.env.VITE_BRAND as BrandKey | undefined) ?? DEFAULT_BRAND] ?? BRANDS[DEFAULT_BRAND];
