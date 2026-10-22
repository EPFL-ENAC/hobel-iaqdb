/** Rows and extra columns of a RankedBars list. */

export interface RankedRow<D> {
  /** unique among the rows */
  key: string;
  label: string;
  /** what the bar and the value column show */
  value: number;
  /** a click on the row emits `select` */
  clickable?: boolean;
  data: D;
}

export interface RankedColumn<D> {
  key: string;
  header: string;
  /** the cell of one row, or of the rows summed into "Other" */
  format: (rows: RankedRow<D>[]) => string;
}
