import { Map, Popup, GeoJSONSource } from 'maplibre-gl';
import {
  Feature,
  FeatureCollection,
  GeoJSON,
  GeoJsonProperties,
  Geometry,
  Point,
} from 'geojson';
import { LayerManager } from 'src/layers/models';
import { FilterParams } from 'src/stores/filters';
import { baseUrl } from 'src/boot/api';
import { truncateString } from 'src/utils/strings';
import { t } from 'src/boot/i18n';

const GEOJSON_URL = `${baseUrl}/map/buildings`;


export class BuildingsLayerManager extends LayerManager<FilterParams> {
  buildingsData: FeatureCollection | null = null;
  filteredData: FeatureCollection | null = null;
  
  /**
   * Creates an instance of BuildingsLayerManager.
   * @param onStudySelected Callback function to handle study selection.
   */
  constructor(private onStudySelected: (id: string) => void) {
    super();
    this.buildingsData = null;
    this.filteredData = null;
  }

  getId(): string {
    return 'buildings';
  }

  isDefaultVisible(): boolean {
    return true;
  }

  jitterCoordinates(lng: number, lat: number, index: number, total: number, radius = 0.0001): [number, number] {
    const angle = (2 * Math.PI / total) * index;
    const dx = radius * Math.cos(angle);
    const dy = radius * Math.sin(angle);
    return [lng + dx, lat + dy];
  }

  async append(map: Map): Promise<void> {
    const response = await fetch(GEOJSON_URL);
    const geoJson = (await response.json()) as FeatureCollection;
    // Jitter coordinates to avoid overlapping of points from different studies
    const studyJitteredCoordinates: { [key: string]: [number, number] }  = {};
    geoJson.features = geoJson.features.map((feature, index) => {
      if (feature.geometry.type === 'Point') {
        const [lng, lat] = (feature.geometry as Point).coordinates;
        const studyId = feature.properties ? feature.properties['study_id'] || '' : '';
        const key = `${studyId}-${lng}-${lat}`;
        let jitteredLng, jitteredLat;
        if (!studyJitteredCoordinates[key]) {
          [jitteredLng, jitteredLat] = this.jitterCoordinates(
            lng,
            lat,
            index,
            geoJson.features.length,
          );
          studyJitteredCoordinates[key] = [jitteredLng, jitteredLat];
        } else {
          [jitteredLng, jitteredLat] = studyJitteredCoordinates[key];
        }
        return {
          ...feature,
          geometry: {
            ...feature.geometry,
            coordinates: [jitteredLng, jitteredLat],
          },
        };
      }
      return feature;
    });
    this.buildingsData = geoJson;

    map.addSource('buildings', {
      type: 'geojson',
      // Point to GeoJSON data. This example visualizes all M1.0+ buildings
      // from 12/22/15 to 1/21/16 as logged by USGS' Earthquake hazards program.
      data: this.buildingsData,
      cluster: true,
      clusterMaxZoom: 14, // Max zoom to cluster points on
      clusterRadius: 50, // Radius of each cluster when clustering points (defaults to 50)
    });

    map.addLayer({
      id: 'buildings-clusters',
      type: 'circle',
      source: 'buildings',
      filter: ['has', 'point_count'],
      paint: {
        // Use step expressions (https://maplibre.org/maplibre-style-spec/#expressions-step)
        // with three steps to implement three types of circles:
        //   * Blue, 20px circles when point count is less than 10
        //   * Yellow, 30px circles when point count is between 10 and 20
        //   * Pink, 40px circles when point count is greater than or equal to 10
        'circle-color': [
          'step',
          ['get', 'point_count'],
          '#51bbd6',
          10,
          '#f1f075',
          20,
          '#f28cb1',
        ],
        'circle-radius': ['step', ['get', 'point_count'], 20, 10, 30, 20, 40],
      },
    });

    map.addLayer({
      id: 'buildings-cluster-count',
      type: 'symbol',
      source: 'buildings',
      filter: ['has', 'point_count'],
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
        'circle-stroke-width': 1,
        'circle-stroke-color': '#fff',
      },
    });

