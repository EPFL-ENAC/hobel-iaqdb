export interface Building {
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

export interface Study {
  slug: string;
  name: string;
  description: string;
}

export interface StudiesResult extends ListResult {
  data: Study[]
}

export interface Room {
  slug: string;
  space: string;
  ventilation: string;
  smoking: string;
}

export interface RoomsResult extends ListResult {
  data: Room[]
}