import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { v4 as uuidv4 } from 'uuid';
import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { Study, Building, Room, Period, Person } from 'src/models'; 

export const useContributeStore = defineStore('contribute', () => {

  const study = ref<Study>({
    identifier: '',
    name: '',
    description: '',
    contact: {} as Person,
    buildings: []
  } as Study);

  function reset() {
    study.value = {
      identifier: '',
      name: '',
      description: '',
      contact: {} as Person,
      buildings: []
    } as Study;
  }

  function addBuilding() {
    let id = 1;
    while (study.value.buildings?.find((bld: Building) => bld.identifier === `${id}`)) {
      id++
    }
    let country = '';
    if (study.value.buildings && study.value.buildings.length > 0) {
      country = study.value.buildings[study.value.buildings.length - 1].country;
    }
    study.value.buildings?.push({
      _id: `__${uuidv4()}`,
      identifier: `${id}`,
      city: '',
      country,
      certification: {
        name: '',
        level: '',
      },
      rooms: []
    } as Building)
  }

  function getRoomDefaults() {
    return {
      space: spaceTypeOptions[0].value,
      occupancy: occupancyOptions[0].value,
      ventilation: ventilationOptions[0].value,
      smoking: yesNoOptions[2].value,
      periods: []
    };
  }

  function deleteBuilding(i: number) {
    study.value.buildings?.splice(i, 1);
  }

  function addRoom(bId: string) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;

    let id = 1;
    while (building.rooms?.find((rm) => rm.identifier === `${id}`)) {
      id++;
    }
    building.rooms?.push({
      _id: `__${uuidv4()}`,
      identifier: `${id}`,
      ...getRoomDefaults(),
    } as Room);
  }

  function deleteRoom(bId: string, i: number) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;

    building.rooms?.splice(i, 1);
  }

  function addPeriod(bId: string, rId: string) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;
    const room = building.rooms?.find((rm) => rm.identifier === rId);
    if (!room) return;

    let id = 1;
    while (room.periods.find((prd) => prd.identifier === `${id}`)) {
      id++;
    }
    room.periods.push({
      _id: `__${uuidv4()}`,
      identifier: `${id}`,
    } as Period);
  }

  function deletePeriod(bId: string, rId: string, i: number) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;
    const room = building.rooms?.find((rm) => rm.identifier === rId);
    if (!room) return;

    room.periods.splice(i, 1);
  }

  async function fetchAltitude(lon: number, lat: number) {
    return api.get('/map/elevation', { params: { lon, lat } }).then((res) => res.data)
  }

  async function fetchClimateZone(lon: number, lat: number) {
    return api.get('/map/climate-zone', { params: { lon, lat } }).then((res) => res.data)
  }

  return {
    study,
    reset,
    addBuilding,
    deleteBuilding,
    addRoom,
    deleteRoom,
    addPeriod,
    deletePeriod,
    fetchAltitude,
    fetchClimateZone
  }
})