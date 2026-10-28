/** Rows and extra columns of a RankedBars list. */

export interface RankedRow<D> {
  /** unique among the rows */
  key: string;
  label: string;
  /** what the bar and the value column show */
  value: number;
  /** a click on the row emits `select` */
  clickable?: boolean;
  /** the bar's colour, over the highlight */
  color?: string;
  /** said on hover */
  title?: string;
  data: D;
}

/** A line above the rows standing for all of them, e.g. their average. */
export interface RankedSummary {
  label: string;
  /** null while there are no rows to stand for: the line keeps its place, blank */
  value: number | null;
  color?: string;
  title?: string;
}

export interface RankedColumn<D> {
  key: string;
  header: string;
  /** the cell of one row, or of the rows summed into "Other" */
  format: (rows: RankedRow<D>[]) => string;
}
