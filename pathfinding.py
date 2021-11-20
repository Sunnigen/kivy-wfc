# Sample code from http://www.redblobgames.com/pathfinding/
# Copyright 2014 Red Blob Games <redblobgames@gmail.com>
#
# Feel free to use this code in your own projects, including commercial projects
# License: Apache v2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>

from collections import deque
from math import sqrt
from random import randint
import heapq

# utility functions for dealing with square grids


def from_id_width(id_tag, width):
    return id_tag % width, id_tag // width


def draw_tile(graph, id_tag, style, width):
    r = "."
    if 'number' in style and id_tag in style['number']: r = "%d" % style['number'][id_tag]
    if 'iteration' in style and id_tag in style['iteration']:
        r = "%d" % style['iteration'].index(id_tag)
    if 'point_to' in style and style['point_to'].get(id_tag, None) is not None:
        (x1, y1) = id_tag
        (x2, y2) = style['point_to'][id_tag]
        if x2 == x1 + 1: r = "\u2192"  # right_arrow unicode character
        if x2 == x1 - 1: r = "\u2190"  # left_arrow
        if y2 == y1 + 1: r = "\u2193"  # down_arrow
        if y2 == y1 - 1: r = "\u2191"  # up_arrow
    if 'start' in style and id_tag == style['start']: r = "S"
    if 'goal' in style and id_tag == style['goal']: r = "G"
    if 'path' in style and id_tag in style['path']: r = "@"
    if id_tag in graph.walls: r = "#" * width
    return r


def draw_grid_reverse(graph, width=2, **style):
    print('=' * graph.width * 2)
    for y in range(graph.height - 1, -1, -1):
        for x in range(graph.width):
            print("%%-%ds" % width % draw_tile(graph, (x, y), style, width), end="")
        print()
    print('=' * graph.width * 2)


def draw_grid(graph, width=2, **style):
    print('=' * graph.width * 2)
    for y in range(graph.height):
        for x in range(graph.width):
            print("%%-%ds" % width % draw_tile(graph, (x, y), style, width), end="")
        print()
    print('=' * graph.width * 2)


class SquareGrid:
    # actual pathfinding
    # Graph
    # Data structure that can tell me the neighbors for each location
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = []
    
    def in_bounds(self, id):
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id):
        # print('\npassable function called.')
        # print(id)
        return id not in self.walls
    
    def neighbors(self, id_tag):
        (x, y) = id_tag
        results = [(x+1, y), (x, y-1), (x-1, y), (x, y+1)]  # above, below, left and right of id_tag
        if (x + y) % 2 == 0: results.reverse() # aesthetics
        results = filter(self.in_bounds, results) # Check if point is within limitations of graph
        results = filter(self.passable, results) # Check if current coordinate is an obstacle
        
        #print('Neighboring Frontiers(results) = ' + str(list(results))) # results is a generator :(, use it once and it doesn't exist anymore
        return results


class GridWithWeights(SquareGrid):

    # Graph + SquareGrid
    # SquareGrid data structure with weights

    def __init__(self, width, height):
        super().__init__(width, height)
        self.weights = {}

    def cost(self, from_node, to_node):
        # Function will tell us the cost of moving from location(from_node) to its neighbor(to_node)
        return self.weights.get(to_node, 1)


class Queue:

    # Queue
    # Data structure used by the search algorithm to decide the order in which to process the location
    def __init__(self):
        self.elements = deque()
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, x):
        self.elements.append(x)
        # heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return self.elements.popleft()


def distance(start, next_frontier, mov):
    # dist = sqrt((next_frontier[0] - start[0]) ** 2 + (next_frontier[1] - start[1]) ** 2)
    dist = abs(next_frontier[0] - start[0]) + abs(next_frontier[1] - start[1])
    if dist > mov:
        return False
    return True


def breadth_first_search_with_probability(graph, start, mov):

    # Search
    # An algorithm that takes a graph, starting, and (optionally) a goal location,
    # and calculates some useful information(frontiers visited, parent pointer, distance)
    # for some or all locations

    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = None
    cost_so_far = {}
    cost_so_far[start] = 0
    iterations = []
    iterations.append(start)
    number_of_iterations = 0
    
    while not frontier.empty():
        current = frontier.get()
        for next_frontier in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next_frontier)
            if next_frontier not in came_from and distance(start, next_frontier, mov):
                cost_so_far[next_frontier] = new_cost
                frontier.put(next_frontier)
                came_from[next_frontier] = current
                number_of_iterations += 1
                iterations.append(next_frontier)
                # iterations[next_frontier] = number_of_iterations
    return came_from, cost_so_far, iterations


if __name__ == '__main__':

    # Map Constraints
    x_max = 8
    y_max = 8
    mov = 3
    # start = (randint(0, x_max-1), randint(0, y_max-1))
    start = (int(x_max/2), int(y_max/2))
    '''
    OBSTACLES_1 = [from_id_width(id, width=30) for id in
                      [30, 21, 22, 51, 52, 81, 82, 93, 94, 111, 112, 123, 124, 133, 134, 141, 142, 153, 154, 163, 164,
                       171, 172, 173, 174, 175, 183, 184, 193, 194, 201, 202, 203, 204, 205, 213, 214, 223, 224, 243,
                       244, 253, 254, 273, 274, 283, 284, 303, 304, 313, 314, 333, 334, 343, 344, 373, 374, 403, 404,
                       433, 434]]
    '''

    OBSTACLES_1 = []
    OBSTACLES_2 = []
    # Populate With Obstacles
    # for i in range(randint(50, 100)):
    # for i in range(450):
    #     x = randint(0, x_max-1)
    #     y = randint(0, y_max-1)
    #     if not (x, y) in OBSTACLES_2 and not (x, y) == start:
    #         OBSTACLES_2.append((x, y))
    #
    # OBSTACLES = OBSTACLES_1 + OBSTACLES_2

    g = GridWithWeights(x_max, y_max)
    # g.walls = [(1, 1)]
    # g.walls = OBSTACLES_2
    # g.walls = OBSTACLES

    came_from, cost_so_far, iterations = breadth_first_search_with_probability(g, start, mov)  # This does the actual computing.
    # Reverse came from
    new_came_from = {}
    # for key, val in came_from.items():
    #     new_came_from[val] = key
    # print('Came From:', came_from)
    # draw_grid(g, width=2, point_to=came_from, start=start)  # This just draws out the graph
    # print('Cost', cost_so_far)
    # draw_grid(g, width=2, number=cost_so_far, start=start)  # This just draws out the graph
    print('Iterations', iterations)
    draw_grid(g, width=4, iteration=iterations, start=start)  # This just draws out the graph
    # print('point_to:', new_came_from)
