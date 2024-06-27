import { defineStore } from 'pinia';
import { api } from 'src/boot/api'


export const useCatalogStore = defineStore('catalog', () => {

  async function loadStudies() {
    return api.get('/catalog/studies').then((response) => response.data)
  }

  async function loadBuildings() {
    return api.get('/catalog/buildings').then((response) => response.data)
  }

  async function loadRooms() {
    return api.get('/catalog/rooms').then((response) => response.data)
  }

  return {
    loadStudies,
    loadBuildings,
    loadRooms
  }

});