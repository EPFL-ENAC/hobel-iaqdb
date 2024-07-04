import pkg_resources
from fastapi import APIRouter, Query
from api.models.catalog import Building
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties, ClimateZone
import rasterio
from pyproj import Transformer

router = APIRouter()


@router.get("/buildings")
async def getBuildings() -> BuildingFeatures:
    buildings = await Building.find_all().to_list()

    features = []
    for building in buildings:
        geometry = Geometry(coordinates=building.location, type="Point")
        properties = BuildingProperties(identifier=building.identifier,
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude)
        feature = BuildingFeature(
            geometry=geometry, properties=properties, type="Feature")
        features.append(feature)
    return BuildingFeatures(features=features, type="FeatureCollection")


@router.get("/climate-zone")
async def getClimateZone(lon: float = Query(0), lat: float = Query(0)) -> ClimateZone:
    data_file_path = pkg_resources.resource_filename(
        'api', 'data/koppen_geiger_1991_2020_0p00833333.tif')

    value = -1

    # Open the GeoTIFF file
    with rasterio.open(data_file_path) as dataset:
        # Get the coordinate reference system (CRS) of the raster
        crs = dataset.crs

        transformer = Transformer.from_crs(crs, "EPSG:4326")

        # Transform the geolocation to the raster's CRS
        x, y = transformer.transform(lon, lat)

        # Get the row and column indices of the raster cell containing the geolocation
        row, col = dataset.index(x, y)
        print(row, col)

        # Read the value at the specified row and column
        value = dataset.read(1)[row, col]

    names = [
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

    name = "NA"
    if value > 0 and value <= 30:
        name = names[value - 1]

    return ClimateZone(id=value, name=name, lon=lon, lat=lat)
