export interface DBModel {
  _id?: string;
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
  altitude?: number;
  climate_zone?: string;
  longitude?: number;
  latitude?: number;
  rooms?: Room[]
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
  contact?: Person;
  buildings?: Building[]
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Room extends DBModel {
  identifier: string;
  space: string;
  occupancy: string;
  ventilation: string;
  smoking: string;
}

export interface RoomsResult extends ListResult {
  data: Room[]
}
