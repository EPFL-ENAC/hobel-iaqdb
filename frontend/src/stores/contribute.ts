import { spaceTypeOptions, occupancyOptions, ventilationTypeOptions, yesNoOptions } from 'src/utils/options';
import { v4 as uuidv4 } from 'uuid';
import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { Study, Building, Space, Person, Instrument } from 'src/models'; 

export const useContributeStore = defineStore('contribute', () => {

  const study = ref<Study>({
    identifier: '',
    name: '',
    description: '',
    contact: {} as Person,
    buildings: [],
    instruments: []
  } as Study);

  function reset() {
    study.value = {
      identifier: '',
      name: '',
      description: '',
      contact: {} as Person,
      buildings: [],
      instruments: []
    } as Study;
  }

  function addContributor() {
    let id = 1;
    while (study.value.contributors?.find((p: Person) => p.id === id)) {
      id++
    }
    if (!study.value.contributors) {
      study.value.contributors = [];
    }
    study.value.contributors?.push({
      id: id,
      name: '',
      email: '',
      email_public: true,
      institution: '',
    } as Person)
  }

  function deleteContributor(i: number) {
    study.value.contributors?.splice(i, 1);
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
      id: `__${uuidv4()}`,
      identifier: `${id}`,
      city: '',
      country,
      certification: {
        name: '',
        level: '',
      },
      spaces: []
    } as Building)
  }

  function getSpaceDefaults() {
    return {
      space: spaceTypeOptions[0].value,
      occupancy: occupancyOptions[0].value,
      ventilation: ventilationTypeOptions[0].value,
      smoking: yesNoOptions[2].value,
      periods: []
    };
  }

  function deleteBuilding(i: number) {
    study.value.buildings?.splice(i, 1);
  }

  function addSpace(bId: string) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;

    let id = 1;
    while (building.spaces?.find((rm) => rm.identifier === `${id}`)) {
      id++;
    }
    building.spaces?.push({
      id: `__${uuidv4()}`,
      identifier: `${id}`,
      ...getSpaceDefaults(),
    } as Space);
  }

  function deleteSpace(bId: string, i: number) {
    const building = study.value.buildings?.find((bld) => bld.identifier === bId);
    if (!building) return;

    building.spaces?.splice(i, 1);
  }

  function addInstrument() {
    let id = 1;
    while (study.value.instruments?.find((inst: Instrument) => inst.identifier === `${id}`)) {
      id++
    }
    study.value.instruments?.push({
      id: `__${uuidv4()}`,
      identifier: `${id}`,
      manufacturer: '',
      model: '',
      equipment_grade_rating: 'unknown',
      placement: 'unknown',
    } as Instrument)
  }

  function deleteInstrument(i: number) {
    study.value.instruments?.splice(i, 1);
  }

  async function fetchAltitude(lon: number, lat: number) {
    return api.get('/map/elevation', { params: { lon, lat } }).then((res) => res.data)
  }

  async function fetchClimateZone(lon: number, lat: number) {
    return api.get('/map/climate-zone', { params: { lon, lat } }).then((res) => res.data)
  }

  async function readExcel(file: File) {
    const formData = new FormData();
    formData.append('files', file);
    return api.post('/catalog/study-excel', formData).then((res) => {
      console.log(res.data);
      study.value = res.data;
    });
  }

  return {
    study,
    reset,
    addContributor,
    deleteContributor,
    addBuilding,
    deleteBuilding,
    addSpace,
    deleteSpace,
    addInstrument,
    deleteInstrument,
    fetchAltitude,
    fetchClimateZone,
    readExcel,
  }
}, { persist: true })