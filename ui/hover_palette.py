from collections import OrderedDict
from functools import partial

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
# from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout

Builder.load_string("""

<Palette>:
    selected_lbl:_selected_lbl
    scroll:_scroll
    prob_layout:_prob_layout
    btn_close:_btn_close

    canvas:
        Color:
            rgba: 1, 0, 0, .5
        Rectangle:
            size: self.size
            pos: self.pos
            
    BoxLayout:
        orientation: 'vertical'
        size_hint: 1.0, None
        size: root.size
        # pos_hint: {'center:x': 0.5, 'center_y': 0.5}
        pos: root.pos
            
        Label:
            id :_selected_lbl
            size_hint: 1.0, 0.2
            text_size: self.size
            markup: True
            valign: 'middle'
            halign: 'left'
            text: ''
                
        ScrollView:
            id: _scroll
            size_hint: 1, 0.8
            # size: self.size
            pos_hint: {'center:x': 0.5, 'center_y': 0.5}
            
            GridLayout:
                id: _prob_layout
                cols: 1
                spacing: 0
                size_hint: 1, None
                
    Button:
        id: _btn_close
        text: 'Close'
        on_press: root.close()
        # pos_hint: {'x':0.05, 'top':.95}
        size_hint: 0.2, 0.1

""")


class TileLabel(Label):
        def __init__(self, tile_name, **kwargs):
            super(TileLabel, self).__init__(**kwargs)
            self.tile_name = tile_name


