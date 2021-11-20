from collections import Counter, deque
from random import randint, shuffle
from typing import Dict, Iterable, List, Tuple

import numpy as np

from utils import helper_functions
import pathfinding


class WaveFunctionCollapse:
    x_max: int = 0
    y_max: int = 0
    tile_range: int = 0
    undecided_tiles: Iterable = None
    matching_tile_data: Dict = None  # dictionary of tile numbers and their matching tiles respective to each side
    base_probability: Dict = None  # dict containing tile numbers as keys and connected probabilities per each direction
    tile_array: List[List[int]] = None  # 2D matrix containing tile numbers stored as int
    tiles_array_probabilities: np.ndarray = None  # 2D Numpy Matrix of dicts of every possible tile per coordinate
    # self.lowest_entropy = [(999, 999), 999]
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
        shuffle(self.undecided_tiles)
        self.attempts = 0
        self.tile_chosen_from_weighted_probabilities = 0
        self.tile_chosen_randomly = 0
        self.probability_reset = 0
        self.reset_entropy()

    def find_lowest_entropy(self):
        """
        find_lowest_entropy calculates the lowest value depending how many
        """

        coord_score = [(999, 999), 999]

        # Loop Through all Tiles and Find Lowest Entropy
        for y in range(self.y_max):
            for x in range(self.x_max):
                if self.tiles_array_probabilities[x][y]:
                    # entropy_val = sum(Counter(self.tiles_array_probabilities[x][y].values()))
                    # print("entropy_val: ", entropy_val)
                    possibility_count = len(self.tiles_array_probabilities[x][y].keys())
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

    def weighted_placement(self, dt=0):
        # Weighted Placement with No Backjumping

        # 1. Check if There are Undecided Tiles
        if len(self.undecided_tiles) < 1:
            self.gui.generate_iter = 0
            return

        # 2. Select Tile Index with Lowest Entropy
        x, y = self.lowest_entropy[0]

        # 3. Check if Tile with Lowest Entropy Exists or Pick the Longest Lasting Undecided Tile
        if (x, y) in self.undecided_tiles:
            self.undecided_tiles.remove((x, y))
        else:
            x, y = self.undecided_tiles.popleft()

        # 4. Select Tile based on  Existing Probabilities else Select Random Tile
        new_tile = self.new_tile_based_on_surrounding_tiles(x, y)

        # Random Selection from Neighbors
        if not new_tile:
            if self.check_decided_neighbors(x, y):
                # No Decided Neighbors, Randomly Selecting Tile
                new_tile = randint(1, len(self.gui.tiles.keys()))
                self.tile_chosen_randomly += 1

        # 5. Update Probabilities Based on Tile Selected At Coordinate
        if new_tile:
            # Update Tile Arrays
            self.tile_chosen_from_weighted_probabilities += 1
            self.tile_array[x][y] = new_tile
            self.field.walls.append((x, y))
            if (x, y) in self.undecided_tiles:
                self.undecided_tiles.remove((x, y))
            self.probability_sphere(x, y, new_tile)

        # 6. Finally, place Tile if Tile was Selected
        self.tiles_array_probabilities[x][y] = {}
        if self.lowest_entropy[0] not in self.undecided_tiles or not self.tiles_array_probabilities[self.lowest_entropy[0][0]][self.lowest_entropy[0][1]]:
            self.reset_entropy()
            if self.gui.lbl_stats:
                self.gui.lbl_stats.text = 'Lowest Entropy|(%s, %s): %s' % (999, 999, 0)
        self.find_lowest_entropy()
        if self.lowest_entropy[1] <= 0 and len(self.undecided_tiles) > 0:
            self.lowest_entropy[0] = self.undecided_tiles[0]
        if new_tile:
            self.gui.place_tile(x, y)
        self.gui.generate_iter -= 1

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
        if (x, y) in coordinates_travelled:
            coordinates_travelled.remove((x, y))

        # Update probabilities all around initial tile
        for coordinate in coordinates_travelled:
            # Check if Tile Already Exists for Coordinate
            if self.tile_array[coordinate[0]][coordinate[1]] != 0:
                continue

            (i, j) = coordinate
            probability_list, final_tile_type = self.obtain_probabilities_list(new_tile, i, j, x, y,
                                                                               coordinates_travelled.index(coordinate))

            if len(probability_list) > 0:
                # Set Final Probabilities
                self.tiles_array_probabilities[i][j] = probability_list
            else:
                # No Probability Found
                print("\n### Impossible Tile Found at (%s, %s)###" % (coordinate[0], coordinate[1]))
                print("tile array probabilityes: ", self.tiles_array_probabilities[i][j])
                print("coordinates_travelled: ", coordinates_travelled)
                print("last tile changed: ", self.last_tile_changed)
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
                # print('%s Tile Type: %s' % (direction, tile_type))
                if len(tiles_list.keys()) > 0:
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
            if len(self.tiles_array_probabilities[i][j].keys()) > 0:
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

    # def obtain_probabilities_list(self, new_tile, i, j, x, y, iteration):
    #     probability_tile_list = []
    #     adjacent_tile_list = []
    #     probability_list = []
    #     final_tile_type = ''
    #
    #     direction_list = [(i + 0, j + 1, 'north'),
    #                       (i + 1, j + 0, 'east'),
    #                       (i + 0, j + (-1), 'south'),
    #                       (i + (-1), j + 0, 'west')]
    #     shuffle(direction_list)
    #     for _ in range(4):
    #         px, py, direction = direction_list.pop()
    #         # if x == px and y == py:
    #             # no point in looking at the origin coordinate, that should aleady have a decided tile
    #             # continue
    #         if self.check_coordinate_within_map(px, py):
    #             ind, op_ind = helper_functions.find_opposite(direction)
    #             # helper_functions.super_print('Checking: %s from coordinate: (%s, %s), Iteration: %s' % (direction, i, j, iteration))
    #             tiles_list, tile_type = self.modify_probability(new_tile, op_ind, i, j, x, y, px, py)
    #             # print('%s Tile Type: %s' % (direction, tile_type))
    #             if len(tiles_list.keys()) > 0:
    #                 if tile_type == 'adjacent':
    #                     adjacent_tile_list.append(tiles_list)
    #                     # print('Appending to Adjacent Tile List:', tiles_list)
    #                 elif tile_type == 'probability':
    #                     probability_tile_list.append(tiles_list)
    #                     # print('Appending to Probability Tile List:', tiles_list)
    #
    #     if adjacent_tile_list:
    #         # Keep and Combine Matches Only Between Tiles
    #         if len(self.tiles_array_probabilities[i][j].keys()) > 0:
    #             adjacent_tile_list.append(self.tiles_array_probabilities[i][j])
    #         probability_list = helper_functions.dict_intersect(adjacent_tile_list)
    #         final_tile_type = 'adjacent'
    #     elif probability_tile_list:
    #         # Combine All Probabilities
    #         if len(self.tiles_array_probabilities[i][j].keys()) > 0:
    #             probability_tile_list.append(self.tiles_array_probabilities[i][j])
    #         probability_list = helper_functions.dict_combine(probability_tile_list)
    #         # probability_list = helper_functions.dict_intersect(probability_tile_list)
    #         final_tile_type = 'probability'
    #
    #     # print('Final Tile Type: %s' % final_tile_type)
    #     # print('Final Probabilities:', probability_list)
    #
    #     # print('returning complete probability_list:', probability_list)
    #     return probability_list, final_tile_type

    def new_tile_based_on_surrounding_tiles(self, x, y):
        # Check if Existing Coordinates have any Defined Probabilites
        # Note: In a perfect world, the statement below wouldn't be needed
        if len(self.tiles_array_probabilities[x][y]) < 1:
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
                    # match_list.append(self.matching_tile_data[self.tile_array[px][py]][op_ind].keys())

        # Return Impossible if New Tile isn't in the Matching List

        for m in match_list:
            if new_tile not in m:
                # New Tile Does Not Match Surroundings!
                print("# New Tile Does Not Match Surroundings!")
                print("match_list: ", match_list)
                return None
        # New Tile is a Good Match
        self.last_tile_changed = (x, y)
        # print("last tile changed: ", self.last_tile_changed)
        return new_tile

    def modify_probability(self, new_tile, op_index, i, j, x, y, px, py):
        # Modify Probability at Given Coordinate
        # print('\nModify Probability at (%s, %s) from (%s, %s), from origin: (%s, %s)' % (i, j, px, py, x, y))
        # TODO: return if base_probability_value < 1
        # Obtain Probabilities from Previous Tiles and Propagate
        tiles_to_check = Counter({})
        probability_value = 1
        # probability_value = helper_functions.determine_probability_value(i, j, x, y, self.tile_range)
        if probability_value <= 0:
            return {}, ''

        # Search for Adjacent Tile
        if self.tile_array[px][py] != 0:
            # print('tile already exists, using actual tile:', self.tile_array[px][py])
            tile_type = 'adjacent'
            # print("self.matching_tile_data[self.tile_array[px][py]][op_index]: ", self.matching_tile_data[self.tile_array[px][py]][op_index] )
            try:
                for tile in self.matching_tile_data[self.tile_array[px][py]][op_index]:
                # for tile, percentage in self.matching_tile_data[self.tile_array[px][py]][op_index].items():
                    base_probability = 1
                    # base_probability = self.base_probability[tile][op_index]
                    tiles_to_check[tile] = 1
                    # tiles_to_check[tile] = round(probability_value * base_probability * percentage * 2.5, 2)

                # New Addition
                # for tile in self.tiles_array_probabilities[px][py].keys():
                #     for possible_tile in self.matching_tile_data[tile][op_index]:
                #         base_probability = 1
                #         tiles_to_check[tile] = 1

            except KeyError:
                print("self.tile_array[px][py]: ", self.tile_array[px][py])
                print('matching tile data:', self.matching_tile_data)



        else:
            # Search for Adjacent Probabilities
            if len(self.tiles_array_probabilities[px][py].keys()) < 1 or probability_value <= 0:
                # print('No nearby tiles, probabilities to choose from or probability value is <= 0')
                return {}, ''  # nothing to return

            tile_type = 'probability'
            # print('tile does not exist yet, extending from probabilities')
            for key in self.tiles_array_probabilities[px][py].keys():
                for possible_tile in self.matching_tile_data[key][op_index]:
                # for possible_tile, percentage in self.matching_tile_data[key][op_index].items():
                    base_probability = 1
                    # base_probability = self.base_probability[possible_tile][op_index]
                    # tiles_to_check[possible_tile] = round(probability_value * base_probability * percentage, 2)
                    tiles_to_check[possible_tile] = 1

        # Find Top Probability Values
        modified_probabilities = tiles_to_check
        # modified_probabilities = dict(tiles_to_check.most_common())
        # print('returning:', modified_probabilities)
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
        # Reset to Default Value
        self.lowest_entropy = [(999, 999), 999]
