from collections import Counter
from math import sqrt
import random
import string

from numpy.random import choice as WeightedChoice


def distance_value(p0, p1, range_val):
    dist = sqrt(((p0[0] - p1[0]) ** 2) + ((p0[1] - p1[1]) ** 2))
    dist_modifier = range_val - dist
    # print('Distance from origin: (%s, %s), to area: (%s, %s) is %s' % (p1[0], p1[1], p0[0], p0[1], dist))
    # print('range_val = %s' % range_val)
    # print('dist_modifier = %s' % dist_modifier)
    if dist_modifier < 0:
        dist_modifier = 0
    return dist_modifier


def find_opposite(side):
    side = side.lower()
    # North, East, South, West  <-- directions
    # 0, 1, 2, 3  <-- indexes
    # return index with opposite direction
    if side == 'north':
        return 0, 2  # return 'south'
    if side == 'east':
        return 1, 3  # return 'west'
    if side == 'south':
        return 2, 0  # return 'north'
    if side == 'west':
        return 3, 1  # return 'east'


def direction_from_origin(new, origin):
    new_dir = 0
    if new > origin:
        new_dir -= 1
    if new < origin:
        new_dir += 1
    return new_dir


def super_print(s):
    print('\n%s\n=== %s ===\n%s' % ('=' * (len(s) + 8), s.title(), '=' * (len(s) + 8)))


def generate_string(length=6, chars=string.ascii_uppercase + string.digits):
    # Returns random string of letters and number characters
    # string = ''.join(random.choice(chars) for _ in range(length))
    return ''.join(random.choice(chars) for _ in range(length))


# def flatten(seq, container=None):
#     # Flatten arbitrary nesting!
#     # Note: Recursive genius!
#     if container is None:
#         container = []
#
#     for s in seq:
#         try:
#             iter(s)  # check if it's iterable
#         except TypeError:
#             container.append(s)
#         else:
#             flatten(s, container)
#
#     return container


def list_intersect(lists):
    # Matching Values Between Lists
    result = lists[0]
    if len(lists) > 1:
        for l in lists[1:]:
            result = set(result).intersection(l)
    # print('list_intersect result:', result)
    return list(result)


def dict_combine(dicts):
    # Combine Dictionaries
    results = Counter()
    for dictionary in dicts:
        results += Counter(dictionary)
    return results


def dict_intersect(dicts):
    # return dicts[0]
    # Increment and Find Common Keys Between Dictionaries
    # print("number of dicts: ", len(dicts))

    comm_keys = dicts[0].keys()
    for d in dicts[1:]:
        # intersect keys first
        comm_keys &= d.keys()
    # then build a result dict with nested comprehension
    # result = {key:{d[key] for d in dicts} for key in comm_keys}
    results = {}
    for key in comm_keys:
        # base_probability = self.base_probability[str(key)][side]
        for d in dicts:
            # if key in results:
            #     results[key] += d[key]
            # else:
            #     results[key] = d[key]
            results[key] = d[key]
    return results


def weighted_choice(dict):
    # Normalize List of Probabilities
    keys = list(dict.keys())
    values = list(dict.values())
    probabilities = []
    total = sum(values)

    if total == 0:
        print('No tile can be found due to small probabilities!')
        return 1
    for val in values:
        # Remove Possibility if Less than Half
        # if val <= total/2:
        #     index = values.index(fval)
        #     keys.pop(index)
        # else:
        try:
            probabilities.append(val/total)
        except:
            print("Error in calculating probabilities!!!")
            print('val/total: %s/%s' % (val, total))
            val = 0.01
            total = len(dict.keys())
            probabilities.append(val/total)
    # print('keys:', keys)
    # print('probabilities:', probabilities)
    result = WeightedChoice(keys, p=probabilities)
    # print("keys: ", keys)
    return random.choice(keys)


def determine_probability_value(x, y, origin_x, origin_y, tile_range):
    return 1

    # How Far Selected Tile is from Origin Tile
    value = distance_value((x, y), (origin_x, origin_y), tile_range)
    return value