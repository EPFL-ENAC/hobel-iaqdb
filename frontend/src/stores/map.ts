import { defineStore } from 'pinia';
import { BuildingsLayerManager } from 'src/layers/buildings';
import { ClimateZonesLayerManager } from 'src/layers/climate_zones';
import { Map } from 'maplibre-gl';
import { FilterParams } from 'src/stores/filters';

export type LayerSelection = {
  id: string;
  visible: boolean;
};

export const useMapStore = defineStore('map', () => {
  const map = ref<Map>();
  const filtersApplied = ref<number>(0);

  const layerManagers = [
    new BuildingsLayerManager(),
    new ClimateZonesLayerManager(),
  ];

  const layerSelections: LayerSelection[] = layerManagers.map((lm) => ({
    id: lm.getId(),
    visible: lm.isDefaultVisible(),
  }));

  /**
   * Find a layer selection state by its identifier.
   * @param id the layer selection state
   * @returns
   */
  function findLayer(id: string) {
    return layerSelections.find((l) => l.id === id);
  }

  /**
   * Toggle the visibility of a layer.
   * @param id the layer identifier
   */
  function applyLayerVisibility(id: string) {
    if (!map.value) return;
    const manager = getLayerManager(id);
    const layer = findLayer(id);
    if (manager && layer) {
      manager.setVisible(map.value, layer.visible);
    }
  }

  /**
   * Apply the data filters to the layers.
   * @param filters the data filters parameters
   */
  function applyFilters(filters: FilterParams) {
    if (!map.value) return;
    layerSelections.map((layer) => {
      if (map.value && layer.visible) {
        const manager = getLayerManager(layer.id);
        if (manager) {
          manager.filter(map.value, filters);
        }
      }
    });
    filtersApplied.value++;
  }

  /**
   * Register the current map and initialize the layers for that map.
   * @param mapInstance the map instance
   * @returns
   */
  async function initLayers(mapInstance: Map) {
    map.value = mapInstance;
    return Promise.all(
      layerSelections.map((layer) => {
        const manager = getLayerManager(layer.id);
        if (!manager) return Promise.resolve();
        return manager
          .append(mapInstance)
          .then(() => applyLayerVisibility(layer.id));
      }),
    );
  }

  /**
   * Get the layer manager by its identifier.
   * @param id the layer identifier
   * @returns
   */
  function getLayerManager(id: string) {
    return layerManagers.find((lm) => lm.getId() === id);
  }

  return {
    map,
    layerSelections,
    filtersApplied,
    applyFilters,
    applyLayerVisibility,
    initLayers,
    getLayerManager,
  };
});
