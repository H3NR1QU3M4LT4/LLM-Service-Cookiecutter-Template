import lms from "../assets/leica-microsystems.png";

export type BrandKey = "lms" | "lbs";

export interface Brand {
  name: string;
  /** Logo image; undefined falls back to a text wordmark until the asset is added. */
  logo?: string;
}

// Drop the Leica Biosystems logo at src/assets/leica-biosystems.png (or .svg), in both apps: it is picked up here.
const lbsLogo = Object.values(
  import.meta.glob<string>("../assets/leica-biosystems.{png,svg}", { eager: true, import: "default" }),
)[0];

export const BRANDS: Record<BrandKey, Brand> = {
  lms: { name: "Leica Microsystems", logo: lms },
  lbs: { name: "Leica Biosystems", logo: lbsLogo },
};

/** Chosen at build time with VITE_BRAND=lms|lbs (default lms). */
export const brand: Brand = BRANDS[(import.meta.env.VITE_BRAND as BrandKey | undefined) ?? "lms"] ?? BRANDS.lms;