class HoverBehavior(object):
    """Hover behavior.

    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget
    """

    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)
    '''Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_mouse_enter')
        self.register_event_type('on_mouse_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        #Window.bind(mouse_pos=self.on_mouse_leave)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.parent:
            Window.unbind(mouse_pos=self.on_mouse_pos)

        if not self.get_root_window():
            return # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        # Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            # We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_mouse_enter')
        else:
            self.dispatch('on_mouse_leave')

    def on_mouse_enter(self):
        pass

    def on_mouse_leave(self):
        pass


Factory.register('HoverBehavior', HoverBehavior)


class Palette(ButtonBehavior, FloatLayout, HoverBehavior):

    label_cursor = ObjectProperty(None)
    label_selected = ObjectProperty(None)
    selected_lbl = ObjectProperty(None)
    prob_layout = ObjectProperty(None)
    scroll = ObjectProperty(None)
    btn_close = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Palette, self).__init__(**kwargs)
        # self.in_animation = Animation(pos_hint={'x': .75}, duration=.10)  #, t='in_expo')
        # self.out_animation = Animation(pos_hint={'x': .995}, duration=.10)  #, t='in_expo')
        self.palette_type = ''
        self.in_animation = None
        self.out_animation = None
        self.rect_list = []
        self.rect_lbl = []
        self.cursor = None
        # TODO: Find a way to obtain general tile size/modify size of scroll label in relation to specific tile size
        self.displayed_tile_size = (27, 27)  # modify this as required\


    def initialize_cursor(self):
        # self.cursor = MapCursor
        pass

    def initialize_palette(self):
        with self.selected_lbl.canvas:
            self.lbl_rect = Rectangle(size=self.displayed_tile_size)
        self.bind(pos=partial(self.update_lbl_rect, self.selected_lbl, self.lbl_rect),
                  size=partial(self.update_lbl_rect, self.selected_lbl, self.lbl_rect))
        # self.size = self.size
        # self.update_lbl_rect(self.selected_lbl, self.lbl_rect)
        Clock.schedule_once(self.refresh_lbl, 0.05)
        self.on_mouse_enter()
        self.on_mouse_leave()

    def load_tile_palette(self, tiles, probability):
        # print('\nload_tile_palette')
        self.clear_prob_palette()
        self.selected_lbl.text = 'File: %s\nThere are %s tiles.' % (self.parent.tile_set_file, len(tiles.keys()))
        self.selected_lbl.halign = 'center'
        ordered_tiles = OrderedDict(sorted(tiles.items(), key=lambda t: int(t[0])))
        for key, tex in ordered_tiles.items():
            # print(key, tex)
            tile_probability = round(
                (probability[key][0] + probability[key][1] + probability[key][2] + probability[key][3]) * 100 * 0.25, 2)
            lbl = TileLabel(
                text='Tile: %s(%s%%)' % (key, tile_probability),
                size_hint=(1, None),
                width=200,
                height=30,
                tile_name=key
            )
            lbl.text_size = lbl.size
            lbl.markup = True
            lbl.valign = 'middle'
            lbl.halign = 'left'

            # tex_size = tex[0].size

            with lbl.canvas:
                lbl_rect_prob = Rectangle(size=self.displayed_tile_size, texture=tex)
                # lbl_rect_prob.texture.mag_filter = 'nearest'
                # lbl_rect_prob.texture.mag_filter = choice(['linear', 'nearest'])
                # lbl_rect_prob.texture.mag_filter = choice(
                #     ['linear', 'nearest', 'linear_mipmap_filter', 'linear_mipmap_nearest', 'nearest_mipmap_nearest',
                #      'nearest_mipmap_linear']
                # )

            self.bind(pos=partial(self.update_lbl_rect, lbl, lbl_rect_prob),
                      size=partial(self.update_lbl_rect, lbl, lbl_rect_prob))
            self.rect_list.append(lbl_rect_prob)
            self.rect_lbl.append(lbl)

            self.prob_layout.add_widget(lbl)

            # self.update_lbl_rect(lbl, lbl_rect_prob)
            Clock.schedule_once(self.refresh_lbl, 0.01)
        self.prob_layout.bind(minimum_height=self.prob_layout.setter('height'))

    def update_palette(self, x, y, tile, tile_tex, tile_prob):
        # print('\ntile, tile_tex, tile_prob, tile_prob_tex')
        # print(tile)
        # print(tile_prob)
        self.clear_prob_palette()
        self.selected_lbl.text = 'Tile: %s\nAt: (%s, %s)' % (tile, x, y)
        self.lbl_rect.texture = tile_tex
        # with self.selected_lbl.canvas:
        for key, val_list in tile_prob.items():
            prob = val_list[0]
            rect_texture = val_list[1]
            lbl = Label(
                text='Tile: %s\nProb: %s' % (key, prob),
                # size_hint=(1, 1)
                size_hint=(None, None),
                width=150,
                height=80
            )
            lbl.text_size = lbl.size
            lbl.markup = True
            lbl.valign = 'middle'
            lbl.halign = 'left'

            with lbl.canvas:
                lbl_rect_prob = Rectangle(size=self.displayed_tile_size, texture=rect_texture)
                # lbl_rect_prob.texture.mag_filter = 'nearest'

            self.bind(pos=partial(self.update_lbl_rect, lbl, lbl_rect_prob),
                      size=partial(self.update_lbl_rect, lbl, lbl_rect_prob))
            self.rect_list.append(lbl_rect_prob)
            self.rect_lbl.append(lbl)
            self.prob_layout.add_widget(lbl)

            # self.update_lbl_rect(lbl, lbl_rect_prob)
            Clock.schedule_once(self.refresh_lbl, 0.01)
        self.prob_layout.bind(minimum_height=self.prob_layout.setter('height'))

    def refresh_lbl(self, dt=0):
        if len(self.rect_lbl) > 0:
            for i in range(len(self.rect_lbl)):
                self.update_lbl_rect(self.rect_lbl[i], self.rect_list[i])
        self.update_lbl_rect(self.selected_lbl, self.lbl_rect)

    def clear_prob_palette(self):
        self.selected_lbl.text = ''
        self.rect_list = []
        self.rect_lbl = []
        self.prob_layout.clear_widgets()

    def on_opacity(self, *args, **kwargs):
        # Hide GUI if BattleField is not Focused
        # print('hover gui opacity: %d' % self.opacity)
        if self.opacity < 1:
            # print('hiding h9overlayout')
            self.out_animation.start(self)

    def on_mouse_enter(self, *args):
        if not self.disabled and self.parent.opacity == 1 and self.in_animation:
            # print("You are in, through this point", self.border_point)
            self.in_animation.start(self)
            pass

    def on_mouse_leave(self, *args):
        if not self.disabled and self.parent.opacity == 1:
            # print("You left through this point", self.border_point)
            # self.out_animation.start(self)
            pass

    def close(self, *args):
        if self.out_animation:
            self.out_animation.start(self)

    def on_press(self, *args):
        # print('%s has been pressed' % self.__class__)

        pass

    def on_release(self, *args):
        # print('%s has been released' % self.__class__)
        pass

    def on_touch_down(self, touch):
        if not self.disabled and self.collide_point(*touch.pos):
            # print('Palette Type:', self.palette_type)
            # print('%s touch down received' % self.__class__)
            # if not self.disabled and self.parent.opacity == 1:
            #     self.out_animation.start(self)
            # if self.palette_type == 'tile':
            #     for lbl in self.rect_lbl:
            #         if lbl.collide_point(*touch.pos):
            #             index = self.rect_lbl.index(lbl)
            #             tex = self.rect_list[index]
            #             print('Touched:', lbl.text, tex)


            # print('Window Touch:', touch.pos)
            # print('Parent Touch:', self.scroll.to_parent(*touch.pos))
            # print('Local Touch:', self.scroll.to_local(*touch.pos))

            if (touch.is_double_tap and touch.button == 'left'):
                if self.palette_type == 'tile' and self.scroll.collide_point(*touch.pos):
                    local_pos = self.scroll.to_local(*touch.pos)
                    for lbl in self.rect_lbl:
                        if lbl.collide_point(*local_pos):
                            self.parent.wang_tiles_map.force_specific_tile(lbl.tile_name)
                            self.scroll.scroll_to(lbl)  # ensure tile is seems from scroll menu
                            return True

            if touch.button == 'right':
                # print('right click on hover palette!')
                if self.palette_type == 'tile' and self.scroll.collide_point(*touch.pos):
                    local_pos = self.scroll.to_local(*touch.pos)
                    for lbl in self.rect_lbl:
                        if lbl.collide_point(*local_pos):
                            # index = self.rect_lbl.index(lbl)
                            # tex = self.rect_list[index]
                            print('Tile %s tile probabilities.' % lbl.tile_name)
                            self.scroll.scroll_to(lbl)
                            self.parent.modify_probability_popup(lbl)
                            return True

            return super(self.__class__, self).on_touch_down(touch)

    def unload_self(self, dt=0):
        Window.unbind(mouse_pos=self.on_mouse_pos)
        self.parent.remove_widget(self)

    def update_lbl_rect(self, label, rect, *args):
        # correct_pos = label.to_parent(*label.center)
        # rect.pos = (correct_pos[0] + (rect.size[0]), correct_pos[1] - (rect.size[1]/2))
        rect.pos = (label.center[0] + (rect.size[0]), label.center[1] - (rect.size[1]/2))
        # print("update_lbl_rect pos:", rect.pos)
