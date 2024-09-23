import { Map } from 'maplibre-gl';
import { LayerManager } from 'src/layers/models';
import { FilterParams } from 'src/stores/filters';

const VERSION = '2024-07-01T14:54';
const CDN_URL = `https://enacit4r-cdn.epfl.ch/iaq/${VERSION}/koppen_geiger/1991_2020`;
//const CDN_URL = 'https://enacit4r-cdn.epfl.ch/iaqdb/tiles/koppen_geiger/1991_2020';

export class ClimateZonesLayerManager extends LayerManager<FilterParams> {
  getId(): string {
    return 'climate-zones';
  }

  isDefaultVisible(): boolean {
    return false;
  }

  async append(map: Map): Promise<void> {
    // map.addSource('climate-zones', {
    //   type: 'vector',
    //   url: 'http://localhost:3000/koppen_geiger_0p1'
    // });

    // map.addLayer({
    //   id: 'climate-zones',
    //   type: 'fill',
    //   source: 'climate-zones',
    //   'source-layer': 'koppen_geiger_0p1',
    //   minzoom: 0,
    //   maxzoom: 22,
    //   paint: {
    //     'fill-color': [
    //         'interpolate',
    //         ['linear'],
    //         ['get', 'id'],
    //         1, '#0000fe',
    //         2, '#0077fe',
    //         3, '#46aafa',
    //         4, '#ff0000',
    //         5, '#ff9696',
    //         6, '#f4a400',
    //         7, '#fedb63',
    //         8, '#ffff00',
    //         9, '#c8c800',
    //         10, '#959500',
    //         11, '#96ff96',
    //         12, '#63c763',
    //         13, '#319531',
    //         14, '#c8ff50',
    //         15, '#63fe31',
    //         16, '#32c800',
    //         17, '#fe00fe',
    //         18, '#c800c8',
    //         19, '#963196',
    //         20, '#966496',
    //         21, '#aaafff',
    //         22, '#5977db',
    //         23, '#4b50b4',
    //         24, '#320087',
    //         25, '#00ffff',
    //         26, '#37c8ff',
    //         27, '#007d7d',
    //         28, '#00455e',
    //         29, '#b3b3b3',
    //         30, '#656565',
    //     ],
    //     'fill-outline-color': '#987db7',
    //     'fill-opacity': 0.7
    //   },
    //   layout: {
    //     visibility: 'none'
    //   }
    // });

    map.addSource('climate-zones', {
      type: 'raster',
      tiles: [`${CDN_URL}/{z}/{x}/{y}.png`],
      tileSize: 256,
      minzoom: 0,
      maxzoom: 7,
    });

    map.addLayer({
      id: 'climate-zones',
      type: 'raster',
      source: 'climate-zones',
      minzoom: 0,
      maxzoom: 22,
      paint: {
        'raster-opacity': 0.7,
      },
      layout: {
        visibility: 'none',
      },
    });
  }

  setVisible(map: Map, visible: boolean): void {
    const visibility = visible ? 'visible' : 'none';
    map.setLayoutProperty('climate-zones', 'visibility', visibility);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  filter(map: Map, filter: FilterParams): void {
    return;
  }
}
