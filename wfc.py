from collections import Counter, deque
from random import randint, shuffle
from typing import Dict, Iterable, List, Tuple

import numpy as np

from utils import helper_functions
import pathfinding


import cProfile
import functools
import pstats
import tempfile

def profile_me(func):
    @functools.wraps(func)
    def wraps(*args, **kwargs):
        file = tempfile.mktemp()
        profiler = cProfile.Profile()
        profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(file)
        metrics = pstats.Stats(file)
        metrics.strip_dirs().sort_stats('time').print_stats(100)
    return wraps


class WaveFunctionCollapse:
    x_max: int = 0
    y_max: int = 0
    tile_range: int = 0
    undecided_tiles: Iterable = None
    impossible_tiles: Iterable = None
    matching_tile_data: Dict = None  # dictionary of tile numbers and their matching tiles respective to each side
    base_probability: Dict = None  # dict containing tile numbers as keys and connected probabilities per each direction
    tile_array: List[List[int]] = None  # 2D matrix containing tile numbers stored as int
    tiles_array_probabilities: np.ndarray = None  # 2D Numpy Matrix of dicts of every possible tile per coordinate
    lowest_entropy: Tuple[Tuple[int, int], int] = [(999, 999), 999]  # coordinate point with lowest tile probability
    probability_coordinate_list: Dict = None  # test to find highest entropy, {val:key}

    # Generation Counters
    attempts: int = 0
    tile_chosen_from_weighted_probabilities: int = 0
    tile_chosen_randomly: int = 0
    probability_reset: int = 0

    # Probability Sphere Variables
    field: pathfinding.GridWithWeights = None

    def __init__(self, gui, width: int, height: int) -> None:
        self.x_max = width
        self.y_max = height
        self.gui = gui

        # Subtract .1 so we can at least retain some probability data at max tile range
        # self.tile_range = (width * height) // 4
        self.tile_range = 3
        self.tile_range += 0.1

        self.undecided_tiles = deque()
        self.matching_tile_data = {}
        self.base_probability = {}


        self.last_tile_changed = (0, 0)

        self.reset_generation_data()

    def reset_generation_data(self):
        self.field = pathfinding.GridWithWeights(self.x_max, self.y_max)
        self.tile_array = [[0 for y in range(self.y_max)] for x in range(self.x_max)]  # tile names
        self.tiles_array_probabilities = np.array(
            [[{} for y in range(self.y_max)] for x in range(self.x_max)])  # tile probabilities
        self.undecided_tiles = deque([(x, y) for y in range(self.y_max) for x in range(self.x_max)])
        self.impossible_tiles = []
        shuffle(self.undecided_tiles)
        self.attempts = 0
        self.tile_chosen_from_weighted_probabilities = 0
        self.tile_chosen_randomly = 0
        self.probability_reset = 0

        # Start off with a random tile
        x = (randint(0, self.x_max - 1))
        y = (randint(0, self.y_max - 1))

        self.lowest_entropy = [(x, y), 999]
        if self.gui.lbl_stats:
            self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (x, y, 999)

            self.force_weighted_placement()


    def find_lowest_entropy(self):
        # print('find_lowest_entropy')
        """
        find_lowest_entropy calculates the lowest value depending how many
        """

        # self.reset_entropy()

        for x, y in self.undecided_tiles:
            if self.tiles_array_probabilities[x][y]:
                entropy_score = len(self.tiles_array_probabilities[x][y])

                if entropy_score < self.lowest_entropy[1]:
                    self.lowest_entropy = [(x, y), entropy_score]

        # Update Label
        if self.gui.lbl_stats:
            self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (self.lowest_entropy[0][0],
                                                                       self.lowest_entropy[0][1],
                                                                       self.lowest_entropy[1])
        return

        # Loop Through all Tiles and Find Lowest Entropy
        for y in range(self.y_max):
            for x in range(self.x_max):
                if self.tiles_array_probabilities[x][y]:
                    # entropy_val = sum(Counter(self.tiles_array_probabilities[x][y].values()))
                    # print("entropy_val: ", entropy_val)
                    possibility_count = len(self.tiles_array_probabilities[x][y])
                    # print("entropy_key: ", entropy_key)
                    # entropy = entropy_val/entropy_key
                    if possibility_count < coord_score[1]:
                        coord_score = [(x, y), possibility_count]

        # Check if Found Score is Lower than Current Selected
        if coord_score[1] < self.lowest_entropy[1]:
            self.lowest_entropy = coord_score

        # Update Label
        if self.gui.lbl_stats:
            self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (self.lowest_entropy[0][0],
                                                                       self.lowest_entropy[0][1],
                                                                       self.lowest_entropy[1])

    def force_weighted_placement(self):
        # Force Placement of a Random Tile
        # Needed if no collapsed tiles, to get things started
        x = (randint(0, self.x_max - 1))
        y = (randint(0, self.y_max - 1))

        self.lowest_entropy = [(x, y), 999]

        new_tile = randint(1, len(self.gui.tiles) - 1)

        self.tile_array[x][y] = new_tile
        self.field.walls.append((x, y))
        if (x, y) in self.undecided_tiles:
            self.undecided_tiles.remove((x, y))
        self.reset_entropy()
        self.probability_sphere(x, y, new_tile)
        self.gui.place_tile(x, y)
        if self.lowest_entropy[1] == 999:
            self.find_lowest_entropy()

        self.tiles_array_probabilities[x][y] = {}


    # @profile_me
    def weighted_placement(self, dt=0):
        # Weighted Placement with No Backjumping

        # 1. Check if There are Undecided Tiles
        if not self.undecided_tiles:
            self.gui.generate_iter = 0
            return

        # 2. Select Tile Index with Lowest Entropy
        x, y = self.lowest_entropy[0]

        # 3. Check if Tile with Lowest Entropy Exists or Pick the Longest Lasting Undecided Tile
        if (x, y) in self.undecided_tiles:
            self.undecided_tiles.remove((x, y))

        # 4. Select Tile based on  Existing Probabilities else Select Random Tile
        new_tile = self.new_tile_based_on_surrounding_tiles(x, y)

        # 5. Update Probabilities Based on Tile Selected At Coordinate
        # if new_tile:
            # print('new tile:', new_tile)
            # Update Tile Arrays
        self.tile_chosen_from_weighted_probabilities += 1
        self.tile_array[x][y] = new_tile
        self.field.walls.append((x, y))
        self.reset_entropy()
        self.probability_sphere(x, y, new_tile)
        self.gui.place_tile(x, y)
        if self.lowest_entropy[1] == 999:
            self.find_lowest_entropy()


        # 6. Find Lowest Entropy
        # print('emptying probabilities: ', x, y)
        self.tiles_array_probabilities[x][y] = {}

        # if self.lowest_entropy[0] not in self.undecided_tiles or not self.tiles_array_probabilities[self.lowest_entropy[0][0]][self.lowest_entropy[0][1]]:


        # self.find_lowest_entropy()
        # if self.lowest_entropy[1] <= 0 and self.undecided_tiles:
        #     self.lowest_entropy[0] = self.undecided_tiles[0]

        # 7. Finally, place Tile if Tile was Selected
        # if new_tile:
        #     self.gui.place_tile(x, y)

        # Update Generation Counter
        self.gui.generate_iter -= 1
        # print('number of undecided tiles: %s' % len(self.undecided_tiles))
        # print('number of impossible tiles: %s' % len(self.impossible_tiles))

    def probability_sphere(self, x, y, new_tile):
        """
        Updates a "Sphere" (Diamond of "tile_range" size) around newly placed tile
        """
        # helper_functions.super_print('Probability Sphere')

        # Obtain List of Uncollapsed Tile Coordinates to Travel Through in an Orderly Fashion
        start = (x, y)
        came_from, cost_so_far, coordinates_travelled = \
            pathfinding.breadth_first_search_with_probability(self.field, start, self.tile_range)

        # Remove Existing Tile
        if start in coordinates_travelled:
            coordinates_travelled.remove(start)

        # Update probabilities all around initial tile
        # print('coordinates_traveled', coordinates_travelled,' starting at', start)
        # if not coordinates_travelled:
        #


        for coordinate in coordinates_travelled:
            i, j = coordinate
            probability_list, final_tile_type = self.obtain_probabilities_list(new_tile, i, j, x, y,
                                                                               coordinates_travelled.index(coordinate))
            # print('updating lowest entropy:', i, j, len(probability_list), probability_list)

            if probability_list:
                # Set Final Probabilities
                self.tiles_array_probabilities[i][j] = probability_list

                # Check if Good Candidate for Next Lowest Entropy Selection
                entropy_score = len(probability_list)

                if entropy_score <= self.lowest_entropy[1]:
                    self.lowest_entropy = [(i, j), entropy_score]
                    # print(self.lowest_entropy)

                    if self.gui.lbl_stats:
                        self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (i, j, self.lowest_entropy[1])

            else:
                # No Probability Found
                print("\n### Impossible Tile Found at (%s, %s)###" % (i, j))
                print("tile array probabilityes: ", self.tiles_array_probabilities[i][j])
                print("coordinates_travelled: ", coordinates_travelled)
                print("last tile changed: ", self.last_tile_changed)
                self.impossible_tiles.append((i, j))
                # self.undecided_tiles.remove((i, j))
                # self.tiles_array_probabilities[i][j] = {}
                self.gui.continuous_generation = False

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
                # tiles_list, tile_type = self.modify_probability(new_tile, op_ind, i, j, x, y, px, py)
                # print('%s Tile Type: %s' % (direction, tile_type))

                if tile_type == 'adjacent':
                    # adjacent_tile_list = set( set(adjacent_tile_list.keys()) & tiles_list)
                    adjacent_tile_list.append(tiles_list)
                    # print('Appending to Adjacent Tile List:', tiles_list)
                elif tile_type == 'probability':
                    adjacent_tile_list.append(tiles_list)
                    probability_tile_list.append(tiles_list)
                        # print('Appending to Probability Tile List:', tiles_list)

        if adjacent_tile_list:
            # Keep and Combine Matches Only Between Tiles
            if len(self.tiles_array_probabilities[i][j]) > 0:
                adjacent_tile_list.append(self.tiles_array_probabilities[i][j])
            probability_list = helper_functions.dict_intersect(adjacent_tile_list)
            final_tile_type = 'adjacent'
        elif probability_tile_list:
            # Combine All Probabilities
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
        # Check if Existing Coordinates have any Defined Probabilites
        # Note: In a perfect world, the statement below wouldn't be needed
        if len(self.tiles_array_probabilities[x][y]) < 1:
            # print("No probabilities at (%s, %s)!!" % (x, y), self.tiles_array_probabilities[x][y])
            # self.gui.continuous_generation = False
            # import sys
            # sys.exit()
            return None

        # Select New Tile from Possible tiles from surrounding tiles
        return self.check_match(helper_functions.weighted_choice(self.tiles_array_probabilities[x][y]), x, y)

    def check_match(self, new_tile, x, y):
        match_list = []  # List of (4) lists of probabilities from all (4) directions

        # Obtain All Possible Probabilities from All (4) Directions based on New Tile
        for px, py, direction in [(x + 0, y + 1, 'north'),
                                  (x + 1, y + 0, 'east'),
                                  (x + 0, y + (-1), 'south'),
                                  (x + (-1), y + 0, 'west')
                                  ]:
            ind, op_ind = helper_functions.find_opposite(direction)

            if self.check_coordinate_within_map(px, py):  # check within map
                if self.tile_array[px][py] != 0:  # check for non-placeholder tile
                    match_list.append(self.matching_tile_data[self.tile_array[px][py]][op_ind])

        # Return Impossible if New Tile isn't in the Matching List

        for m in match_list:
            if new_tile not in m:
                # New Tile Does Not Match Surroundings!
                print("# New Tile at (%s, %s) Does Not Match Surroundings!" % (x, y))
                print("match_list: ", match_list)
                return None
        # New Tile is a Good Match
        self.last_tile_changed = (x, y)
        # print("last tile changed: ", self.last_tile_changed)
        return new_tile

    # @profile_me
    def modify_probability(self, new_tile, op_index, i, j, x, y, px, py):
        # Modify Probability at Given Coordinate
        # print('\nModify Probability at (%s, %s) from (%s, %s), from origin: (%s, %s)' % (i, j, px, py, x, y))
        # TODO: return if base_probability_value < 1
        # Obtain Probabilities from Previous Tiles and Propagate
        modified_probabilities = Counter({})
        probability_value = 1
        # probability_value = helper_functions.determine_probability_value(i, j, x, y, self.tile_range)
        # if probability_value <= 0:
        #     print("probability ")
        #     return {}, ''

        # Search for Adjacent Tile
        if self.tile_array[px][py] != 0:
            # print('tile already exists, using actual tile:', self.tile_array[px][py])
            tile_type = 'adjacent'
            # print("self.matching_tile_data[self.tile_array[px][py]][op_index]: ", self.matching_tile_data[self.tile_array[px][py]][op_index] )
            modified_probabilities = {tile: 1 for tile in self.matching_tile_data[self.tile_array[px][py]][op_index]}

                # for tile in self.matching_tile_data[self.tile_array[px][py]][op_index]:
                #     base_probability = 1
                    # base_probability = self.base_probability[tile][op_index]
                    # tiles_to_check[tile] = 1
                    # tiles_to_check[tile] = round(probability_value * base_probability * percentage * 2.5, 2)
        else:
            # Search for Adjacent Probabilities
            if not self.tiles_array_probabilities[px][py] or probability_value <= 0:
                # print('No nearby tiles, probabilities to choose from or probability value is <= 0')
                return {}, ''  # nothing to return

            tile_type = 'probability'
            # print('tile does not exist yet, extending from probabilities')


            modified_probabilities = {possible_tile: 1 for key in self.tiles_array_probabilities[px][py].keys()
                              for possible_tile in self.matching_tile_data[key][op_index]}

                    # base_probability = self.base_probability[possible_tile][op_index]
                    # tiles_to_check[possible_tile] = round(probability_value * base_probability * percentage, 2)

        # Find Top Probability Values
        # modified_probabilities = tiles_to_check
        return modified_probabilities, tile_type

    def check_decided_neighbors(self, x, y):
        # Check if Surrounding Coordinates are Undecided
        for new_x, new_y in [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]:
            # Check if Neighbor is Already observed(collapsed)
            if not (new_x, new_y) in self.undecided_tiles:
                if self.check_coordinate_within_map(new_x, new_y):
                    return False  # At least (1) tile neighbor has been decided

        return True  # All neighbors are undecided

    def check_coordinate_within_map(self, x, y):
        # (x, y) Must be Within Map
        # print('(%s, %s) Must be Within Map (%s, %s)' % (x, y, self.x_max-1, self.y_max-1))
        if 0 <= x <= self.x_max - 1 and 0 <= y <= self.y_max - 1:
            # print(((x, y), 'is within map.'))
            return True
        return False

    def reset_entropy(self) -> None:
        # print('reset_entropy')
        # Reset to Default Value
        self.lowest_entropy = [(999, 999), 999]

        if self.gui.lbl_stats:
            self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (999, 999, 999)
