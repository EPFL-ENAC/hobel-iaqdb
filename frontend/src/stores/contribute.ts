import {
  spaceTypeOptions,
  occupancyOptions,
  ventilationTypeOptions,
  physicalParameterOptions,
  yesNoOptions,
} from 'src/utils/options';
import { defineStore } from 'pinia';
import { api, baseUrl } from 'src/boot/api';
import {
  Study,
  Building,
  Space,
  Person,
  Instrument,
  InstrumentParameter,
  Dataset,
  FileNode,
} from 'src/models';

import { FileObject, DataFile } from 'src/components/models';
import P from 'app/dist/spa/assets/PageOne.d985d06c';

export const useContributeStore = defineStore(
  'contribute',
  () => {
    const study = ref<Study>({
      id: 0,
      identifier: '',
      name: '',
      description: '',
      contributors: [],
      buildings: [],
      instruments: [],
      datasets: [],
    } as Study);

    const dataFiles = ref<DataFile[]>([]);

    function reset() {
      study.value = {
        identifier: '',
        name: '',
        description: '',
        contributors: [],
        buildings: [],
        instruments: [],
        datasets: [],
      } as Study;
      dataFiles.value = [];
    }

    async function load(identifier: string) {
      return api.get(`/contribute/study-draft/${identifier}`).then((res) => study.value = res.data);
    }

    const inProgress = computed(
      () => study.value.name || study.value.description,
    );

    function addContributor() {
      let id = 1;
      while (study.value.contributors?.find((p: Person) => p.id === id)) {
        id++;
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
      } as Person);
    }

    function deleteContributor(i: number) {
      study.value.contributors?.splice(i, 1);
    }

    function addBuilding() {
      if (!study.value.buildings) {
        study.value.buildings = [];
      }
      let id = 1;
      while (
        study.value.buildings?.find(
          (bld: Building) => bld.id === id || bld.identifier === `${id}`,
        )
      ) {
        id++;
      }
      let country = '';
      if (study.value.buildings && study.value.buildings.length > 0) {
        country =
          study.value.buildings[study.value.buildings.length - 1].country;
      }
      study.value.buildings?.push({
        id: id,
        identifier: `${id}`,
        city: '',
        country,
        certification: {
          name: '',
          level: '',
        },
        spaces: [],
      } as Building);
    }

    function getSpaceDefaults() {
      return {
        space: spaceTypeOptions[0].value,
        occupancy: occupancyOptions[0].value,
        ventilation: ventilationTypeOptions[0].value,
        smoking: yesNoOptions[2].value,
        periods: [],
      };
    }

    function deleteBuilding(i: number) {
      study.value.buildings?.splice(i, 1);
    }

    function addSpace(bId: string) {
      const building = study.value.buildings?.find(
        (bld) => bld.identifier === bId,
      );
      if (!building) return;

      let id = 1;
      while (building.spaces?.find((rm) => rm.id === id || rm.identifier === `${id}`)) {
        id++;
      }
      building.spaces?.push({
        id: id,
        identifier: `${id}`,
        ...getSpaceDefaults(),
      } as Space);
    }

    function deleteSpace(bId: string, i: number) {
      const building = study.value.buildings?.find(
        (bld) => bld.identifier === bId,
      );
      if (!building) return;

      building.spaces?.splice(i, 1);
    }

    function addInstrument() {
      if (!study.value.instruments) {
        study.value.instruments = [];
      }
      let id = 1;
      while (
        study.value.instruments?.find(
          (inst: Instrument) => inst.id === id || inst.identifier === `${id}`,
        )
      ) {
        id++;
      }
      study.value.instruments?.push({
        id: id,
        identifier: `${id}`,
        manufacturer: '',
        model: '',
        equipment_grade_rating: 'unknown',
        placement: 'unknown',
      } as Instrument);
    }

    function deleteInstrument(i: number) {
      study.value.instruments?.splice(i, 1);
    }

    function addInstrumentParameter(instId: string) {
      const instrument = study.value.instruments?.find(
        (inst) => inst.identifier === instId,
      );
      if (!instrument) return;

      if (!instrument.parameters) {
        instrument.parameters = [];
      }
      let id = 1;
      while (
        instrument.parameters?.find(
          (param: InstrumentParameter) => param.id === id,
        )
      ) {
        id++;
      }
      instrument.parameters.push({
        id: id,
        physical_parameter: physicalParameterOptions[0].value,
        analysis_method: '',
        measurement_uncertainty: '',
      } as InstrumentParameter);
    }

    function deleteInstrumentParameter(instId: string, i: number) {
      const instrument = study.value.instruments?.find(
        (inst) => inst.identifier === instId,
      );
      if (!instrument) return;

      instrument.parameters?.splice(i, 1);
    }

    async function addDataset(dataFile: DataFile) {
      const uploaded = await uploadTmpFiles([dataFile.file]);
      if (!study.value.datasets) {
        study.value.datasets = [];
      }
      let name = dataFile.file.name;
      // remove extension
      const ext = name.split('.').pop();
      if (ext) {
        name = name.replace(`.${ext}`, '');
      }
      let id = 0;
      while (
        study.value.datasets?.find(
          (ds: Dataset) => ds.id === id,
        )
      ) {
        id++;
      }
      let idName = study.value.datasets?.find((ds: Dataset) => ds.name === name) ? 1 : 0;
      while (
        study.value.datasets?.find(
          (ds: Dataset) => ds.name === `${name}-${idName}`,
        )
      ) {
        idName++;
      }
      if (idName > 0) {
        name = `${name}-${idName}`;
      }
      study.value.datasets?.push({
        id: id,
        name: name,
        description: dataFile.file.name,
        variables: dataFile.variables,
        folder: uploaded,
      } as Dataset);
    }

    async function deleteDataset(i: number) {
      const dataset = study.value.datasets?.[i];
      if (!dataset) return;
      if (dataset.folder?.children) {
        await Promise.all(dataset.folder.children.map((f) => deleteFile(f)));
      }
      study.value.datasets?.splice(i, 1);
    }

    async function fetchAltitude(lon: number, lat: number) {
      return api
        .get('/map/elevation', { params: { lon, lat } })
        .then((res) => res.data);
    }

    async function fetchClimateZone(lon: number, lat: number) {
      return api
        .get('/map/climate-zone', { params: { lon, lat } })
        .then((res) => res.data);
    }

    async function readExcel(file: File) {
      const formData = new FormData();
      formData.append('files', file);
      return api.post('/contribute/study-excel', formData).then((res) => {
        console.log(res.data);
        study.value = res.data;
      });
    }

    async function saveOrUpdateDraft() {
      if (study.value.identifier !== '' && study.value.identifier !== '_draft') {
        return api.put(`/contribute/study-draft/${study.value.identifier}`, study.value)
          .then((res) => study.value = res.data);
      }
      return api.post('/contribute/study-draft', study.value)
        .then((res) => study.value = res.data);
    }

    async function deleteFile(file: FileNode) {
      return api.delete(`/files/${file.path}`);
    }

    function downloadFile(file: FileNode) {
      window.open(`${baseUrl}/files/${file.path}`);
    }

    function uploadTmpFiles(files: FileObject[]): Promise<FileNode> {
      const formData = new FormData();
      files.forEach((f) => {
        formData.append('files', f);
      });
      return api.post('/files/tmp', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }).then((res) => res.data);
    }

    return {
      study,
      inProgress,
      reset,
      load,
      addContributor,
      deleteContributor,
      addBuilding,
      deleteBuilding,
      addSpace,
      deleteSpace,
      addInstrument,
      deleteInstrument,
      addInstrumentParameter,
      deleteInstrumentParameter,
      addDataset,
      deleteDataset,
      downloadFile,
      fetchAltitude,
      fetchClimateZone,
      readExcel,
      saveOrUpdateDraft,
      uploadTmpFiles,
    };
  },
  { persist: true },
);
