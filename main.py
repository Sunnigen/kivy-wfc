import os
import re

from kivy.animation import Animation
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')  # disables right click multitouch function


from ui.map import Map
from ui.popups import *


Builder.load_file('main.kv')


class MyButton(Button):
    def __init__(self, **kwargs):
        self._callbacks = []
        super(MyButton, self).__init__(**kwargs)


class NumericInput(TextInput):
    pat = re.compile('[^0-9]')

    def __init__(self, **kwargs):
        self.pos_hint = {'center_y': 0.5}
        self.size_hint_y = 0.5
        self.multiline = False
        super(NumericInput, self).__init__(**kwargs)

        # self.padding_x = [
        #     self.center[0] - self._get_text_width(max(self._lines, key=len), self.tab_width, self._label_cached) / 2.0,
        #     0] if self.text else [self.center[0], 0]
        # # top, bottom
        # self.padding_y = [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        # if '.' in self.text:
        #     s = re.sub(pat, '', substring)
        # else:
        for s in substring.split('.', 1):
            s = re.sub(pat, '', s)
        # print('\n')
        # print(s)
        # print('substring:', substring)
        if len(self.text) > 1:
            return

        return super(NumericInput, self).insert_text(s, from_undo=from_undo)


class DecimalNumericInput(TextInput):
    pat = re.compile('[^0-9]')

    def __init__(self, **kwargs):
        self.pos_hint = {'center_y': 0.5}
        self.size_hint_y = 0.5
        self.multiline = False
        super(DecimalNumericInput, self).__init__(**kwargs)

        # self.padding_x = [
        #     self.center[0] - self._get_text_width(max(self._lines, key=len), self.tab_width, self._label_cached) / 2.0,
        #     0] if self.text else [self.center[0], 0]
        # # top, bottom
        # self.padding_y = [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(DecimalNumericInput, self).insert_text(s, from_undo=from_undo)