    // inspect a cluster on click
    map.on('click', 'buildings-clusters', async (e) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: ['buildings-clusters'],
      });
      const clusterId = features[0].properties.cluster_id;
      const zoom = await (
        map.getSource('buildings') as GeoJSONSource
      ).getClusterExpansionZoom(clusterId);
      map.easeTo({
        center: (features[0].geometry as Point).coordinates as [number, number],
        zoom,
      });
    });

    // When a click event occurs on a feature in
    // the unclustered-point layer, open a popup at
    // the location of the feature, with
    // description HTML from its properties.
    map.on('click', 'buildings-unclustered-point', (e) => {
      if (!e.features) return;
      const feature = e.features[0];
      if (!feature) return;

      // Ensure that if the map is zoomed out such that
      // multiple copies of the feature are visible, the
      // popup appears over the copy being pointed to.
      const coordinates = (feature.geometry as Point).coordinates.slice() as [
        number,
        number,
      ];
      while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
      }

      // for each feature, group by study_id and create a table
      // with the properties of the feature
      // and a link to the study
      const studyFeatures = {} as Record<string, Feature[]>;
      e.features.forEach((feat) => {
        const studyId = feat.properties['study_id'];
        if (!studyFeatures[studyId]) {
          studyFeatures[studyId] = [];
        }
        studyFeatures[studyId].push(feat);
      });
      const studyNames = {} as Record<string, string>;
      e.features.forEach((feat) => {
        studyNames[feat.properties['study_id']] = feat.properties['study_name'];
      });
      
      const city = feature.properties['city'] ? `${feature.properties['city']}, ${feature.properties['country']}` : '';
      const studyElements = Object.keys(studyFeatures)
            .map((key) => {
              const buildings_count = studyFeatures[key].length;
              const spaces_count = studyFeatures[key].reduce(
                (acc, feat) => acc + (feat.properties ? feat.properties['spaces_count'] : 0),
                0,
              );
              const divContainer = document.createElement('div');
              divContainer.className = 'q-ma-sm';
              
              const studyContainer = document.createElement('div');
              const aContainer = document.createElement('a');
              aContainer.href = 'javascript:void(0)';
              aContainer.classList.add('epfl');
              aContainer.onclick = () => this.onStudySelected(key);
              aContainer.innerText = truncateString(studyNames[key], 30) + ' ';
              studyContainer.appendChild(aContainer);
              divContainer.appendChild(studyContainer);

              const buildingsContainer = document.createElement('div');
              buildingsContainer.innerHTML = `
                <span class="text-bold">${buildings_count}</span> ${t('buildings_count', buildings_count)}`;
              divContainer.appendChild(buildingsContainer);

              const spacesContainer = document.createElement('div');
              spacesContainer.innerHTML = `
                <span class="text-bold">${spaces_count}</span> ${t('spaces_count', spaces_count)}`;
              divContainer.appendChild(spacesContainer);
              
              return divContainer;
            });
      const contentContainer = document.createElement('div');
      const cityContainer = document.createElement('div');
      cityContainer.classList.add('q-pa-sm', 'text-bold');
      cityContainer.style.minWidth = '100px';
      cityContainer.innerText = city;
      contentContainer.appendChild(cityContainer);
      studyElements.forEach((el, index) => {
        contentContainer.appendChild(el);
        if (index < studyElements.length - 1) {
          const separator = document.createElement('hr');
          separator.classList.add('q-my-sm');
          contentContainer.appendChild(separator);
        }
      });

      new Popup().setLngLat(coordinates).setDOMContent(contentContainer).addTo(map);
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

  filter(map: Map, filter: FilterParams): void {
    if (!this.buildingsData) return;

    const filteredFeatures = this.buildingsData.features.filter(
      (feature: Feature<Geometry, GeoJsonProperties>) => {
        let filtered = true;
        if (filter.construction_years) {
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
    } as GeoJSON;
    (map.getSource('buildings') as GeoJSONSource).setData(this.filteredData);
  }
}
