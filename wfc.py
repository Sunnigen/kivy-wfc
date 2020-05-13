from collections import Counter, deque
from random import randint, shuffle

import numpy as np


import helper_functions
import pathfinding


class WaveFunctionCollapse:
    def __init__(self, gui, width, height):
        self.x_max = width
        self.y_max = height
        self.gui = gui
        self.tile_range = int(width * height)  # Subtract .1 so we can at least retain some probability data at max tile range

        self.tile_range += 0.1
        self.undecided_tiles = deque()
        self.matching_tile_data = {}  # dictionary of tile numbers and their matching tiles respective to each side
        self.base_probability = {}  # dictionary containing tile numbers as keys and connected probabilities
        # per each direction
        self.tile_array = None  # 2D matrix containing tile numbers stored as strings
        self.tiles_array_probabilities = None  # 2D Matrix of dictionaries of every possible tile per coordinate
        self.lowest_entropy = [(999, 999), 0]  # coordinate point with highest tile probability
        self.probability_coordinate_list = {}  # test to find highest entropy, {val:key}

        # Generation Counters
        self.attempts = 0
        self.tile_chosen_from_weighted_probabilities = 0
        self.tile_chosen_randomly = 0
        self.probability_reset = 0

        # Probability Sphere Variables
        self.field = None
        self.reset_generation_data()

    def reset_generation_data(self):
        self.field = pathfinding.GridWithWeights(self.x_max, self.y_max)
        self.tile_array = [["1" for y in range(self.y_max)] for x in range(self.x_max)]  # tile names
        self.tiles_array_probabilities = np.array(
            [[{} for y in range(self.y_max)] for x in range(self.x_max)])  # tile probabilities
        self.undecided_tiles = deque([(x, y) for y in range(self.y_max) for x in range(self.x_max)])
        shuffle(self.undecided_tiles)
        self.attempts = 0
        self.tile_chosen_from_weighted_probabilities = 0
        self.tile_chosen_randomly = 0
        self.probability_reset = 0
        self.lowest_entropy = [(999, 999), 0]

    def find_lowest_entropy(self):
        coord_score = [(999, 999), 0]

        # Loop Through all Tiles and Find Lowest Entropy
        for y in range(self.y_max):
            for x in range(self.x_max):
                if self.tiles_array_probabilities[x][y]:
                    entropy_val = sum(Counter(self.tiles_array_probabilities[x][y].values()))
                    entropy_key = len(self.tiles_array_probabilities[x][y].keys())
                    entropy = entropy_val/entropy_key
                    if entropy > coord_score[1]:
                        coord_score = [(x, y), entropy]

        # Check if Score is Lower than Current
        if coord_score[1] > self.lowest_entropy[1]:
            self.lowest_entropy = coord_score

            # Update Label
            if self.gui.lbl_stats:
                self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (self.lowest_entropy[0][0], self.lowest_entropy[0][1], self.lowest_entropy[1])

    def weighted_placement(self, dt=0):
        # ---Weighted Placement with No Backjumping---

        # Check if There are Undecided Tiles
        if len(self.undecided_tiles) < 1:
            self.gui.generate_iter = 0
            return

        # Select Tile Index with Lowest Entropy
        x, y = self.lowest_entropy[0]

        # Check if Tile with Lowest Entropy Exists
        if (x, y) in self.undecided_tiles:
            self.undecided_tiles.remove((x, y))
        else:
            x, y = self.undecided_tiles.popleft()

        # ---Check for Existing Probabilities---
        new_tile = self.new_tile_based_on_surrounding_tiles(x, y)

        # # ---Select Tile on Random---
        if not new_tile:
            if self.check_decided_neighbors(x, y):
                # ---No Decided Neighbors, Randomly Selecting Tile---
                new_tile = str(randint(2, len(self.gui.tiles.keys())))
                self.tile_chosen_randomly += 1

        # ---Update Probabilities Based on Tile Selected At Coordinate---
        if new_tile:
            # ---Update Tile Arrays--
            self.tile_chosen_from_weighted_probabilities += 1
            self.tile_array[x][y] = new_tile
            if (x, y) in self.undecided_tiles:
                self.undecided_tiles.remove((x, y))
            self.probability_sphere(x, y, new_tile)

        # ---Place Tile if Tile was Selected---
        self.tiles_array_probabilities[x][y] = {}
        if self.lowest_entropy[0] not in self.undecided_tiles or not self.tiles_array_probabilities[self.lowest_entropy[0][0]][self.lowest_entropy[0][1]]:
            self.lowest_entropy = [(999, 999), 0]
            if self.gui.lbl_stats:
                self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (999, 999, 0)
        self.find_lowest_entropy()
        if self.lowest_entropy[1] <= 0 and len(self.undecided_tiles) > 0:
            self.lowest_entropy[0] = self.undecided_tiles[0]
        if new_tile:
            self.gui.place_tile(x, y)
        self.gui.generate_iter -= 1

    def probability_sphere(self, x, y, new_tile):
        # Note: Updates a "Sphere"(Diamond of tile_range size)
        # helper_functions.super_dprint('Probability Sphere')
        start = (x, y)
        came_from, cost_so_far, coordinates_travelled = \
            pathfinding.breadth_first_search_with_probability(self.field, start, self.tile_range)
        if (x, y) in coordinates_travelled:
            coordinates_travelled.remove((x, y))

        # ---Update probabilities all around initial tile---
        for coordinate in coordinates_travelled:
            # ---Check if Tile Already Exists for Coordinate---
            if self.tile_array[coordinate[0]][coordinate[1]] != "1":
                continue
            (i, j) = coordinate
            probability_list, final_tile_type = self.obtain_probabilities_list(new_tile, i, j, x, y,
                                                                               coordinates_travelled.index(coordinate))

            if len(probability_list) > 0:
                # Set Final Probabilities
                self.tiles_array_probabilities[i][j] = probability_list
            else:
                # No Probability Found
                self.tiles_array_probabilities[i][j] = {}

    def obtain_probabilities_list(self, new_tile, i, j, x, y, iteration):
        probability_tile_list = []
        adjacent_tile_list = []
        probability_list = []
        final_tile_type = ''

        direction_list = [(i + 0, j + 1, 'north'),
                          (i + 1, j + 0, 'east'),
                          (i + 0, j + (-1), 'south'),
                          (i + (-1), j + 0, 'west')]
        shuffle(direction_list)
        for _ in range(4):
            px, py, direction = direction_list.pop()
            # if x == px and y == py:
                # no point in looking at the origin coordinate, that should aleady have a decided tile
                # continue
            if self.check_coordinate_within_map(px, py):
                ind, op_ind = helper_functions.find_opposite(direction)
                # helper_functions.super_print('Checking: %s from coordinate: (%s, %s), Iteration: %s' % (direction, i, j, iteration))
                tiles_list, tile_type = self.modify_probability(new_tile, op_ind, i, j, x, y, px, py)
                # print('%s Tile Type: %s' % (direction, tile_type))
                if len(tiles_list.keys()) > 0:
                    if tile_type == 'adjacent':
                        adjacent_tile_list.append(tiles_list)
                        # print('Appending to Adjacent Tile List:', tiles_list)
                    elif tile_type == 'probability':
                        probability_tile_list.append(tiles_list)
                        # print('Appending to Probability Tile List:', tiles_list)

        if adjacent_tile_list:
            # ---Keep and Combine Matches Only Between Tiles---
            if len(self.tiles_array_probabilities[i][j].keys()) > 0:
                adjacent_tile_list.append(self.tiles_array_probabilities[i][j])
            probability_list = helper_functions.dict_intersect(adjacent_tile_list)
            final_tile_type = 'adjacent'
        elif probability_tile_list:
            # ---Combine All Probabilities---
            if len(self.tiles_array_probabilities[i][j].keys()) > 0:
                probability_tile_list.append(self.tiles_array_probabilities[i][j])
            probability_list = helper_functions.dict_combine(probability_tile_list)
            # probability_list = helper_functions.dict_intersect(probability_tile_list)
            final_tile_type = 'probability'

        # print('Final Tile Type: %s' % final_tile_type)
        # print('Final Probabilities:', probability_list)

        # print('returning complete probability_list:', probability_list)
        return probability_list, final_tile_type

    def new_tile_based_on_surrounding_tiles(self, x, y):
        # ---Check if New Tile Selected Fits in with Possible tiles from surrounding tiles---
        if len(self.tiles_array_probabilities[x][y]) < 1:
            return None
        new_tile = self.check_match(helper_functions.weighted_choice(self.tiles_array_probabilities[x][y]), x, y)
        return new_tile

    def check_match(self, new_tile, x, y):
        match_list = []  # List of (4) lists of probabilities from all (4) directions

        # Obtain All Possible Probabilities from All (4) Directions based on New Tile
        for px, py, direction in [(x + 0, y + 1, 'north'), (x + 1, y + 0, 'east'), (x + 0, y + (-1), 'south'), (x + (-1), y + 0, 'west')]:
            ind, op_ind = helper_functions.find_opposite(direction)
            if self.check_coordinate_within_map(px, py):  # check within map
                if self.tile_array[px][py] != "1":  # check for non-placeholder tile
                    match_list.append(self.matching_tile_data[str(self.tile_array[px][py])][op_ind].keys())

        # Return Impossible if New Tile isn't in the Matching List
        for m in match_list:
            if new_tile not in m:
                # New Tile Does Not Match Surroundings!
                return ''
        # New Tile is a Good Match
        return new_tile

    def modify_probability(self, new_tile, op_index, i, j, x, y, px, py):
        # ---Modify Probability at Given Coordinate---
        # print('\nModify Probability at (%s, %s) from (%s, %s), from origin: (%s, %s)' % (i, j, px, py, x, y))
        # TODO: return if base_probability_value < 1
        # ---Obtain Probabilities from Previous Tiles and Propagate---
        tiles_to_check = Counter({})
        probability_value = 1
        # probability_value = helper_functions.determine_probability_value(i, j, x, y, self.tile_range)
        if probability_value <= 0:
            return {}, ''

        # ---Search for Adjacent Tile---
        if self.tile_array[px][py] != "1":
            # print('tile already exists, using actual tile:', self.tile_array[px][py])
            tile_type = 'adjacent'
            for tile, percentage in self.matching_tile_data[str(self.tile_array[px][py])][op_index].items():
                base_probability = self.base_probability[tile][op_index]
                tiles_to_check[tile] = round(probability_value * base_probability * percentage * 2.5, 2)
        else:
            # ---Search for Adjacent Probabilities---
            if len(self.tiles_array_probabilities[px][py].keys()) < 1 or probability_value <= 0:
                # print('No nearby tiles, probabilities to choose from or probability value is <= 0')
                return {}, ''  # nothing to return

            tile_type = 'probability'
            # print('tile does not exist yet, extending from probabilities')
            for key in self.tiles_array_probabilities[px][py].keys():
                for possible_tile, percentage in self.matching_tile_data[str(key)][op_index].items():
                    base_probability = self.base_probability[possible_tile][op_index]
                    tiles_to_check[possible_tile] = round(probability_value * base_probability * percentage, 2)

        # ---Find Top Probability Values---
        modified_probabilities = dict(tiles_to_check.most_common(15))
        # print('returning:', modified_probabilities)
        return modified_probabilities, tile_type

    def check_decided_neighbors(self, x, y):
        # ---Check if Surrounding Coordinates are Undecided---
        for new_x, new_y in [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]:
            if not (new_x, new_y) in self.undecided_tiles:
                if self.check_coordinate_within_map(new_x, new_y):
                    return False  # At least (1) tile neighbor has been decided
        return True  # All neighbors are undecided

    def check_coordinate_within_map(self, x, y):
        # ---(x, y) Must be Within Map---
        # print('---(x, y) Must be Within Map---')
        if 0 <= x <= self.x_max - 1 and 0 <= y <= self.y_max - 1:
            # print(((x, y), 'is within map.'))
            return True
        return False
