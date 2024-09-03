export interface DBModel {
  id?: number;
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
  address?: string;
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
  contact?: Person;
  buildings?: Building[];
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Space extends DBModel {
  identifier: string;
  type: string;
  occupancy?: string;
  ventilation?: string;
  ventilation_rate?: number;
  air_change_rate?: number;
  particle_filtration_rating: number;
  heating?: string;
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
  periods: Period[];
}

export interface SpacesResult extends ListResult {
  data: Space[]
}

export interface Period extends DBModel {
  identifier: string;
  start_date: string;
  end_data: string;
  ventilation: string;
  ventilation_rate: number;
  air_change_rate: number;
  particle_filtration_rating: number;
  cooling_strategy: string;
  heating_strategy: string;
  standalone_air_filtration: string;
  combustion_sources: string;
  major_combustion_sources: string;
  small_combustion_sources: string;
  printers: string;
  carpets: string;
  pets: string;
  visible_dampness: string;
  visible_mold: string;
  cleaning_with_detergents: string;
}