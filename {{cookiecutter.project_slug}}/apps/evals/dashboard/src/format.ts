export const num = (x: number | null, digits = 0) => (x === null ? "–" : x.toFixed(digits));
export const pct = (x: number) => `${Math.round(x * 100)}%`;
export const usd = (x: number | null) => (x === null ? "–" : `$${x.toFixed(4)}`);
export const when = (iso: string) => iso.replace("T", " ").slice(0, 16);

/** "+0.3" / "-0.3" / "" next to a value, relative to the baseline; `goodWhenHigher` picks the colour. */
export function delta(value: number | null, base: number | null, goodWhenHigher: boolean, digits = 2) {
  if (value === null || base === null || value === base) return null;
  const diff = value - base;
  const good = goodWhenHigher ? diff > 0 : diff < 0;
  return { text: `${diff > 0 ? "+" : ""}${diff.toFixed(digits)}`, color: good ? "text-green-700" : "text-leica-700" };
}
