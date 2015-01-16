"""
    See http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
"""

from math import atan, cos, degrees, log, pi, pow, radians, sinh, tan

TILE_BASE_URL = 'http://kvr.fra.nexttuesday.de/tiles/{zoom}/{xtile}/{ytile}.png'
TILE_SIZE = 256


def tiles_count(z):
    return pow(2, z)


def sec(x):
    return 1 / cos(x)


def get_tile_by_lat_lng(lat, lon, z):
    n = tiles_count(z)
    x = (lon + 180) / 360
    y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return int(n*x), int(n*y)


def get_lat_bounds(y, z):
    n = tiles_count(z)
    unit = 1 / n
    rel_y1 = y * unit
    rel_y2 = rel_y1 + unit
    lat1 = mercator_to_lat(pi * (1 - 2 * rel_y1))
    lat2 = mercator_to_lat(pi * (1 - 2 * rel_y2))
    return lat1, lat2


def get_lng_bounds(x, z):
    n = tiles_count(z)
    unit = 360.0 / n
    lng1 = -180 + x * unit
    lng2 = lng1 + unit
    return lng1, lng2


def get_tile_bounds(x, y, z):
    lat1, lat2 = get_lat_bounds(y, z)
    lng1, lng2 = get_lng_bounds(x, z)
    return lat2, lng1, lat1, lng2


def mercator_to_lat(mercator_y):
    return degrees(atan(sinh(mercator_y)))
