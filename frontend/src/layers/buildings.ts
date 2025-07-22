import { type Map, Popup, type GeoJSONSource } from 'maplibre-gl';
import type {
  Feature,
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
  // Point,
} from 'geojson';
import Spiderfy, { type SpiderfyOptions } from '@nazka/map-gl-js-spiderfy';
import { LayerManager } from 'src/layers/models';
import type { FilterParams } from 'src/stores/filters';
import { baseUrl } from 'src/boot/api';
import { truncateString } from 'src/utils/strings';
import { t } from 'src/boot/i18n';
import { buildingTypeOptions, outdoorEnvOptions, yesNoOptions, mechanicalVentilationTypeOptions, ageGroupOptions, socioeconomicStatusOptions } from 'src/utils/options';

const GEOJSON_URL = `${baseUrl}/map/buildings`;

interface MouseEventWithCoordinates extends MouseEvent {
  lngLat?: {
    lng: number;
    lat: number;
  };
}

export class BuildingsLayerManager extends LayerManager<FilterParams> {
  buildingsData: FeatureCollection | null = null;
  filteredData: FeatureCollection | null = null;
  spiderfy: Spiderfy | null = null;

  /**
   * Creates an instance of BuildingsLayerManager.
   * @param onStudySelected Callback function to handle study selection.
   */
  constructor(private onStudySelected: (id: string) => void) {
    super();
    this.buildingsData = null;
    this.filteredData = null;
    this.spiderfy = null;
  }

  getId(): string {
    return 'buildings';
  }

  isDefaultVisible(): boolean {
    return true;
  }

  async append(map: Map): Promise<void> {
    const response = await fetch(GEOJSON_URL);
    const geoJson = (await response.json()) as FeatureCollection;
    this.buildingsData = geoJson;

    const { data: image } = await map.loadImage(
      '/circle.png',
    );
    map.addImage('marker-icon', image,  { sdf: true });

    map.addSource('buildings', {
      type: 'geojson',
      data: this.buildingsData,
      cluster: true,
    });

     map.addLayer({
      id: 'buildings-clusters',
      type: 'symbol',
      source: 'buildings',
      filter: ['has', 'point_count'],
      layout: {
        'icon-image': 'marker-icon',
        'icon-allow-overlap': true,
        'icon-size': 2, //['case', ['has', 'point_count'], 2, 1],
      },
      paint: {
        'icon-color': '#f2c037',
      }
    });

    map.addLayer({
      id: 'buildings-cluster-count',
      type: 'symbol',
      source: 'buildings',
      layout: {
        'text-field': '{point_count_abbreviated}',
        'text-font': ['Roboto Regular'],
        'text-size': 12,
      },
    });

    map.addLayer({
      id: 'buildings-unclustered-point',
      type: 'circle',
      source: 'buildings',
      filter: ['!', ['has', 'point_count']],
      paint: {
        // get color from color property
        'circle-color': ['get', 'color'],
        'circle-radius': 10,
      },
    });

    let popup: Popup | null = null;
    this.spiderfy = new Spiderfy(map, {
      onLeafHover: (feature: Feature, event: MouseEventWithCoordinates) => {
        if (!feature || !feature.geometry || feature.geometry.type !== 'Point') return;
        if (popup) {
          popup.remove();
          popup = null;
        }
        const popupContent = this.makeBuildingElement(feature);
        // Show the popup with the content
        const coordinates = (event.lngLat ? [event.lngLat.lng, event.lngLat.lat] : feature.geometry.coordinates.slice()) as [number, number];
        popup = new Popup().setLngLat(coordinates).setDOMContent(popupContent).addTo(map);
      },
      minZoomLevel: 8,
      zoomIncrement: 2,
      circleSpiralSwitchover: 10,
      animationSpeed: 100,
      spiderLeavesLayout: {
        'icon-image': 'marker-icon',
        'icon-allow-overlap': true,
        'icon-size': 1,
      },
      spiderLeavesPaint: {
        'icon-color': ['get', 'color'],
      },
    } as SpiderfyOptions);
    this.spiderfy?.applyTo('buildings-clusters');

    // When a click event occurs on a feature in
    // the unclustered-point layer, open a popup at
    // the location of the feature, with
    // description HTML from its properties.
    map.on('mouseenter', 'buildings-unclustered-point', (e) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: ['buildings-unclustered-point'],
      });
      if (!features.length) return;
      if (popup) {
        popup.remove();
        popup = null;
      }

