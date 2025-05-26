import {
  buildingSpaceTypeOptions,
  occupancyOptions,
  mechanicalVentilationTypeOptions,
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

export const useContributeStore = defineStore(
  'contribute',
  () => {

    const authStore = useAuthStore();

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

    function addBuilding(buildingSource: Building | undefined = undefined) {
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
      if (buildingSource) {
        const buildingCopy = JSON.parse(JSON.stringify(buildingSource));
        buildingCopy.id = id;
        buildingCopy.identifier = `${id}`;
        study.value.buildings?.push(buildingCopy);
      } else {
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
    }

    function getSpaceDefaults(type: string) {
      let space = 'other';
      if (buildingSpaceTypeOptions[type]) {
        space = buildingSpaceTypeOptions[type][0].value;
      }
      return {
        space,
        occupancy: occupancyOptions[0].value,
        mechanical_ventilation_type: mechanicalVentilationTypeOptions[0].value,
        smoking: yesNoOptions[2].value,
        periods: [],
      };
    }

    function deleteBuilding(i: number) {
      study.value.buildings?.splice(i, 1);
    }

    function addSpace(bId: string, spaceSource: Space | undefined = undefined) {
      const building = study.value.buildings?.find(
        (bld) => bld.identifier === bId,
      );
      if (!building) return;

      let id = 1;
      while (building.spaces?.find((rm) => rm.id === id || rm.identifier === `${id}`)) {
        id++;
      }
      if (spaceSource) {
        const spaceCopy = JSON.parse(JSON.stringify(spaceSource));
        spaceCopy.id = id;
        spaceCopy.identifier = `${id}`;
        building.spaces?.push(spaceCopy);
      } else {
        building.spaces?.push({
          id: id,
          identifier: `${id}`,
          ...getSpaceDefaults(building.type),
        } as Space);
      }
    }

    function deleteSpace(bId: string, i: number) {
      const building = study.value.buildings?.find(
        (bld) => bld.identifier === bId,
      );
      if (!building) return;

      building.spaces?.splice(i, 1);
    }

    function addInstrument(instrumentSource: Instrument | undefined = undefined) {
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
      if (instrumentSource) {
        const instrumentCopy = JSON.parse(JSON.stringify(instrumentSource));
        instrumentCopy.id = id;
        instrumentCopy.identifier = `${id}`;
        study.value.instruments?.push(instrumentCopy);
      } else {
        study.value.instruments?.push({
          id: id,
          identifier: `${id}`,
          manufacturer: '',
          model: '',
          equipment_grade_rating: 'unknown',
          placement: 'unknown',
        } as Instrument);
      }
    }

    function deleteInstrument(i: number) {
      study.value.instruments?.splice(i, 1);
    }

    function addInstrumentParameter(instId: string, parameterSource: InstrumentParameter | undefined = undefined) {
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
      if (parameterSource) {
        const parameterCopy = JSON.parse(JSON.stringify(parameterSource));
        parameterCopy.id = id;
        instrument.parameters?.push(parameterCopy);
      } else {
        instrument.parameters.push({
          id: id,
          physical_parameter: physicalParameterOptions[0].value,
          analysis_method: '',
          measurement_uncertainty: '',
        } as InstrumentParameter);
      }
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

    async function updateDataset(dataset: Dataset, dataFile: DataFile) {
      const uploaded = await uploadTmpFiles([dataFile.file]);
      dataset.variables = dataFile.variables;
      dataset.folder = uploaded;
      return dataset;
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
      let identifier = study.value.identifier;
      if (!isUUID(identifier)) {
        identifier = '';
      }
      const formData = new FormData();
      formData.append('files', file);
      return api.post('/contribute/study-excel', formData).then((res) => {
        console.log(res.data);
        study.value = res.data;
        study.value.identifier = identifier;
      });
    }

    async function getDrafts() {
      if (!authStore.isAuthenticated) return Promise.reject('Not authenticated');
      return authStore.updateToken().then(() => 
        api.get('/contribute/study-drafts', {
          headers: {
            Authorization: `Bearer ${authStore.accessToken}`,
          },
        })
          .then((res) => res.data));
    }

    function isUUID(str: string) {
      return str.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    }

    async function saveOrUpdateDraft() {
      // check study identifier is a valid uuid
      if (!isUUID(study.value.identifier)) {
        study.value.identifier = '';
      }
      // make sure numeric fields are numbers or undefined
      ['start_year', 'end_year', 'duration'].forEach((field) => {
        if (typeof study.value[field] !== 'number') study.value[field] = undefined;
      });
      study.value.buildings?.forEach((b) => {
        ['construction_year', 'renovation_year', 'particle_filtration_rating', 'long', 'lat', 'altitude'].forEach((field) => {
          if (typeof b[field] !== 'number') b[field] = undefined;
        });
        b.spaces?.forEach((s) => {
          ['floor_area', 'space_volume', 'occupancy_density', 'ventilation_rate', 'air_change_rate'].forEach((field) => {
            if (typeof s[field] !== 'number') s[field] = undefined;
          });
        });
      });
      if (study.value.identifier !== '' && study.value.identifier !== '_draft') {
        // check if study exists
        return api.get(`/contribute/study-draft/${study.value.identifier}`).then(() => {
          // update existing study
          return api.put(`/contribute/study-draft/${study.value.identifier}`, study.value)
            .then((res) => study.value = res.data);
        }).catch(() => {
          // create new study, ensure identifier is empty
          study.value.identifier = '';
          return api.post('/contribute/study-draft', study.value)
            .then((res) => study.value = res.data);
        });
      }
      return api.post('/contribute/study-draft', study.value)
        .then((res) => study.value = res.data);
    }

    async function publishDraft(study: Study) {
      if (!authStore.isAuthenticated) return Promise.reject('Not authenticated');
      return authStore.updateToken().then(() => 
        api.put(`/contribute/study-draft/${study.identifier}/_publish`)
      );
    }
    
    async function deleteDraft(study: Study) {
      if (!authStore.isAuthenticated) return Promise.reject('Not authenticated');
      return authStore.updateToken().then(() => 
        api.delete(`/contribute/study-draft/${study.identifier}`)
      );
    }

    async function deleteFile(file: FileNode) {
      return api.delete(`/files/${file.path}`);
    }

    function downloadFile(file: FileNode) {
      window.open(`${baseUrl}/files/${file.path}?d=true`);
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
      updateDataset,
      deleteDataset,
      downloadFile,
      fetchAltitude,
      fetchClimateZone,
      readExcel,
      saveOrUpdateDraft,
      publishDraft,
      deleteDraft,
      uploadTmpFiles,
      getDrafts,
    };
  },
  { persist: true },
);
