export interface DBModel {
  id?: number;
  [Key: string]: unknown;
}

export interface Person {
  name: string;
  email: string;
  institution: string;
}

export interface Building extends DBModel {
  identifier: string;
  country: string;
  city: string;
  long: number;
  lat: number;
  altitude?: number;
  climate_zone?: string;
  longitude?: number;
  latitude?: number;
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
  start_year?: number;
  end_year?: number;
  reference?: string;
  doi?: string;
  cite?: string;
  contacts?: Person[];
  buildings?: Building[];
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Space extends DBModel {
  identifier: string;
  space: string;
  occupancy: string;
  ventilation: string;
  smoking: string;
  periods: Period[];
}

export interface SpacesResult extends ListResult {
  data: Space[]
}

export interface Period extends DBModel {
  identifier: string;
  start_date: string;
  end_data: string;
  ventilation_strategy: string;
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