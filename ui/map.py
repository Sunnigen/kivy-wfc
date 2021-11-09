from array import array
import pickle
from os.path import isfile
from random import choice

import numpy as np

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.scatter import Scatter

from ui.cursor import MapCursor
from utils.helper_functions import *
from utils import load_tileset
from wfc import WaveFunctionCollapse


Builder.load_file('ui/map.kv')


class Map(Scatter):
    layout = ObjectProperty(None)
    generate_iter = NumericProperty(0)
    continuous_generation = BooleanProperty(False)

    tile_set_loaded: bool = False
    x_max: int = 15
    y_max: int = 15

    lbl_stats = None  # place holder for parents label entropy
    lbl_current = None  # place holder for current selection
    prob_palette = None  # place holder for probability palette
    tile_palette = None  # place holder for tile palette

    border_len: int = 1  # space between tiles

    def __init__(self, x_max, y_max, tile_size, tile_set_file, **kwargs):
        super(Map, self).__init__(**kwargs)
        # Initial Variables
        self.x_max = x_max
        self.y_max = y_max
        self.tileset_file = 'data/' + tile_set_file
        self.tile_size = tile_size

        if self.lbl_stats:
            self.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (999, 999, 0)

        # WFC
        self.wfc = WaveFunctionCollapse(self, self.x_max, self.y_max)

        # Tile Grid Variables
        self.tiles = []  # list of dicionaries containing tile number and their respective texture
        self.tile_rect_array = None  # 2D Matrix of all kivy.graphics.Rectangle objects
        self.cursor = None
        self.resize_map()
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.scale = 6.0
        self.update_interval = None
        Window.bind(on_key_down=self.on_keyboard_down)
        self.user_touch = True
        self.center_map()

    def disable_user_interaction(self, *args):
        self.user_touch = False
        Window.unbind(on_key_down=self.on_keyboard_down)

    def enable_user_interaction(self, *args):
        self.user_touch = True
        Window.bind(on_key_down=self.on_keyboard_down)

    def on_keyboard_down(self, keyboard, keycode, *args):
        keycode = str(keycode)
        print("keycode: %s" % keycode)

        # Continuous Generation Toggle
        if keycode == '32':  # Space
            if self.continuous_generation:
                # Halt generation

                if self.parent:
                    self.parent.generation_switch.active = False

                self.continuous_generation = False
                return
            else:
                # Turn on generation
                if self.parent:
                    self.parent.generation_switch.active = True
                self.continuous_generation = True
                return

        # Advance X number of tile(s)
        elif keycode in ['49', '257']:
            self.parent.generate(1)
        elif keycode in ['53', '261']:
            self.parent.generate(5)

        # Step back X number of tile(s)
        elif keycode == '8':
            self.parent.generate(-1)

        # Reset Map
        elif keycode == '114':  # 'R'
            self.parent.reset_map_texture()

        # Move Cursor
        elif keycode in ['119', '264']:  # 'W'
            self.cursor.increment_y(1)
        elif keycode in ['115', '258']:  # 'S'
            self.cursor.increment_y(-1)
        elif keycode in ['97', '260']:  # 'A'
            self.cursor.increment_x(-1)
        elif keycode in ['100', '262']:  # 'D'
            self.cursor.increment_x(1)

        # Diagonal
        elif keycode == '101':  # E
            self.cursor.increment_x(1)
            self.cursor.increment_y(1)
        elif keycode == '113':  # Q
            self.cursor.increment_x(-1)
            self.cursor.increment_y(1)
        elif keycode == '122':  # Z
            self.cursor.increment_x(-1)
            self.cursor.increment_y(-1)
        elif keycode == '99':  # C
            self.cursor.increment_x(1)
            self.cursor.increment_y(-1)

        elif keycode == '114':  # R
            self.reset_map_texture()
        elif keycode == '98':  # B
            self.generate_iter += 1

        # Update Displayed Cursor Information
        if self.lbl_current:
            coord_x = self.cursor.x_coord
            coord_y = self.cursor.y_coord
            self.update_palette()
            tile_name = self.wfc.tile_array[coord_x][coord_y]
            self.lbl_current.text = "Cursor at: (%s, %s)\nTile: %s" % (coord_x, coord_y, tile_name)

    def on_touch_down(self, touch):
        if not self.user_touch:
            return

        # Zoom In/Out
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown' and self.scale <= 20.0:
                self.scale += 0.25
            elif touch.button == 'scrollup' and self.scale >= 1.0:
                self.scale -= 0.25

            return super(self.__class__, self).on_touch_down(touch)

        # Tile Double Click Displays Tile Probability Information
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            local_x, local_y = self.to_local(*touch.pos)
            coord_x = int(local_x/(self.tile_size + 1))
            coord_y = int(local_y/(self.tile_size + 1))
            if self.wfc.check_coordinate_within_map(coord_x, coord_y):
                tile_name = self.wfc.tile_array[coord_x][coord_y]
                self.cursor.move_cursor_by_pos(self.tile_rect_array[coord_x][coord_y].pos)
                self.cursor.x_coord = coord_x
                self.cursor.y_coord = coord_y
                self.update_palette()
                if self.lbl_current:
                    # print(str((coord_x, coord_y)), str(self.tiles_array_probabilities[coord_x][coord_y]))
                    # self.lbl_current.text = "Cursor at: " + str((coord_x, coord_y)) + "Tile:" + str(tile_name) + "Probabilities: " + str(tile_probabilities)
                    # self.lbl_current.text = "Cursor at: (%s, %s)\nTile: %s\nTile Probabilities: %s" % (coord_x, coord_y, tile_name, tile_probabilities)
                    self.lbl_current.text = "Cursor at: (%s, %s)\nTile: %s" % (coord_x, coord_y, tile_name)
        return super(self.__class__, self).on_touch_down(touch)

    def place_tile(self, x, y, dt=0):
        key, texture = str(self.wfc.tile_array[x][y]), self.tiles[str(self.wfc.tile_array[x][y])]
        self.tile_rect_array[x][y].texture = texture

    def print_stats(self):
        super_print('Print Stats')
        tiles_array = np.rot90(self.wfc.tile_array, k=1)
        tiles_array_probabilities = np.rot90(self.wfc.tiles_array_probabilities, k=1)
        print('Probabilities:')
        for i in range(len(tiles_array_probabilities)):
            print('\nrow %s from top' % (len(tiles_array_probabilities) - i - 1), tiles_array_probabilities[i])

        print('Current Tiles:')
        for y in range(self.y_max):
            print(self.y_max - y - 1, tiles_array[y])
        print('Number of Undecided Tiles:', len(self.wfc.undecided_tiles))
        print(self.wfc.undecided_tiles)
        print('Lowest Entropy:', self.wfc.lowest_entropy)

        print('\nGeneration Stats:')
        print('tile_chosen_from_weighted_probabilities:', self.wfc.tile_chosen_from_weighted_probabilities)
        print('tile_chosen_randomly:', self.wfc.tile_chosen_randomly)
        print('probability_reset:', self.wfc.probability_reset)

    def update_palette(self):
        x, y = self.cursor.x_coord, self.cursor.y_coord
        tile = self.wfc.tile_array[x][y]
        tile_tex = self.tiles[str(tile)]
        tile_prob = {}

        if len(self.wfc.tiles_array_probabilities[x][y]) > 0:
            for key, prob in self.wfc.tiles_array_probabilities[x][y].items():
                tile_prob[key] = [prob, self.tiles[str(key)]]

        self.prob_palette.update_palette(x, y, tile, tile_tex, tile_prob)

    def force_specific_tile(self, new_tile):
        # Force a Tile Selected from User
        x, y = self.cursor.x_coord, self.cursor.y_coord
        if new_tile:
            self.wfc.tile_array[x][y] = new_tile
            if (x, y) in self.wfc.undecided_tiles:
                self.wfc.undecided_tiles.remove((x, y))
            self.wfc.probability_sphere(x, y, new_tile)
            self.place_tile(x, y)
            self.wfc.tiles_array_probabilities[x][y] = {}
            self.update_palette()

    def place_random_tile(self):
        if not self.wfc.undecided_tiles:
            return
        x, y = choice(self.wfc.undecided_tiles)
        new_tile = choice(list(self.tiles.keys()))

        if new_tile:
            self.wfc.tile_array[x][y] = new_tile
            if (x, y) in self.wfc.undecided_tiles:
                self.wfc.undecided_tiles.remove((x, y))
            self.probability_sphere(x, y, new_tile)
            self.place_tile(x, y)

        self.wfc.tiles_array_probabilities[x][y] = {}
        self.update_palette()

    def force_tile(self):
        # Force Tile Placement and Update Probabilities Around Tile
        x, y = self.cursor.x_coord, self.cursor.y_coord

        if len(self.wfc.tiles_array_probabilities[x][y].keys()) < 1:
            return
        new_tile = self.new_tile_based_on_surrounding_tiles(x, y)

        if new_tile:
            if (x, y) in self.wfc.undecided_tiles:
                self.wfc.undecided_tiles.remove((x, y))
            self.wfc.tile_array[x][y] = new_tile
            self.probability_sphere(x, y, new_tile)
            self.place_tile(x, y)
        self.wfc.tiles_array_probabilities[x][y] = {}
        self.update_palette()

    def place_tiles(self, x_max, y_max):
        # Place a tile texture from coordinate
        for y in range(y_max):
            for x in range(x_max):
                # key, texture = str(self.wfc.tile_array[x][y]), self.tiles[str(self.wfc.tile_array[x][y])][0]
                key, texture = str(self.wfc.tile_array[x][y]), self.tiles[str(self.wfc.tile_array[x][y])][0]
                self.tile_rect_array[x][y].texture = texture

    def on_continuous_generation(self, *args):
        if not self.check_for_tile_set_data():
            return

        if self.continuous_generation:
            super_print('starting continuous generation')
            self.update_interval = Clock.schedule_interval(self.wfc.weighted_placement, 0.01)
        else:
            super_print('ceasing continuous generation')
            self.update_interval.cancel()

    def on_generate_iter(self, *args):
        # print('on_generate_iter')
        if self.continuous_generation:
            self.generate_iter = 0
            return

        if not self.check_for_tile_set_data():
            self.generate_iter = 0
            return

        if self.generate_iter < 1:
            # print('generate_iter is less than 1')
            if self.update_interval:
                # print('stopping interval')
                self.update_interval.cancel()
                return

        if self.generate_iter > 0:
            # print('generate_iter is more than 0')
            if not self.update_interval:
                # print('no update interval exists, creating self.update_interval')
                self.update_interval = Clock.schedule_interval(self.wfc.weighted_placement, 0.001)
                return

            elif not self.update_interval.is_triggered:
                # print('update interval is not triggered, restarting self.update_interval')
                self.update_interval = Clock.schedule_interval(self.wfc.weighted_placement, 0.001)
                return

    def center_map(self):
        self.scale = 6.0
        self.update_size()
        self.pos = ((Window.width/2) - (self.size[0] / 2) * self.scale, (Window.height/2) - (self.size[1] / 2) * self.scale)
        # self.pos = ((self.size[0] / 2), (self.y_max * self.tile_size * 0.5) - (self.size[1] / 2))

    def reset_cursor(self):
        if self.cursor:
            self.cursor = None

        with self.layout.canvas:
            hue = Color(0, 0, 0, 1)
            self.cursor = MapCursor(self, (self.x_max, self.y_max), self.tile_size, hue)
        self.cursor.begin_cursor_animation()

    @staticmethod
    def reset_tex(rect, size):
        texture = Texture.create(size=size)
        size = int(size[0] * size[1] * 4)
        # buf = []
        buf = [255 for x in range(int(size))]
        # for _ in range(size):
        #     buf.extend([255, 255, 255, 255])
        arr = array('B', buf)
        texture.blit_buffer(arr, colorfmt='rgba', bufferfmt='ubyte')
        rect.size = texture.size
        rect.texture = texture

    def reset_map_texture(self):
        super_print('Reseting Map!')
        self.wfc.reset_generation_data()
        for y in range(self.y_max):
            for x in range(self.x_max):
                self.reset_tex(self.tile_rect_array[x][y], (self.tile_size, self.tile_size))

    def resize_map(self):
        self.tile_rect_array = None
        self.layout.canvas.clear()
        self.tile_rect_array = [[None for y in range(self.y_max)] for x in range(self.x_max)]
        with self.layout.canvas:
            Color(1, 1, 1, 1)
            for y in range(self.y_max):
                for x in range(self.x_max):
                    rect = Rectangle(
                        size=(self.tile_size, self.tile_size),
                        pos=((x * self.tile_size) + (x * self.border_len), (y * self.tile_size) + (y * self.border_len))
                    )
                    self.tile_rect_array[x][y] = rect
        self.reset_cursor()

    def reset_ui(self):
        if self.lbl_stats:
            self.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (999, 999, 0)
        self.center_map()

    def change_map_size(self, x_max, y_max, tile_size):
        if self.x_max == x_max and self.y_max == y_max and self.tile_size == tile_size:
            return
        self.x_max, self.y_max, self.tile_size = x_max, y_max, tile_size
        self.wfc.x_max, self.wfc.y_max = x_max, y_max

        # self.wfc.tile_range = int(self.wfc.x_max * self.wfc.y_max)
        self.wfc.tile_range = 4
        # self.wfc.tile_range = (self.x_max + self.y_max)/4  # Subtract .1 so we can at least retain some probability data at max tile range
        # if self.wfc.tile_range < 1:
        #     self.wfc.tile_range = 1
        #
        # if self.wfc.tile_range > 5:
        #     self.wfc.tile_range = 5
        #
        # self.wfc.tile_range += 0.1

        self.resize_map()
        self.wfc.reset_generation_data()
        self.enable_user_interaction()

    def check_for_tile_set_data(self):
        if not self.tiles:
            print('tile set not loaded')
            print('load tile set!')
            return False
        return True

    def load_tile_set_data(self, file=''):
        if not file:
            tileset_file = self.tileset_file
        else:
            tileset_file = file
        # print('Loading Tileset File: %s' % tileset_file)
        self.tiles, self.wfc.matching_tile_data, self.wfc.base_probability = load_tileset.load_tile_textures(tileset_file, self.tile_size)
        # print('tiles:', self.tiles)
        # self.tile_palette.load_tile_palette(self.tiles, self.wfc.base_probability)

    def save_probabilities(self):
        # Permanently Update Probability Settings in Pickle
        # self.base_probability[tile] = new_probability_list

        if not isfile(self.tileset_file):
            print('%s file cannot be found.' % self.tileset_file)
            return
        # print('self.tiles:', self.tiles)

        tiles = load_tileset.untexture_tiles(self.tiles)

        with open(self.tileset_file, 'wb') as f:
            pickle.dump(tiles, f)
            pickle.dump(self.wfc.matching_tile_data, f)
            pickle.dump(self.wfc.base_probability, f)
        self.tile_palette.load_tile_palette(self.tiles, self.wfc.base_probability)

    def toggle_border(self):
        # Add/Remove Space Between Tiles
        self.border_len -= 1
        self.border_len = abs(self.border_len)
        self.update_size()

        # Re-Position Tiles
        for y in range(self.y_max):
            for x in range(self.x_max):
                tile = self.tile_rect_array[x][y]
                tile.pos = (x * self.tile_size) + (x * self.border_len), (y * self.tile_size) + (y * self.border_len)

    def update_size(self, *args):
        self.size = ((self.x_max * self.tile_size) + (self.border_len * self.x_max),
                     (self.y_max * self.tile_size) +  (self.border_len * self.y_max))

    def update_rect(self, *args):
        self.update_size()
        self.layout.pos = self.pos
        self.layout.size = self.size
