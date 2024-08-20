import pkg_resources
import requests
import rasterio
from pyproj import Transformer
from api.config import config
from api.models.geo import ClimateZone, Elevation

CLIMATE_ZONES = [
    "Af",
    "Am",
    "Aw",
    "BWh",
    "BWk",
    "BSh",
    "BSk",
    "Csa",
    "Csb",
    "Csc",
    "Cwa",
    "Cwb",
    "Cwc",
    "Cfa",
    "Cfb",
    "Cfc",
    "Dsa",
    "Dsb",
    "Dsc",
    "Dsd",
    "Dwa",
    "Dwb",
    "Dwc",
    "Dwd",
    "Dfa",
    "Dfb",
    "Dfc",
    "Dfd",
    "ET",
    "EF",
]


class GeoService:

    def readClimateZone(self, lon: float = 0, lat: float = 0, precise: bool = True) -> ClimateZone:
        data_file_path = pkg_resources.resource_filename(
            "api", "data/koppen_geiger_1991_2020_0p00833333.tif" if precise else "data/koppen_geiger_1991_2020_0p1.tif")

        value = -1

        # Open the GeoTIFF file
        with rasterio.open(data_file_path) as dataset:
            # Get the coordinate reference system (CRS) of the raster
            crs = dataset.crs

            transformer = Transformer.from_crs(crs, "EPSG:4326")

            # Transform the geolocation to the raster"s CRS
            x, y = transformer.transform(lon, lat)

            # Get the row and column indices of the raster cell containing the geolocation
            row, col = dataset.index(x, y)

            # Read the value at the specified row and column
            value = dataset.read(1)[row, col]

        name = "NA"
        if value > 0 and value <= 30:
            name = CLIMATE_ZONES[value - 1]

        return ClimateZone(id=value, name=name, lon=lon, lat=lat)

    def queryElevation(self, lon: float = 0, lat: float = 0) -> Elevation:
        resp = requests.get(f"{config.ELEVATION_URL}/api/v1/lookup",
                            params={"locations": f"{lat},{lon}"})
        content = resp.json()
        print(content)
        place = content["results"][0]
        return Elevation(altitude=place["elevation"], lon=lon, lat=lat)
