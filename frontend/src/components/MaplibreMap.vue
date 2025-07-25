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
import 'maplibregl-theme-switcher/styles.css';
import maplibregl from 'maplibre-gl';
import MaplibreGeocoder from '@maplibre/maplibre-gl-geocoder';
import {
  ThemeSwitcherControl,
  type ThemeDefinition,
} from 'maplibregl-theme-switcher';
import {
  AttributionControl,
  FullscreenControl,
  GeolocateControl,
  Map,
  type MapMouseEvent,
  NavigationControl,
  ScaleControl,
  type StyleSpecification,
} from 'maplibre-gl';
import { DivControl } from 'src/utils/control';
import { geocoderApi } from 'src/utils/geocoder';
import type { Settings } from 'src/stores/settings';

interface Props {
  styleSpec?: string | StyleSpecification | undefined;
  center?: [number, number];
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  themes?: ThemeDefinition[];
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

const settingsStore = useSettingsStore();

const { locale } = useI18n({ useScope: 'global' });
const DEFAULT_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, <a href="https://www.epfl.ch/" target="_blank">EPFL</a>';
// to be adapted to the style.json
const DEFAULT_THEME = 'light';
const THEMES: ThemeDefinition[] = [
  { id: 'classic', label: 'Classic' },
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
];

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

  const settings = settingsStore.settings;
  map.addControl(
    new ThemeSwitcherControl(THEMES, {
      defaultStyle: settings ? settings.theme || DEFAULT_THEME : DEFAULT_THEME,
      eventListeners: {
        onChange(event: MouseEvent, style) {
          // persist the last theme choice
          settingsStore.saveSettings({ theme: style } as Settings);
          return false;
        },
      },
    }),
  );

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
    THEMES.map((th) => th.id).forEach((id) => {
      map?.setLayoutProperty(
        id,
        'visibility',
        id === settings?.theme ? 'visible' : 'none',
      );
    });
    emit('map:loaded', map);
    loading.value = false;
  });
});
</script>
