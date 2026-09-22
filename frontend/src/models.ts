export interface DBModel {
  id?: number | string;
  [Key: string]: unknown;
}

export interface Person extends DBModel {
  name: string;
  email: string;
  email_public: boolean;
  institution: string;
}

export interface Certification extends DBModel {
  program: string;
  level: string;
}

export interface Building extends DBModel {
  identifier: string;
  country: string;
  city: string;
  postcode?: string | undefined;
  timezone?: string;
  long?: number | undefined;
  lat?: number | undefined;
  altitude?: number | undefined;
  climate_zone?: string | undefined;
  type?: string;
  other_type?: string | undefined;
  outdoor_env?: string;
  other_outdoor_env?: string | undefined;
  green_certified?: string;
  construction_year?: number;
  renovation?: string;
  renovation_details?: string | undefined;
  renovation_year?: number | undefined;
  mechanical_ventilation?: string;
  particle_filtration_system?: string;
  particle_filtration_rating?: number;
  operable_windows?: string;
  airtightness?: number;
  age_group?: string;
  socioeconomic_status?: string;
  smoking?: string;
  spaces?: Space[];
  certifications?: Certification[];
}

interface ListResult {
  total: number;
  skip: number | undefined;
  limit: number | undefined;
}

export interface BuildingsResult extends ListResult {
  data: Building[];
}

export interface Study extends DBModel {
  identifier: string;
  name: string;
  description: string;
  website?: string;
  start_year?: number;
  end_year?: number;
  duration?: number;
  occupant_impact?: string[];
  other_indoor_param?: string[];
  citation?: string;
  doi?: string;
  funding?: string;
  ethics?: string;
  license?: string;
  data_processing?: string;
  contributors?: Person[];
  buildings?: Building[];
  instruments?: Instrument[];
  datasets?: Dataset[];
}
export interface ParseError {
    loc: string;
    msg: string;
    severity: string;
}

export interface StudyDraftParseResult {
    study: Study | null;
    errors: ParseError[];
}

export interface StudiesResult extends ListResult {
  data: Study[];
}

export interface StudySummary extends DBModel {
  identifier: string;
  name: string;
  description: string;
  color: string;
  countries: string[];
  cities: string[];
}
export interface StudySummariesResult extends ListResult {
  data: StudySummary[];
}
export interface Space extends DBModel {
  identifier: string;
  type: string;
  floor_area?: number | undefined;
  space_volume?: number | undefined;
  occupancy_density?: number | undefined;
  occupancy_number?: number | undefined;
  occupancy?: string | undefined;
  mechanical_ventilation_type?: string | undefined;
  other_mechanical_ventilation_type?: string | undefined;
  cooling_type?: string | undefined;
  other_cooling_type?: string | undefined;
  heating_type?: string | undefined;
  other_heating_type?: string | undefined;
  air_filtration?: string | undefined;
  printers?: string | undefined;
  carpets?: string | undefined;
  combustion_sources?: string | undefined;
  major_combustion_sources?: string | undefined;
  minor_combustion_sources?: string | undefined;
  pets?: string | undefined;
  dampness?: string | undefined;
  mold?: string | undefined;
  detergents?: string | undefined;
}

export interface SpacesResult extends ListResult {
  data: Space[];
}

export interface Instrument extends DBModel {
  identifier: string;
  manufacturer: string;
  model: string;
  equipment_grade_rating: string;
  placement: string;
  parameters?: InstrumentParameter[];
}

export interface InstrumentParameter extends DBModel {
  physical_parameter: string;
  analysis_method?: string;
  measurement_uncertainty?: string;
  note?: string;
}

export interface InstrumentsResult extends ListResult {
  data: Instrument[];
}

export interface Variable extends DBModel {
  name: string;
  type: string;
  unit?: string;
  format?: string;
  reference?: string;
}

export interface Dataset extends DBModel {
  name: string;
  description?: string;
  folder: FileNode;
  variables?: Variable[];
  // measurement load state, set by the backend after publish
  summary_status?: 'pending' | 'ready' | 'failed';
  summary_error?: string;
  load_report?: Record<string, unknown>;
}

export interface FileNode {
  name: string;
  path: string;
  size: number | undefined;
  alt_name: string | undefined;
  alt_path: string | undefined;
  alt_size: number | undefined;
  is_file: boolean;
  children: FileNode[] | undefined;
}

export interface UploadResult {
  files: FileNode[];
}

// ---- Explore charts API (/stats/*), mirrors backend api/models/explore.py

export type ExploreEntity = 'studies' | 'buildings' | 'spaces' | 'datasets';
export type ExploreGrain = 'day' | 'hour' | 'raw';
export type ExploreSource = 'metadata' | 'measurements' | 'relationships';
export type ExploreAgg =
  | 'count'
  | 'availability'
  | 'coverage'
  | 'stats'
  | 'exceedance'
  | 'pairs'
  | 'matrix';

export interface ExploreDimension {
  key: string;
  label: string;
  entity: 'study' | 'building' | 'space' | 'dataset' | 'parameter' | 'time';
  filter_path: string | null;
  drill_to: string | null;
  kind: 'category' | 'time';
}

export interface ExploreBenchmark {
  id: number;
  parameter: string;
  source: string;
  averaging: 'hour' | 'day';
  value: number;
  unit: string;
  note?: string;
}

export interface ExploreParameter {
  slug: string;
  label: string;
  reference: string;
  unit: string;
  benchmarks: ExploreBenchmark[];
}

export interface ExploreSchema {
  dimensions: ExploreDimension[];
  parameters: ExploreParameter[];
  metrics: string[];
  version: number;
}

/** Same dialect as /catalog/*, anchored on the study. */
export interface ExploreFilter {
  [key: string]: unknown;
  $building?: Record<string, unknown>;
  $space?: Record<string, unknown>;
  $dataset?: Record<string, unknown>;
}

export interface ExploreParams {
  filter?: ExploreFilter;
  from?: string;
  to?: string;
  parameters?: string[];
  by?: string[];
  agg?: ExploreAgg;
  grain?: ExploreGrain;
  qualifier?: string[];
  threshold?: number;
  entity?: ExploreEntity;
  fields?: string[];
  x?: string;
  y?: string;
  method?: 'pearson' | 'spearman';
}

export interface ExploreStats {
  mean: number;
  sd?: number;
  min: number;
  p05: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  max: number;
}

export interface ExploreBucket {
  key: (string | null)[];
  n: number;
  n_records?: number;
  stats?: ExploreStats;
  exceedance?: { threshold: number; n_above: number; share: number };
  coverage?: { n_datasets: number; n_missing: number; first_at?: string; last_at?: string };
  availability?: { present: number; total: number };
  fit?: { slope?: number; intercept?: number; r2?: number; r?: number };
  points?: [number, number][];
  sampled?: boolean;
}

export interface ExploreMeta {
  source: ExploreSource;
  agg: ExploreAgg;
  grain: ExploreGrain | 'space' | 'entity';
  dimensions: string[];
  parameters: string[];
  unit?: string;
  from?: string;
  to?: string;
  n: number;
  n_records?: number;
  version: number;
  available_parameters?: string[];
}

export interface ExploreResult {
  meta: ExploreMeta;
  buckets: ExploreBucket[];
}

export interface Contribution extends DBModel {
  created_at?: string;
  created_by?: string;
  updated_at?: string;
  updated_by?: string;
  published_at?: string;
  published_by?: string;
  data_embargo?: string;
}

export interface StudyBundle {
  study: Study;
  contribution?: Contribution;
}
