from collections import defaultdict
from io import BytesIO
import numpy as np
from os.path import isfile
import pickle
from sys import exit

from kivy.graphics.texture import Texture

from PIL import Image

import helper_functions


def obtain_file_name(file):
    return file.split('/')[-1:][0].split('.')[:-1][0]


def convert_im_to_bytes_io(im, png=''):
    with BytesIO() as output:
        # with Image.open(directory + png).transpose(Image.FLIP_TOP_BOTTOM) as img:
        img = im.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(output, "PNG")
        output.seek(0)
        output_read = output.read()
        return output_read


def convert_im_bytes_to_pixels(png_bytes):
    with BytesIO(png_bytes) as rawIO:
        with Image.open(rawIO) as byteImg:
            byteImg = byteImg.convert('RGBA')
            # size = byteImg.size
    return byteImg.tobytes()


def rgb_comparision(tile_data, initial_rgb_list, delta_threshold, index, oppos_index):
    # print('rgb comparision', tile_data)
    matching_list = {}
    # ---Compare RGB Values and Find Matching Tiles---
    for key, rgb_list in tile_data.items():
        if key == '1':
            continue
        # resultant = np.subtract(list(initial_rgb_list[index].pixels), list(rgb_list[oppos_index].pixels)) < delta_threshold
        resultant = abs(np.subtract(list(initial_rgb_list[index]), list(rgb_list[oppos_index]))) <= delta_threshold

        if False in resultant:
        # if count > max_false:
            # print('%s does not match' % key)
            pass
        else:
            # print('tile: %s is a matching tile' % key)
            matching_list[key] = 1
            # matching_tiles[initial_key][index].append(key)

    # ---Assign Default/Equal Probability From All Tiles---
    # TODO: Find a way to modify percentages based on compatibility of tiles
    keys = len(matching_list.keys())
    percentage = 0
    if keys != 0:
        percentage = round(1/keys, 2)

    for key in matching_list.keys():
        matching_list[key] = percentage

    return matching_list


def print_matching_tiles(matching_tiles):
    # print('matching_tiles')
    for key, val in matching_tiles.items():
        print('For tile: %s' % key)
        # print(
        #     'For tile: %s\n\t%s tiles match north,\n\t%s tiles match east\n\t%s tiles match south\n\t%s tiles match west' % (
        #     key, len(val[0]), len(val[1]), len(val[2]), len(val[3])))
        print('\t%s tiles match north' % len(val[0]), val[0])
        print('\t%s tiles match east' % len(val[1]), val[1])
        print('\t%s tiles match south' % len(val[2]), val[2])
        print('\t%s tiles match west' % len(val[3]), val[3])


def print_tile_data(tile_data):
    for key, val_list in tile_data.items():
        print(key, val_list)


def create_matching_tiles(tile_data, tile_size):
    # Tile data should contain a dictionary with north, south, east, west side rgb values
    # matching_tiles should return al
    # North, East, South, West  <-- directions
    # 0, 1, 2, 3  <-- indexes
    print('\ncreate_matching_tiles')
    matching_tiles = {}
    delta_threshold = 0

    tile_data_max = len(tile_data.keys())
    counter = 0

    for initial_key, initial_rgb_list in tile_data.items():
        counter += 1
        print('Finding match for Tile %s of %s' % (counter, tile_data_max))
        # matching_tiles[initial_key] = [[], [], [], []]
        matching_tiles[initial_key] = [{}, {}, {}, {}]

        # ---"1" Needs to be a default placeholder---
        if initial_key == '1':
            print('place holder found')
            tile_list = []
            for i in range(2, tile_data_max + 1):
                tile_list.append(str(i))
            continue

        # ---Obtain Matches for Each Side---
        for direction in ['north', 'east', 'south', 'west']:
            index, oppos_index = helper_functions.find_opposite(direction)

            matching_tiles[initial_key][index] = rgb_comparision(tile_data, initial_rgb_list, delta_threshold, index,
                                                                 oppos_index)

    # ---Base Probability Data---
    # Note: Base probability per tile based on how many times a tile can match with the tileset.
    base_probability = {}
    for tile in matching_tiles.keys():
        south_count = 0
        east_count = 0
        north_count = 0
        west_count = 0
        # print('\nSearching for Tile: %s' % tile)
        # print('Match List:', match_list)

        for match_list in matching_tiles.values():
            if str(tile) in match_list[0]:
                south_count += 1
            if str(tile) in match_list[1]:
                east_count += 1
            if str(tile) in match_list[2]:
                north_count += 1
            if str(tile) in match_list[3]:
                west_count += 1


            # for tile_list in match_list:
            #     # print('Looking in list:', tile_list)
            #     if str(tile) in tile_list:
            #         tile_count += 1


        # ---Store Probabilities Based on Which Side---
        # Order: South, East, North, West
        base_probability[tile] = [round(south_count / tile_data_max, 2), round(east_count / tile_data_max, 2),
                                  round(north_count / tile_data_max, 2), round(west_count / tile_data_max, 2)]

    # for tile, prob_list in base_probability.items():
        # print('\nTile: %s, occurs:' % tile)
        # print('\tSouth: %s Times\n\tEast: %s Times\n\tNorth: %s Times\n\tWest: %s Times' % (
        # prob_list[0] * tile_data_max, prob_list[1] * tile_data_max, prob_list[2] * tile_data_max, prob_list[3] * tile_data_max))
        # print(base_probability[tile])
    return matching_tiles, base_probability


