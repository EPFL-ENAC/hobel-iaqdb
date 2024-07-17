import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';

import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { Study, Building, Room, Person } from 'src/models'; 

export const useContributeStore = defineStore('contribute', () => {

  const study = ref<Study>({
    contact: {} as Person,
    buildings: [{
      identifier: '1',
      name: '',
      description: '',
      certification: {
        name: '',
        level: '',
      },
      rooms: [{
        identifier: '1',
        ...getRoomDefaults(),
      }]
    }]
  } as Study);

  function reset() {
    study.value = {
      identifier: '1',
      contact: {} as Person,
      buildings: [{
        identifier: '1',
        certification: {
          name: '',
          level: '',
        },
        rooms: [{
          identifier: '1',
        ...getRoomDefaults(),
        }]
      }]
    } as Study;
  }

  function addBuilding() {
    let id = 1;
    while (study.value.buildings.find((bld: Building) => bld.identifier === `${id}`)) {
      id++
    }
    let country = '';
    if (study.value.buildings.length > 0) {
      country = study.value.buildings[study.value.buildings.length - 1].country;
    }
    study.value.buildings.push({
      identifier: `${id}`,
      certification: {
        name: '',
        level: '',
      },
      rooms: [{
        identifier: '1',
        ...getRoomDefaults(),
      }],
      country
    } as Building)
  }

  function getRoomDefaults() {
    return {
      space: spaceTypeOptions[0].value,
      occupancy: occupancyOptions[0].value,
      ventilation: ventilationOptions[0].value,
      smoking: yesNoOptions[2].value,
    };
  }

  function deleteBuilding(i: number) {
    study.value.buildings.splice(i, 1);
  }

  function addRoom(bId: string) {
    const building = study.value.buildings.find((bld) => bld.identifier === bId);
    if (!building) return;

    let id = 1;
    while (building.rooms.find((rm) => rm.identifier === `${id}`)) {
      id++;
    }
    building.rooms.push({
      identifier: `${id}`,
      space: spaceTypeOptions[0].value,
      occupancy: occupancyOptions[0].value,
      ventilation: ventilationOptions[0].value,
      smoking: yesNoOptions[2].value,
    } as Room);
  }

  function deleteRoom(bId: string, i: number) {
    const building = study.value.buildings.find((bld) => bld.identifier === bId);
    if (!building) return;

    building.rooms.splice(i, 1);
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
    fetchAltitude,
    fetchClimateZone
  }
})