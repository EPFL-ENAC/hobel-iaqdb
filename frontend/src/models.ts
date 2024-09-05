export interface DBModel {
  id?: number | string;
  [Key: string]: unknown;
}

export interface Person extends DBModel {
  name: string;
  email: string;
  institution: string;
}

export interface Building extends DBModel {
  identifier: string;
  country: string;
  city: string;
  postcode?: string;
  timezone?: string;
  long: number;
  lat: number;
  altitude?: number;
  climate_zone?: string;
  type?: string;
  outdoor_env?: string;
  construction_year?: number;
  renovation?: string;
  renovation_year?: number;
  mechanical_ventilation?: string;
  operable_windows: string;
  special_population_designation?: string;
  special_population?: string;
  smoking?: string;
  spaces?: Space[]
}

interface ListResult {
  total: number;
  skip: number | undefined;
  limit: number | undefined;
}

export interface BuildingsResult extends ListResult {
  data: Building[]
}

export interface Study extends DBModel {
  identifier: string;
  name: string;
  description: string;
  website?: string;
  start_year?: number;
  end_year?: number;
  duration?: number;
  cite?: string;
  doi?: string;
  funding?: string;
  ethics?: string;
  license?: string;
  contributors?: Person[];
  buildings?: Building[];
  instruments?: Instrument[];
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Space extends DBModel {
  identifier: string;
  type: string;
  occupancy?: string;
  mechanical_ventilation_status?: string;
  mechanical_ventilation_type?: string;
  windows_status?: string;
  ventilation_rate?: number;
  air_change_rate?: number;
  particle_filtration_rating: number;
  cooling_status?: string;
  cooling_type?: string;
  heating_status?: string;
  heating_type?: string;
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
  data: Space[]
}

export interface Instrument extends DBModel {
  identifier: string;
  manufacturer: string;
  model: string;
  equipment_grade_rating: string;
  placement: string;
}