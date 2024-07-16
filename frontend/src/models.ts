export interface DBModel {
  _id: number;
  [Key: string]: unknown;
}

export interface Building extends DBModel {
  slug: string;
  country: string;
  city: string;
  altitude: number;
  climate_zone: string;
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
  slug: string;
  name: string;
  description: string;
  start_year: number;
  end_year: number;
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Room extends DBModel {
  slug: string;
  space: string;
  ventilation: string;
  smoking: string;
}

export interface RoomsResult extends ListResult {
  data: Room[]
}