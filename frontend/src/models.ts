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
  postcode?: string;
  timezone?: string;
  long?: number;
  lat?: number;
  altitude?: number;
  climate_zone?: string;
  type?: string;
  other_type?: string;
  outdoor_env?: string;
  other_outdoor_env?: string;
  green_certified?: string;
  construction_year?: number;
  renovation?: string;
  renovation_details?: string;
  renovation_year?: number;
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

export interface StudiesResult extends ListResult {
  data: Study[];
}

export interface Space extends DBModel {
  identifier: string;
  type: string;
  floor_area?: number;
  space_volume?: number;
  occupancy_density?: number;
  occupancy_number?: number;
  occupancy?: string;
  mechanical_ventilation_type?: string;
  other_mechanical_ventilation_type?: string;
  cooling_type?: string;
  other_cooling_type?: string;
  heating_type?: string;
  other_heating_type?: string;
  air_filtration?: string;
  printers?: string;
  carpets?: string;
  combustion_sources?: string;
  major_combustion_sources?: string;
  minor_combustion_sources?: string;
  pets?: string;
  dampness?: string;
  mold?: string;
  detergents?: string;
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