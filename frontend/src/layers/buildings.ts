import { Map, Popup, GeoJSONSource } from 'maplibre-gl';
import { Feature, FeatureCollection, GeoJSON, GeoJsonProperties, Geometry, Point } from 'geojson';
import { LayerManager } from 'src/layers/models';
import { FilterParams } from 'src/stores/filters';
import { baseUrl } from 'src/boot/api';

const GEOJSON_URL = `${baseUrl}/map/buildings`;

export class BuildingsLayerManager extends LayerManager<FilterParams> {

  buildingsData: FeatureCollection | null = null;

  getId(): string {
    return 'buildings';
  }

  isDefaultVisible(): boolean {
    return true;
  }

  async append(map: Map): Promise<void> {
    const response = await fetch(GEOJSON_URL);
    this.buildingsData = await response.json() as FeatureCollection;

    map.addSource('buildings', {
      type: 'geojson',
      // Point to GeoJSON data. This example visualizes all M1.0+ buildings
      // from 12/22/15 to 1/21/16 as logged by USGS' Earthquake hazards program.
      data: this.buildingsData,
      cluster: true,
      clusterMaxZoom: 14, // Max zoom to cluster points on
      clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)
    });

    map.addLayer({
      id: 'buildings-clusters',
      type: 'circle',
      source: 'buildings',
      filter: ['has', 'point_count'],
      paint: {
        // Use step expressions (https://maplibre.org/maplibre-style-spec/#expressions-step)
        // with three steps to implement three types of circles:
        //   * Blue, 20px circles when point count is less than 5
        //   * Yellow, 30px circles when point count is between 5 and 10
        //   * Pink, 40px circles when point count is greater than or equal to 10
        'circle-color': [
          'step',
          ['get', 'point_count'],
          '#51bbd6',
          5,
          '#f1f075',
          10,
          '#f28cb1'
        ],
        'circle-radius': [
          'step',
          ['get', 'point_count'],
          20,
          5,
          30,
          10,
          40
        ]
      }
    });

    map.addLayer({
      id: 'buildings-cluster-count',
      type: 'symbol',
      source: 'buildings',
      filter: ['has', 'point_count'],
      layout: {
        'text-field': '{point_count_abbreviated}',
        'text-font': ['Roboto Regular'],
        'text-size': 12
      }
    });

    map.addLayer({
      id: 'buildings-unclustered-point',
      type: 'circle',
      source: 'buildings',
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': '#11b4da',
        'circle-radius': 5,
        'circle-stroke-width': 1,
        'circle-stroke-color': '#fff'
      }
    });

    // inspect a cluster on click
    map.on('click', 'buildings-clusters', async (e) => {
      const features = map.queryRenderedFeatures(e.point, {
          layers: ['buildings-clusters']
      });
      const clusterId = features[0].properties.cluster_id;
      const zoom = await (map.getSource('buildings') as GeoJSONSource).getClusterExpansionZoom(clusterId);
      map.easeTo({
        center: (features[0].geometry as Point).coordinates as [number, number],
        zoom
      });
    });

    // When a click event occurs on a feature in
    // the unclustered-point layer, open a popup at
    // the location of the feature, with
    // description HTML from its properties.
    map.on('click', 'buildings-unclustered-point', (e) => {
      const feature = e.features ? e.features[0] : null;
      if (!feature) return;
      

      // Ensure that if the map is zoomed out such that
      // multiple copies of the feature are visible, the
      // popup appears over the copy being pointed to.
      const coordinates = (feature.geometry as Point).coordinates.slice() as [number, number];
      while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
      }

      const rows = Object.keys(feature.properties)
        .filter((key) => key !== 'slug')
        .map((key) => {
          return `<tr><td>${key}</td><td>${feature.properties[key]}</td></tr>`
        }).join('');

      new Popup()
        .setLngLat(coordinates)
        .setHTML(
          `<table>${rows}</table>`
        )
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
    ['buildings-clusters', 'buildings-cluster-count', 'buildings-unclustered-point'].forEach(id => {
      map.setLayoutProperty(
        id,
        'visibility',
        visibility
      )
    });
  }

  filter(map: Map, filter: FilterParams): void {
    if (!this.buildingsData) return;

    const filteredFeatures = this.buildingsData.features
      .filter((feature: Feature<Geometry, GeoJsonProperties>) => {
        let filtered = feature.properties?.altitude >= filter.altitudes[0] && feature.properties?.altitude <= filter.altitudes[1];
        if (filtered&& filter.climateZones && filter.climateZones.length) {
          filtered = filter.climateZones.includes(feature.properties?.climate_zone);
        }
        return filtered;
      });
    const filteredData = {
      ...this.buildingsData,
      features: filteredFeatures
    } as GeoJSON;
    (map.getSource('buildings') as GeoJSONSource).setData(filteredData);
  }

}
