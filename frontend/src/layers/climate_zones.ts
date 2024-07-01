import { Map } from 'maplibre-gl';
import { LayerManager } from 'src/layers/models';
import { FilterParams } from 'src/stores/filters';

const VERSION = '2024-07-01T14:54';
const CDN_URL = `https://enacit4r-cdn.epfl.ch/iaq/${VERSION}/koppen_geiger/1991_2020`;

export class ClimateZonesLayerManager extends LayerManager<FilterParams> {


  getId(): string {
    return 'climate-zones';
  }
  
  isDefaultVisible(): boolean {
    return false;
  }

  async append(map: Map): Promise<void> {
    
    map.addSource('climate-zones', {
      type: 'raster',
      tiles: [`${CDN_URL}/{z}/{x}/{y}.png`],
      tileSize: 256,
      minzoom: 0,
      maxzoom: 7
    });

    map.addLayer({
      id: 'climate-zones',
      type: 'raster',
      source: 'climate-zones',
      minzoom: 0,
      maxzoom: 22,
      paint: {
        'raster-opacity': 0.7
      },
      layout: {
        visibility: 'none'
      }
    });
  }

  setVisible(map: Map, visible: boolean): void {
    const visibility = visible ? 'visible' : 'none';
    map.setLayoutProperty(
      'climate-zones',
      'visibility',
      visibility
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  filter(map: Map, filter: FilterParams): void {
    return;
  }

}
