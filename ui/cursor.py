from kivy.animation import Animation
from kivy.graphics import Rectangle


class MapCursor(Rectangle):

    def __init__(self, map, map_size, tile_size, hue, **kwargs):
        super(MapCursor, self).__init__(**kwargs)
        self.map = map
        self.tile_size = tile_size
        self.hue = hue  # pass it's own hue to itself
        self.size = (tile_size, tile_size)
        self.cursor_anim_1 = ''
        self.cursor_anim_2 = ''
        self.pos = (0, 0)
        self.map_size = map_size
        self.x_coord = 0
        self.y_coord = 0

        self.hide_cursor()

    def change_map_size(self, x_max, y_max, tile_size):
        self.map_size = (x_max, y_max)
        self.tile_size = tile_size
        # self.pos = (0, 0)
        self.move_cursor(0, 0)

    def increment_x(self, x):
        border_len = self.map.border_len
        x_coord = self.x_coord + x

        if 0 > x_coord:
            return

        if x_coord > self.map_size[0] - 1:
            return

        self.x_coord = x_coord
        self.pos = int(x_coord * (self.tile_size + (1*border_len))), self.pos[1]
        # anim = Animation(
        #     pos=(int(x_coord * (self.tile_size + (1*border_len))), self.pos[1]),
        #     duration=.01)
        # anim.start(self)

    def increment_y(self, y):
        border_len = self.map.border_len
        y_coord = self.y_coord + y

        if 0 > y_coord:
            return

        if y_coord > self.map_size[1] - 1:
            return
        self.y_coord = y_coord
        self.pos = self.pos[0], int(y_coord * (self.tile_size + (1*border_len)))
        # anim = Animation(
        #     pos=(self.pos[0], int(y_coord * (self.tile_size + (1*border_len)))),
        #     duration=.01)
        # anim.start(self)

    def move_cursor(self, touch_x, touch_y):
        touch_x = int(touch_x)
        touch_y = int(touch_y)
        self.x_coord, self.y_coord = touch_x, touch_y
        # self.current_coordinates = (touch_x, touch_y)
        # print('\nCurrent Cursor Position: (%d, %d)' % (self.pos[0]/32, self.pos[1]/32))
        # print('Moving cursor to pos = (%d, %d).' % (touch_x, touch_y))
        anim = Animation(
            pos=(touch_x*self.tile_size, touch_y*self.tile_size),
            duration=.1)
        anim.start(self)

    def move_cursor_by_pos(self, new_pos):
        Animation(pos=new_pos, duration=.1).start(self)

    def begin_cursor_animation(self):
        # Highlighting Widget Animation
        self.reveal_cursor()
        self.cursor_anim_1 = Animation(a=.75, duration=.5)
        self.cursor_anim_2 = Animation(a=0, duration=.5)
        self.cursor_anim_1.bind(on_complete=lambda x, y: self.cursor_anim_2.start(self.hue))
        self.cursor_anim_2.bind(on_complete=lambda x, y: self.cursor_anim_1.start(self.hue))
        self.cursor_anim_1.repeat = False

        if self.cursor_anim_1:
            self.cursor_anim_1.start(self.hue)

    def cancel_cursor_animation(self, dt=0, *args):
        # Cancel Animation
        if isinstance(self.cursor_anim_1, Animation):
            self.cursor_anim_1.cancel(self)
            self.cursor_anim_2.cancel(self)

            self.cursor_anim_1.unbind(on_complete=lambda: self.cursor_anim_2.start(self))
            self.cursor_anim_2.unbind(on_complete=lambda: self.cursor_anim_1.start(self))

            self.cursor_anim_1 = ''
            self.cursor_anim_2 = ''

    def hide_cursor(self, *args):
        self.hue.a = 0

    def reveal_cursor(self, *args):
        self.hue.a = 0.75


class MenuCursor(Rectangle):
    def __init__(self, widget_list, hue, **kwargs):
        super(MenuCursor, self).__init__(**kwargs)

