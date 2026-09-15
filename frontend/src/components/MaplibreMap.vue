<template>
  <div>
    <div
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90"
    >
      <q-spinner-dots color="primary" size="100px" />
    </div>
    <div id="maplibre-map" :style="`height: ${height}; width: ${width};`" />
  </div>
</template>

<script setup lang="ts">
import 'maplibre-gl/dist/maplibre-gl.css';
import '@maplibre/maplibre-gl-geocoder/dist/maplibre-gl-geocoder.css';
import * as maplibregl from 'maplibre-gl';
import MaplibreGeocoder from '@maplibre/maplibre-gl-geocoder';
import {
  AttributionControl,
  FullscreenControl,
  GeolocateControl,
  Map,
  type MapMouseEvent,
  NavigationControl,
  ScaleControl,
  setWorkerUrl,
  type StyleSpecification,
} from 'maplibre-gl';
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import { DivControl } from '@/utils/control';
import { geocoderApi } from '@/utils/geocoder';

interface Props {
  styleSpec?: string | StyleSpecification | undefined;
  center?: [number, number];
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  position?: boolean | string | undefined;
  geocoder?: boolean | string | undefined;
  attribution?: string;
  height?: string;
  width?: string;
  navigation?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  styleSpec: '/style.json',
  center: () => [6.5667, 46.5197], // Default to EPFL location
  zoom: 12,
  minZoom: 0,
  maxZoom: 22,
  position: false,
  geocoder: false,
  height: '100%',
  width: '100%',
});

const emit = defineEmits(['map:loaded', 'map:click']);

// maplibre-gl v6 ships its worker as a separate ESM file; under a bundler the
// URL cannot be inferred from import.meta.url, so it must be set explicitly.
// https://maplibre.org/maplibre-gl-js/docs/#installation
setWorkerUrl(maplibreWorkerUrl);

const { locale } = useI18n({ useScope: 'global' });
const DEFAULT_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, <a href="https://www.epfl.ch/" target="_blank">EPFL</a>';

const loading = ref(true);

let map: Map | undefined = undefined;

onMounted(() => {
  map = new Map({
    container: 'maplibre-map',
    style: props.styleSpec || '/style.json',
    center: props.center,
    zoom: props.zoom,
    minZoom: props.minZoom,
    maxZoom: props.maxZoom,
    attributionControl: false,
  });

  map.addControl(new NavigationControl());
  map.addControl(new GeolocateControl({}));
  map.addControl(new ScaleControl());
  map.addControl(new FullscreenControl());

  map.addControl(
    new AttributionControl({
      compact: true,
      customAttribution: props.attribution || DEFAULT_ATTRIBUTION,
    }),
  );

  if (props.geocoder === true || props.geocoder === 'true') {
    map.addControl(
      new MaplibreGeocoder(geocoderApi, {
        maplibregl,
        showResultsWhileTyping: true,
        language: locale.value,
      }),
      'top-left',
    );
  }

  map.on('click', (event: MapMouseEvent) => {
    emit('map:click', event, map);
  });

  if (props.position === true || props.position === 'true') {
    const positionControl = new DivControl({ id: 'map-position' });
    map.addControl(positionControl, 'bottom-left');
    map.on('mousemove', function (event: MapMouseEvent) {
      if (positionControl.container) {
        positionControl.container.innerHTML = `Lat/Lon: (${event.lngLat.lat.toFixed(4)}; ${event.lngLat.lng.toFixed(4)})`;
      }
    });
    map.on('mouseout', function () {
      if (positionControl.container) {
        positionControl.container.innerHTML = '';
      }
    });
  }

  void map.once('load', () => {
    emit('map:loaded', map);
    loading.value = false;
  });
});
</script>