      const feature = features[0];
      if (!feature || !feature.geometry || feature.geometry.type !== 'Point') return;
      const popupContent = this.makeBuildingElement(feature);
      const coordinates = feature.geometry.coordinates.slice() as [number, number];
      popup = new Popup()
        .setLngLat(coordinates)
        .setDOMContent(popupContent)
        .addTo(map);
    });

    map.on('mouseenter', 'buildings-clusters', () => {
      map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'buildings-clusters', () => {
      map.getCanvas().style.cursor = '';
    });
  }

  setVisible(map: Map, visible: boolean): void {
    const visibility = visible ? 'visible' : 'none';
    [
      'buildings-clusters',
      'buildings-cluster-count',
      'buildings-unclustered-point',
    ].forEach((id) => {
      map.setLayoutProperty(id, 'visibility', visibility);
    });
  }

  makeBuildingElement = (feature: Feature): HTMLElement => {
    if (!feature.properties) return document.createElement('div');
    const city = feature.properties['city'] ? `${feature.properties['city']}, ${feature.properties['country']}` : '';

    const divContainer = document.createElement('div');

    const studyContainer = document.createElement('div');
    const aContainer = document.createElement('a');
    aContainer.href = 'javascript:void(0)';
    aContainer.classList.add('epfl');
    aContainer.onclick = () => {
      if (!feature.properties || !feature.properties['study_id']) return;
      this.onStudySelected(feature.properties['study_id']);
    };
    aContainer.innerText = truncateString(feature.properties['study_name'] || '', 30) + ' ';
    studyContainer.appendChild(aContainer);
    divContainer.appendChild(studyContainer);

    const contentContainer = document.createElement('div');

    const cityContainer = document.createElement('div');
    cityContainer.classList.add('q-mb-sm');
    cityContainer.innerText = city;
    contentContainer.appendChild(cityContainer);

    const propertiesContainer = document.createElement('table');
    propertiesContainer.classList.add('grid-dl');
    ['building_type', 'outdoor_env', 'age_group', 'socioeconomic_status', 'mechanical_ventilation', 'mechanical_ventilation_types', 'spaces_count'].forEach((property) => {
      if (feature.properties && feature.properties[property]) {
        const div = document.createElement('tr');
        const dt = document.createElement('td');
        dt.classList.add('text-bold');
        dt.innerText = t(`feature.${property}`);
        const dd = document.createElement('td');
        dd.style.minWidth = '100px';
        let value = feature.properties[property];
        if (property === 'building_type') {
          value = buildingTypeOptions.find((option) => option.value === value)?.label || value;
        } else if (property === 'outdoor_env') {
          value = outdoorEnvOptions.find((option) => option.value === value)?.label || value;
        } else if (property === 'age_group') {
          value = ageGroupOptions.find((option) => option.value === value)?.label || value;
        } else if (property === 'socioeconomic_status') {
          value = socioeconomicStatusOptions.find((option) => option.value === value)?.label || value;
        } else if (property === 'mechanical_ventilation') {
          value = yesNoOptions.find((option) => option.value === value)?.label || value;
        } else if (property === 'mechanical_ventilation_types') {
          value = value.split('|').map((item: string) => mechanicalVentilationTypeOptions.find((option) => option.value === item)?.label || item).join(', ');
        } else if (property === 'spaces_count') {
          value = feature.properties['spaces_count'] || 0;
        }
        dd.innerText = value;
        div.appendChild(dt);
        div.appendChild(dd);
        propertiesContainer.appendChild(div);
      }
    });
    contentContainer.appendChild(propertiesContainer);

    divContainer.appendChild(contentContainer);

    return divContainer;
  }

  filter(map: Map, filter: FilterParams): void {
    if (!this.buildingsData) return;

    const filteredFeatures = this.buildingsData.features.filter(
      (feature: Feature<Geometry, GeoJsonProperties>) => {
        let filtered = true;
        if (filtered && filter.construction_years) {
          filtered =
            feature.properties?.construction_year >= filter.construction_years[0] &&
            feature.properties?.construction_year <= filter.construction_years[1];
        }
        if (filtered && filter.altitudes) {
          filtered =
            feature.properties?.altitude >= filter.altitudes[0] &&
            feature.properties?.altitude <= filter.altitudes[1];
        }
        if (filtered && filter.countries && filter.countries.length) {
          filtered = filter.countries.includes(
            feature.properties?.country,
          );
        }
        if (filtered && filter.cities && filter.cities.length) {
          filtered = filter.cities.includes(
            `${feature.properties?.city}, ${feature.properties?.country}`,
          );
        }
        if (filtered && filter.climate_zones && filter.climate_zones.length) {
          filtered = filter.climate_zones.includes(
            feature.properties?.climate_zone,
          );
        }
        if (filtered && filter.study_ids && filter.study_ids.length) {
          filtered = filter.study_ids.includes(
            feature.properties?.study_id,
          );
        }
        if (filtered && filter.building_types && filter.building_types.length) {
          filtered = filter.building_types.includes(
            feature.properties?.building_type,
          );
        }
        if (filtered && filter.age_groups && filter.age_groups.length) {
          filtered = filter.age_groups.includes(
            feature.properties?.age_group,
          );
        }
        if (filtered && filter.socioeconomic_status && filter.socioeconomic_status.length) {
          filtered = filter.socioeconomic_status.includes(
            feature.properties?.socioeconomic_status,
          );
        }
        if (filtered && filter.outdoor_envs && filter.outdoor_envs.length) {
          filtered = filter.outdoor_envs.includes(
            feature.properties?.outdoor_env,
          );
        }
        if (filtered && filter.mechanical_ventilation) {
          filtered = filter.mechanical_ventilation === feature.properties?.mechanical_ventilation;
        }
        if (filtered && filter.mechanical_ventilation_types && filter.mechanical_ventilation_types.length) {
          filtered =
            filter.mechanical_ventilation_types.filter((vent) =>
              feature.properties?.mechanical_ventilation_types.includes(vent),
            ).length > 0;
        }
        if (
          filtered &&
          filter.study_ids &&
          filter.study_ids.length &&
          feature.properties?.study_id !== undefined
        ) {
          filtered = filter.study_ids.includes(
            feature.properties.study_id,
          );
        }
        return filtered;
      },
    );
    this.filteredData = {
      ...this.buildingsData,
      features: filteredFeatures,
    };
    map.getSource<GeoJSONSource>('buildings')?.setData(this.filteredData);
  }
}