class Content(FloatLayout):
    lbl_stats = ObjectProperty(None)
    lbl_current = ObjectProperty(None)
    prob_palette = ObjectProperty(None)
    tile_palette = ObjectProperty(None)
    generation_switch = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Content, self).__init__(**kwargs)
        # self.tile_set_file = 'wang_tiles_classic.pickle'
        # self.tile_set_file = 'grass_water_simple.pickle'
        # self.tile_set_file = 'test1.pickle'
        # self.tile_set_file = 'fe_0.pickle'
        self.tile_set_file = 'fe_32x.pickle'
        # self.tile_set_file = 'fe_19.pickle'
        # self.tile_set_file = 'fe_25H.pickle'
        # self.tile_set_file = 'fe_11H.pickle'
        # self.tile_set_file = 'fe_1.pickle'
        # self.tile_set_file = 'grass_corner.pickle'
        # self.tile_set_file = 'grass_water.pickle'
        # self.tile_set_file = 'dungeon_simple.pickle'

        # self.tile_palette.in_animation = Animation(pos_hint={'right': .25}, duration=.10)
        # self.tile_palette.out_animation = Animation(pos_hint={'right': .005}, duration=.10)
        # self.tile_palette.btn_close.pos_hint = {'right': 1, 'top': 1.0}
        # self.tile_palette.btn_close.size_hint = 0.3, 0.05

        self.prob_palette.in_animation = Animation(pos_hint={'x': .8}, duration=.10)
        self.prob_palette.out_animation = Animation(pos_hint={'x': .995}, duration=.10)
        self.prob_palette.btn_close.pos_hint = {'right': 1, 'top': 1}
        self.prob_palette.btn_close.size_hint = 0.3, 0.05

        self.x_max = 20
        self.y_max = 20
        self.tile_size = 16
        self.displayed_size = 32
        # self.displayed_size = 27

        self.wang_tiles_map = Map(self.x_max, self.y_max, self.tile_size, tile_set_file=self.tile_set_file)
        self.add_widget(self.wang_tiles_map, index=99)
        # Pass Widgets to Wang Tile Map
        self.pass_widgets()

        if self.tile_set_file:
            self.load_initial_tileset()

        self.wang_tiles_map.wfc.force_weighted_placement()

    def generate(self, count):
        if self.wang_tiles_map:
            # self.wang_tiles_map.random_generation(self.x_max, self.y_max, self.tile_size)
            # self.wang_tiles_map.generate_tiles(count)
            self.wang_tiles_map.generate_iter += int(count)

    def print_stats(self):
        if self.wang_tiles_map:
            self.wang_tiles_map.print_stats()

    def reset_map_texture(self):
        if self.wang_tiles_map:
            self.wang_tiles_map.reset_map_texture()

    def continuous_generation(self, widget, state):
        # print('continuous_generation')
        # print('\n', widget, widget.active)
        if state:
            # print('starting generation')
            self.wang_tiles_map.continuous_generation = True
        else:
            # print('ceasing generation')
            self.wang_tiles_map.continuous_generation = False

    # def force_tile(self):
    #     if self.wang_tiles_map:
    #         self.wang_tiles_map.force_tile()

    # def random_tiles(self):
    #     if self.wang_tiles_map:
    #         self.wang_tiles_map.place_random_tile()

    def load_initial_tileset(self, *args):
        if self.wang_tiles_map:
            self.wang_tiles_map.load_tile_set_data()

    def selected_tileset(self, instance, selected_file, *args):
        # print('Directory Path:', os.path.dirname(os.path.realpath(__file__)))
        # print('Instance: %s' % instance)
        # Change Tileset Used
        print('Selected File: %s' % selected_file)
        if self.wang_tiles_map:
            self.wang_tiles_map.load_tile_set_data(selected_file[0])
            self.reset_map_texture()

    def modify_probability_popup(self, lbl):
        if self.wang_tiles_map:
            self.wang_tiles_map.disable_user_interaction()
        tile = lbl.tile_name
        popup = TileProbability()
        probability_list = self.wang_tiles_map.wfc.base_probability[tile]
        # print('Loading initial probabilities for Tile: %s' % tile, probability_list)

        popup_content = BoxLayout(orientation='vertical', size_hint=(1, 1,))
        direction_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.25))
        direction_box.add_widget(Label(text='North Tiles'))
        direction_box.add_widget(Label(text='East Tiles'))
        direction_box.add_widget(Label(text='South Tiles'))
        direction_box.add_widget(Label(text='West Tiles'))

        probability_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.50))
        probability_box.add_widget(DecimalNumericInput(text=str(probability_list[0])))
        probability_box.add_widget(DecimalNumericInput(text=str(probability_list[1])))
        probability_box.add_widget(DecimalNumericInput(text=str(probability_list[2])))
        probability_box.add_widget(DecimalNumericInput(text=str(probability_list[3])))

        btn_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.50))
        btn_apply = Button(text='Save')
        btn_double = Button(text='Double')
        btn_reset = Button(text='Reset')
        btn_reduce = Button(text='Reduce')
        btn_reduce.bind(on_press=partial(self.reduce_probabilities, probability_box.children))
        btn_double.bind(on_press=partial(self.double_probabilities, probability_box.children))
        btn_reset.bind(on_press=partial(self.reset_probabilies, probability_list, probability_box.children))
        btn_apply.bind(on_press=partial(self.modify_probability_list, tile, probability_box.children, lbl, popup))
        btn_box.add_widget(btn_reset)
        btn_box.add_widget(btn_reduce)
        btn_box.add_widget(btn_double)
        btn_box.add_widget(btn_apply)

        popup_content.add_widget(direction_box)
        popup_content.add_widget(probability_box)
        popup_content.add_widget(btn_box)

        popup.content = popup_content
        popup.bind(on_dismiss=self.wang_tiles_map.enable_user_interaction)
        popup.open()

    def display_matching_tiles(self):
        # Check if Wang Tiles Map in Place
        if self.wang_tiles_map:
            self.wang_tiles_map.disable_user_interaction()
        else:
            print('Wang Tiles Map does not exist!')
            return
        popup_content = FloatLayout(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        if len(self.wang_tiles_map.tiles.keys()) < 1:
            print('No tiles found in Wang Tiles Map!')
            print('Tiles:', self.wang_tiles_map.tiles)
            return
        # Add Widgets
        popup = MatchingTiles(content=popup_content)
        main_tile = Label(
            pos_hint={'x': 0, 'top': 1.0},
            size_hint=(None, None),
            size=(200, 33),
            text='_',
            markup=True,
            valign='middle',
            halign='left'
        )
        main_tile.text_size = main_tile.size
        with main_tile.canvas:
            main_tile_rect = Rectangle(pos=(main_tile.pos[0] + 25, main_tile.pos[1]),size=(self.displayed_size, self.displayed_size))
        self.bind(pos=partial(self.update_lbl_rect, main_tile, main_tile_rect),
                  size=partial(self.update_lbl_rect, main_tile, main_tile_rect))

        grid = GridLayout(rows=4, spacing=0, size_hint=(None, 1.0), pos_hint={'x': 0.0, 'y': 0.0})
        north_lbl = Label(text='North\nMatches:', pos_hint={'x': 0, 'top': 0.8}, size_hint=(0.25, 0.2))
        east_lbl = Label(text='East\nMatches:', pos_hint={'x': 0, 'top': 0.6}, size_hint=(0.25, 0.2))
        south_lbl = Label(text='South\natches:', pos_hint={'x': 0, 'top': 0.4}, size_hint=(0.25, 0.2))
        west_lbl = Label(text='West\nMatches:', pos_hint={'x': 0, 'top': 0.2}, size_hint=(0.25, 0.2))
        popup_content.add_widget(north_lbl)
        popup_content.add_widget(east_lbl)
        popup_content.add_widget(south_lbl)
        popup_content.add_widget(west_lbl)

        north_box = BoxLayout(size_hint=(1, 0.25), orientation='horizontal')
        east_box = BoxLayout(size_hint=(1, 0.25), orientation='horizontal')
        south_box = BoxLayout(size_hint=(1, 0.25), orientation='horizontal')
        west_box = BoxLayout(size_hint=(1, 0.25), orientation='horizontal')
        grid.bind(minimum_width=grid.setter('width'))

        scrollview = ScrollView(size_hint=(0.8, 0.8), size=popup.size, do_scroll_x=True, do_scroll_y=False, pos_hint={'x':0.2, 'y':0})
        scrollview.add_widget(grid)
        popup_content.add_widget(scrollview)

        # Modify Specific Tile Probability
        layout_change_prob = FloatLayout(size_hint=(1, None), size=(self.parent.width, 51), pos_hint={'x': 0.0, 'top': 0.9})
        lbl_prob = Label(
            pos_hint={'x': 0, 'top': 0.9},
            size_hint=(None, None),
            size=(200, 33),
            text='_',
            markup=True,
            valign='middle',
            halign='left'
        )
        lbl_prob.text_size = lbl_prob.size
        with lbl_prob.canvas:
            lbl_prob_rect = Rectangle(pos=(lbl_prob.pos[0] + 25, lbl_prob.pos[1]),size=(self.displayed_size, self.displayed_size))
        self.bind(pos=partial(self.update_lbl_rect, lbl_prob, lbl_prob_rect),
                  size=partial(self.update_lbl_rect, lbl_prob, lbl_prob_rect))
        input_prob = DecimalNumericInput(size_hint=(0.25, 1.0), pos_hint={'center_y': 0.5, 'right': 0.9})
        btn_change_prob = MyButton(pos_hint={'center_y': 0.5, 'right': 1.0}, size_hint=(0.1, 1), text='Modify')
        # btn_change_prob.bind(on_press=partial(self.change_tile_probability, lbl_prob, main_tile.text, input_prob.text))
        #  lbl, origin_tile, tile, index, new_value
        layout_change_prob.add_widget(input_prob)
        layout_change_prob.add_widget(lbl_prob)
        layout_change_prob.add_widget(btn_change_prob)
        popup_content.add_widget(layout_change_prob)

        # Spinner to Select Specific Tile
        # spinner = Spinner(
        #     pos_hint={'right': 1.0, 'top': 1.0},
        #     size_hint=(None, None),
        #     size=(100, 33),
        #     values=sorted(self.wang_tiles_map.tiles.keys())
        # )
        # spinner.bind(text=partial(self._update_match_spinner, main_tile, main_tile_rect, grid, north_box, east_box, south_box, west_box, btn_change_prob, input_prob, lbl_prob, lbl_prob_rect))

        dropdown = DropDown(
            # pos_hint={'right': 1.0, 'top': 1.0},
            size_hint=(None, None),
            size=(100, 33),
        )

        for val in sorted(self.wang_tiles_map.tiles.keys()):
            lbl_drop = Button(text=val, size_hint_y=None, height=44)

            with lbl_drop.canvas:
                lbl_drop_rect = Rectangle(pos=(lbl_drop.pos[0] + 10, lbl_drop.pos[1]),
                                     size=(self.displayed_size, self.displayed_size))
            grid.bind(pos=partial(self.update_lbl_rect, lbl_drop, lbl_drop_rect),
                      size=partial(self.update_lbl_rect, lbl_drop, lbl_drop_rect))
            lbl_drop_rect.texture = self.wang_tiles_map.tiles[val]
            lbl_drop.bind(on_release=lambda lbl_drop: dropdown.select(lbl_drop.text))
            dropdown.add_widget(lbl_drop)
            Clock.schedule_once(partial(self.update_lbl_rect, lbl_drop, lbl_drop_rect), .05)

        dropdown.bind(
            on_select=partial(self._update_match_spinner, main_tile, main_tile_rect, grid, north_box, east_box, south_box,
                         west_box, btn_change_prob, input_prob, lbl_prob, lbl_prob_rect))
        dropdownbtn = Button(text='Tiles!', pos_hint={'right': 1.0, 'top': 1.0},
            size_hint=(None, None),
            size=(100, 33)
                             )
        dropdownbtn.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(dropdownbtn, 'text', x))
        popup_content.add_widget(main_tile)
        # popup_content.add_widget(spinner)
        popup_content.add_widget(dropdown)
        popup_content.add_widget(dropdownbtn)
        popup.bind(on_dismiss=self.wang_tiles_map.enable_user_interaction)
        popup.open()
        Clock.schedule_once(partial(self.update_lbl_rect, main_tile, main_tile_rect), 0.05)
        Clock.schedule_once(partial(self.update_lbl_rect, lbl_prob, lbl_prob_rect), 0.05)

    def _update_match_spinner(self, main_tile, main_tile_rect, grid, north_box, east_box, south_box, west_box, btn_change_prob, input_prob, lbl_prob, lbl_prob_rect, spinner, value):

        # Update Main Tile
        main_tile.text = value
        main_tile_rect.texture = self.wang_tiles_map.tiles[value]
        # print(north_box, east_box, south_box, west_box)

        # Update Matching Tile Display
        grid.clear_widgets()
        north_box.clear_widgets()
        east_box.clear_widgets()
        south_box.clear_widgets()
        west_box.clear_widgets()

        north_tiles = self.wang_tiles_map.wfc.matching_tile_data[value][0]
        east_tiles = self.wang_tiles_map.wfc.matching_tile_data[value][1]
        south_tiles = self.wang_tiles_map.wfc.matching_tile_data[value][2]
        west_tiles = self.wang_tiles_map.wfc.matching_tile_data[value][3]

        # print('\nMatching Tiles for %s:' % value)
        # print(north_tiles)
        # print(east_tiles)
        # print(south_tiles)
        # print(west_tiles)
        # for tile in no
        max_index = max([len(north_tiles), len(east_tiles), len(south_tiles), len(west_tiles)])

        lbl_array = [[None for col in range(max_index)] for row in range(4)]
        row = -1
        for tiles in [north_tiles, east_tiles, south_tiles, west_tiles]:
            # for key, val_prob in tiles.items():
            matching_keys = list(tiles.keys())
            matching_vals = list(tiles.values())
            row += 1
            for i in range(max_index):
                # print('tiles:', tiles)
                if i < len(matching_keys):
                    tile = matching_keys[i]
                    prob = matching_vals[i]
                else:
                    tile = ''
                    prob = ''

                lbl = Label(size_hint_x=None, width=100)
                if tile:
                    lbl.text = 'Tile: %s\n%s%%' % (tile, prob*100)
                    with lbl.canvas:
                        lbl_rect = Rectangle(pos=(lbl.pos[0] + 25, lbl.pos[1]),
                                             size=(self.displayed_size, self.displayed_size))
                    grid.bind(pos=partial(self.update_lbl_rect, lbl, lbl_rect),
                              size=partial(self.update_lbl_rect, lbl, lbl_rect))
                    lbl_rect.texture = self.wang_tiles_map.tiles[tile]

                    Clock.schedule_once(partial(self.update_lbl_rect, lbl, lbl_rect), .05)
                    lbl.bind(on_touch_down=partial(self.lbl_test, tile, prob, input_prob, lbl_prob, lbl_prob_rect, main_tile, row, btn_change_prob))
                # lbl_array[row][i] = lbl
                grid.add_widget(lbl)

    # def lbl_test(self, tile, prob, input_prob, lbl_prob, lbl_prob_rect, main_tile, row, btn_change_prob, dir_lbl, touch, *args):
    #
    #     if dir_lbl.collide_point(*touch.pos):
    #         # print('\nlbl_test')
    #         lbl_prob.text = 'Tile %s: %s%%' % (tile, prob * 100)
    #         lbl_prob_rect.texture = self.wang_tiles_map.tiles[tile]
    #         input_prob.text = str(prob)
    #         # print('tile:', tile)
    #         # print('prob:', prob)
    #         # print('call backs before:', btn_change_prob._callbacks)
    #         if len(btn_change_prob._callbacks) > 0:
    #             for cb in btn_change_prob._callbacks:
    #                 btn_change_prob.unbind(on_press=cb)
    #                 btn_change_prob._callbacks.remove(cb)
    #
    #         partial_cb = partial(self.change_tile_probability, main_tile.text, tile, row, input_prob, lbl_prob, dir_lbl)
    #         btn_change_prob.bind(on_press=partial_cb)
    #         btn_change_prob._callbacks.append(partial_cb)
    #         # print('call backs after:', btn_change_prob._callbacks)

    def change_tile_probability(self, origin_tile, tile, index, input, lbl_prob, dir_lbl, *args):
        print("change_tile_probability")
        # print('Origin Tile:', origin_tile, 'Tile:', tile, 'Index:', index, 'Input Val:', input.text)
        # print('self.wang_tiles_map.matching_tile_data[origin_tile][index]:',
        #       self.wang_tiles_map.matching_tile_data[origin_tile][index])
        self.wang_tiles_map.matching_tile_data[origin_tile][index][tile] = float(input.text)
        dir_lbl.text = 'Tile: %s\n%s%%' % (tile, float(input.text)*100)
        lbl_prob.text =  'Tile %s: %s%%' % (tile, float(input.text)*100)
        # print('Tile: %s\n%s%%' % (tile, float(input.text)*100))
        # print('self.wang_tiles_map.matching_tile_data[origin_tile][index]:',
        #       self.wang_tiles_map.matching_tile_data[origin_tile][index])

    def modify_probability_list(self, tile, numeric_textinputs, lbl, popup, *args):
        # print('\nmodify_probability_list')
        # print(tile, numeric_textinputs, args)
        self.dismiss_popup(popup)
        new_probability_list = []
        tile_probability = 0
        for child in numeric_textinputs:
            new_probability_list.append(float(child.text))
            tile_probability += float(child.text)

        # print('tile %s' % tile, new_probability_list)

        if self.wang_tiles_map:
            self.wang_tiles_map.wfc.base_probability[tile] = new_probability_list
            tile_probability = round(tile_probability * 100 * 0.25, 2)

            lbl.text = 'Tile: %s(%s%%)' % (tile, tile_probability)
            # self.tile_palette.load_tile_palette(self.wang_tiles_map.tiles, self.wang_tiles_map.base_probability)

    # def probability_change(self, *args):
    #     # Save All Changes to Probabilities
    #     if self.wang_tiles_map:
    #         self.wang_tiles_map.save_probabilities()

    def reduce_probabilities(self, inputs, *args):
        for input in inputs:
            if len(input.text) > 0:
                input.text = str(float(input.text)/2)

    def double_probabilities(self, inputs, *args):
        for input in inputs:
            if len(input.text) > 0:
                input.text = str(float(input.text)*2)

    def reset_probabilies(self, probability_list, numeric_textinputs, *args):
        # print('\nmodify_probability_list')
        # print(probability_list, numeric_textinputs, args)
        index = 0
        for child in numeric_textinputs:
            # print('child.text', child.text)
            child.text = str(probability_list[index])
            index += 1

    def tileset_popup(self, *args):
        if self.wang_tiles_map:
            self.wang_tiles_map.disable_user_interaction()

        popup_content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(
            filters=['*.pickle'],
            rootpath=os.path.dirname(os.path.realpath(__file__)) + "/data"
        )
        file_chooser.bind(on_submit=self.selected_tileset)
        # file_chooser.bind(on_submit=self.dismiss_popup)

        popup_content.add_widget(file_chooser)
        popup = TilesetChooser(content=popup_content)
        popup.bind(on_dismiss=self.wang_tiles_map.enable_user_interaction)
        popup.open()

    def map_size_popup(self):
        if self.wang_tiles_map:
            self.wang_tiles_map.disable_user_interaction()

        popup_content = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1)
        )
        box = BoxLayout(orientation='horizontal', spacing=30)
        self.x_max_input = NumericInput(text=str(self.x_max))
        self.y_max_input = NumericInput(text=str(self.y_max))
        box.add_widget(self.x_max_input)
        box.add_widget(self.y_max_input)
        popup_content.add_widget(box)

        btn = Button(text=('Change'))
        popup_content.add_widget(btn)
        popup = MapSizePopup(content=popup_content)
        btn.bind(on_press=partial(self.change_map_size, self.x_max_input, self.y_max_input))
        btn.bind(on_press=partial(popup.dismiss))
        popup.bind(on_dismiss=self.wang_tiles_map.enable_user_interaction)
        popup.open()

    def dismiss_popup(self, popup_widget, *args):
        popup_widget.dismiss()
        if self.wang_tiles_map:
            self.wang_tiles_map.enable_user_interaction()

    def toggle_border(self, *args):
        self.wang_tiles_map.toggle_border()

    def change_map_size(self, x_max, y_max, instance):
        if len(x_max.text) < 1:
            print('Fill in x_max!')
            return
        if len(y_max.text) < 1:
            print('Fill in y_max!')
            return

        self.x_max = x_max.text
        self.y_max = y_max.text

        if self.wang_tiles_map:
            self.wang_tiles_map.change_map_size(int(x_max.text), int(y_max.text), self.tile_size)

    def pass_widgets(self):
        if self.wang_tiles_map:
            # pass widgets to help identify tiles
            self.wang_tiles_map.lbl_stats = self.lbl_stats
            self.wang_tiles_map.lbl_current = self.lbl_current
            self.wang_tiles_map.prob_palette = self.prob_palette
            # self.wang_tiles_map.tile_palette = self.tile_palette

            self.prob_palette.initialize_palette()
            # self.tile_palette.initialize_palette()

    def update_lbl_rect(self, label, rect, *args):
        rect.pos = (label.center[0] + (rect.size[0]), label.center[1] - (rect.size[1]/2))


class KivyWFC(App):
    def build(self):
        return Content()


if __name__ == '__main__':
    KivyWFC().run()
