import gevent.monkey; gevent.monkey.patch_thread()

import argparse
from cStringIO import StringIO
from itertools import product
import math
import sys

import gevent
from PIL import Image
import requests

from tile_utils import get_tile_by_lat_lng, get_tile_bounds, TILE_BASE_URL, TILE_SIZE

CIRCLE_IMAGE_NAME = 'dark-red-circle.png'
CIRCLE_IMAGE = Image.open(CIRCLE_IMAGE_NAME)


def download_tile(tile_x, tile_y, zoom):
    """Downloads the tile with given (x, y) coordinates and a zoom level."""
    request_string = TILE_BASE_URL.format(zoom=zoom, xtile=tile_x, ytile=tile_y)
    response = requests.get(request_string)
    if response.status_code != 200:
        raise Exception('Cannot load tile {} ({})'.format(request_string, response.status_code))

    return Image.open(StringIO(response.content)).convert('RGBA')


def get_circle_position(lat, lng, bounds):
    """Returns the position of a target point inside a center tile."""
    s, w, n, e = bounds

    x_pos_rel = (lng - w) / (e - w)
    y_pos_rel = (n - lat) / (n - s)

    return int(round(x_pos_rel * TILE_SIZE)), int(round(y_pos_rel * TILE_SIZE)), x_pos_rel <= 0.5, y_pos_rel <= 0.5


def get_center_tile_position(left_bound, top_bound, tiles_per_row):
    """Returns center tile position.
    :param left_bound: True, if the target point is closer to the left edge of a center tile
    :param top_bound: True, if the target point is closer to the top edge of a center tile
    """
    tile_xind = tile_yind = tiles_per_row / 2
    if tiles_per_row % 2 == 0:
        if not left_bound:
            tile_xind -= 1
        if not top_bound:
            tile_yind -= 1

    return tile_xind, tile_yind


def get_tiles(zoom, lat, lng, ntiles):
    """Returns an image, containing `ntiles` tiles with a point `(lat, lng)` as a center.
    Zoom level is set to `zoom`.
    """

    center_x, center_y = get_tile_by_lat_lng(lat, lng, zoom)
    center_bounds = get_tile_bounds(center_x, center_y, zoom)
    circle_x, circle_y, is_closer_to_left, is_closer_to_top = get_circle_position(lat, lng, center_bounds)

    tiles_per_row = int(math.sqrt(ntiles))
    tile_xind, tile_yind = get_center_tile_position(is_closer_to_left, is_closer_to_top, tiles_per_row)

    png_image = Image.new('RGBA', (tiles_per_row * TILE_SIZE, tiles_per_row * TILE_SIZE))

    def insert_center_tile():
        center_tile = download_tile(center_x, center_y, zoom)
        center_tile.paste(CIRCLE_IMAGE, (circle_x, circle_y), CIRCLE_IMAGE)
        png_image.paste(center_tile, (tile_xind * TILE_SIZE, tile_yind * TILE_SIZE))

    def insert_tile(tile_x, tile_y):
        tile_image = download_tile(center_x - tile_xind + tile_x, center_y - tile_yind + tile_y, zoom)
        png_image.paste(tile_image, (tile_x * TILE_SIZE, tile_y * TILE_SIZE))

    downloads = [gevent.spawn(insert_center_tile)]

    tiles = [(x, y) for x, y in product(range(tiles_per_row), range(tiles_per_row))]
    for tile_x, tile_y in tiles:
        if tile_x == tile_xind and tile_y == tile_yind:
            continue

        downloads.append(gevent.spawn(insert_tile, tile_x, tile_y))

    gevent.joinall(downloads)
    png_image.save(sys.stdout, 'PNG')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gets a map region for a specified location and zoom level')
    parser.add_argument('zoom', metavar='Z', type=int, nargs='?', help='zoom level')
    parser.add_argument('latitude', metavar='LAT', type=float, nargs='?', help='latitude')
    parser.add_argument('longitude', metavar='LNG', type=float, nargs='?', help='longitude')
    parser.add_argument('--ntiles', dest='ntiles', type=int, nargs='?', choices=[1, 4, 9, 16], default=1,
                        help='number of tiles in context')

    args = parser.parse_args()

    try:
        get_tiles(args.zoom, args.latitude, args.longitude, args.ntiles)
    except Exception as e:
        sys.stderr.write('An exception occured!\n{}'.format(e))