# load_type='texture'
def pickle_tile_set_data(tileset_file, tile_size, rotated_tiles=True):
    # ---Check if Pickle Already Exists---
    print('---Create Identical Tile Data---')
    name = obtain_file_name(tileset_file)
    pickle_file = 'data/%s.pickle' % name

    # if isfile(pickle_file):
    #     print('%s already exists.' % pickle_file)
    #     return

    # ---Convert Tileset into Iterable List of Textures---
    print('\nload_tile_set')
    print('tile_size:', tile_size)

    tiles = defaultdict(list)
    tile_side_data = defaultdict(list)
    tile_number = 1
    im = Image.open(tileset_file)

    width, height = im.size

    # print('Tile Set Size:', width, height)
    tiles_x = width//tile_size
    tiles_y = height//tile_size
    tile_count = tiles_x * tiles_y
    if tile_count < 1:
        print('There are not enough tiles in %s.' % tileset_file)
        exit()
    elif tile_count < 2:
        print('There is only 1 tile in %s.' % tileset_file)
    else:
        print('There are a possible of %s usable tiles in %s.' % (tile_count, tileset_file))
    white_counter = 0
    black_counter = 0
    for i in range(height // tile_size):
        for j in range(width // tile_size):
            print('\n\nnew tile')
            duplicate_found = False
            # ---PIL Image Data---
            box = (j * tile_size, i * tile_size, (j + 1) * tile_size, (i + 1) * tile_size)

            cropped_im = im.crop(box)
            # new_size = cropped_im.size  # might want to save this to input tile size within pickle
            cropped_im_io = convert_im_to_bytes_io(cropped_im)
            cropped_im_pixels = convert_im_bytes_to_pixels(cropped_im_io)
            # print('cropped_im:', cropped_im)
            # print('cropped_im_io:', cropped_im_io)
            # print('cropped_im_pixels:', cropped_im_pixels)

            # ---Check if Tile is all White or all Black Colored---
            # Note: Account for possible blank or unused tiles.
            if cropped_im_pixels[0] == 255 and cropped_im_pixels[1] == 255 and cropped_im_pixels[2] == 255:
                # print('255 found!')
                white_counter += 1
                continue
            if cropped_im_pixels[0] == 0 and cropped_im_pixels[1] == 0 and cropped_im_pixels[2] == 0:
                # print('0 found!')
                black_counter += 1
                continue

            # ---Search for Similar Tiles---
            # print('---Search for Similar Tiles---')
            # print('Tile Number:',  tile_number)
            for pixels in tiles.values():
                if cropped_im_pixels == pixels[0]:
                    print('duplicate found!')
                    duplicate_found = True
                    break

            if not duplicate_found:


                # ---Input Tile Data---
                tiles[str(tile_number)].append(cropped_im_pixels)
                tile_side_data[str(tile_number)] = (obtain_side_pixel_data(cropped_im, tile_size))

                if tile_number == 1:
                    print('Place holder tile found. Skipping.')
                    tile_number += 1
                    continue
            duplicate_found = False
            # ---Obtain Rotated Image Data---
            if rotated_tiles:
                for _ in range(3):
                    rotated_im = cropped_im.rotate(angle=(_ + 1) * 90)
                    rotated_im_io = convert_im_to_bytes_io(rotated_im)
                    rotated_im_pixels = convert_im_bytes_to_pixels(rotated_im_io)

                    # ---Search for Similar Tiles---
                    print('\n---Search for Similar Rotated Tiles---')
                    print('Tile Number:', tile_number)

                    for pixels in tiles.values():
                        print('\npixels:', pixels[0])
                        print('cropped_im_pixels:', cropped_im_pixels)
                        print(cropped_im_pixels == pixels[0])
                        if pixels[0] == rotated_im_pixels:
                            print('duplicate rotated tile found at %s' % tile_number)
                            duplicate_found = True
                            break
                    if duplicate_found:
                        continue
                    tile_number += 1
                    tiles[str(tile_number)].append(rotated_im_pixels)
                    tile_side_data[str(tile_number)] = (obtain_side_pixel_data(rotated_im, tile_size))



                    # if rotated_im_pixels != cropped_im_pixels:
                    #     tiles[str(tile_number)].append(rotated_im_pixels)
                    #     tile_side_data[str(tile_number)] = (obtain_side_pixel_data(rotated_im, tile_size))
                    # else:
                    #     tile_number -= 1
                    #     print('duplicate tile found at %s' % tile_number)

            tile_number += 1
    print('tiles:', tiles)

    # ---Create Identical Tile Data---
    matching_tile_data, base_probability = create_matching_tiles(tile_side_data, tile_size)
    with open(pickle_file, 'wb') as f:
        pickle.dump(tiles, f)
        # pickle.dump(tile_side_data, f)
        pickle.dump(matching_tile_data, f)
        pickle.dump(base_probability, f)

    # # ---Verify Correct Data---
    # print('\n\nThere are %s usable tiles in %s' % (len(list(tiles.keys())), tileset_file))
    # print('Tiles:', tiles)
    # print('Base Probability:', base_probability)
    # print('Matching Tile Data:')
    # for key, direction_key in matching_tile_data.items():
    #     print('Tile: %s' % key)
    #     print('\tSouth:', direction_key[0])
    #     print('\tEast:', direction_key[1])
    #     print('\tNorth:', direction_key[2])
    #     print('\tWest:', direction_key[3])


def load_tile_textures(pickle_file, tile_size):
    print('Loading %s.' % pickle_file)

    tile_textures = {}
    matching_tile_data = {}
    base_probability = {}

    with open(pickle_file, 'rb') as f:
        tiles_pixel_data = pickle.load(f)  # tile pixel data
        matching_tile_data = pickle.load(f)  # all matching tiles per tile
        base_probability = pickle.load(f)  # all matching tiles per tile
    # print('base_probability:', base_probability)
    # print('matching_tile_data:', matching_tile_data)
    # print('tiles_pixel_data:', tiles_pixel_data)

    for tile_key, pixel_data in tiles_pixel_data.items():
        # print('Tile Key: %s, Pixel Data:' % tile_key, pixel_data[0])
        # print('Tile Key: %s, Pixel Data:' % tile_key, pixel_data)
        texture = Texture.create(size=(tile_size, tile_size))
        texture.blit_buffer(
            pbuffer=pixel_data[0],
            colorfmt='rgba',
            bufferfmt='ubyte',
            pos=(0, 0)
        )
        texture.mag_filter = 'nearest'
        tile_textures[str(tile_key)] = texture

    # print('\nTextures Created:')
    # print('Tile Textures:', tile_textures)
    # print('Matching Tile Data:', matching_tile_data)
    # print('Base Probabilities:', base_probability)

    return tile_textures, matching_tile_data, base_probability


def untexture_tiles(tiles):
    new_tiles = defaultdict(list)
    for name, texture in tiles.items():
        pixels = [texture.pixels]
        # print(name, pixels)
        new_tiles[name] = pixels

    return new_tiles


def obtain_side_pixel_data(cropped_im, tile_size):
    # super_print('obtain_side_pixel_data')
    side_pixel_data = []
    # North, East, South, West
    # The box is a 4-tuple defining the left, lower, right, and upper pixel coordinate.

    # South, East, North, West
    # The box is a 4-tuple defining the lower, right, top, and left pixel coordinate.
    north_box = (0, tile_size - 1, tile_size, tile_size)
    east_box = (tile_size - 1, 0, tile_size, tile_size)
    south_box = (0, 0, tile_size, 1)
    west_box = (0, 0, 1, tile_size)

    box_list = [south_box, east_box, north_box, west_box]
    for box in box_list:
        cropped = cropped_im.crop(box)
        cropped_pixels = convert_im_bytes_to_pixels(convert_im_to_bytes_io(cropped))
        side_pixel_data.append(cropped_pixels)

    return side_pixel_data


if __name__ == '__main__':
    # file, tile_size, rotated_tiles = 'tile_maps/wang_tiles_test_simple.png', 3, True
    # file, tile_size, rotated_tiles = 'tile_maps/dungeon_simple.png', 3, True
    file, tile_size, rotated_tiles = 'tile_maps/grass_corner.png', 3, True
    # file, tile_size, rotated_tiles = 'tile_maps/grass_water.png', 3, True

    pickle_tile_set_data(file, tile_size, rotated_tiles)
