export const fmtMs = (value: number | null | undefined): string =>
  value === null || value === undefined ? "—" : `${Math.round(value * 10) / 10} ms`;

export const fmtPercent = (value: number | null | undefined): string =>
  value === null || value === undefined ? "—" : `${Math.round(value * 10) / 10}%`;
