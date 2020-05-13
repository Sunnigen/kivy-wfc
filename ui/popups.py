from functools import partial

from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup


class MatchingTiles(Popup):
    def __init__(self, **kwargs):
        super(MatchingTiles, self).__init__(**kwargs)

    def display_matching_tiles(self):
        # ---Check if Wang Tiles Map in Place---
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
        # ---Add Widgets---
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
            main_tile_rect = Rectangle(pos=(main_tile.pos[0] + 25, main_tile.pos[1]),
                                       size=(self.displayed_size, self.displayed_size))
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
        # north_box.bind(size_hint_min_x=west_box.setter('width'))
        # east_box.bind(size_hint_min_x=west_box.setter('width'))
        # south_box.bind(size_hint_min_x=west_box.setter('width'))
        # west_box.bind(size_hint_min_x=west_box.setter('width'))
        # grid.add_widget(north_box)
        # grid.add_widget(east_box)
        # grid.add_widget(south_box)
        # grid.add_widget(west_box)
        grid.bind(minimum_width=grid.setter('width'))

        scrollview = ScrollView(size_hint=(0.8, 0.8), size=popup.size, do_scroll_x=True, do_scroll_y=False,
                                pos_hint={'x': 0.2, 'y': 0})
        scrollview.add_widget(grid)
        popup_content.add_widget(scrollview)

        spinner = Spinner(
            pos_hint={'right': 1.0, 'top': 1.0},
            size_hint=(None, None),
            size=(100, 33),
            values=sorted(self.wang_tiles_map.tiles.keys())
        )
        spinner.bind(
            text=partial(self._update_match_spinner, main_tile, main_tile_rect, grid, north_box, east_box, south_box,
                         west_box))

        popup_content.add_widget(main_tile)
        popup_content.add_widget(spinner)

        popup.bind(on_dismiss=self.wang_tiles_map.enable_user_interaction)
        popup.open()
        Clock.schedule_once(partial(self.update_lbl_rect, main_tile, main_tile_rect), 0.05)


class TileProbability(Popup):
    def __init__(self, **kwargs):
        super(TileProbability, self).__init__(**kwargs)


class TilesetChooser(Popup):
    def __init__(self, **kwargs):
        super(TilesetChooser, self).__init__(**kwargs)


class MapSizePopup(Popup):
    def __init__(self, **kwargs):
        super(MapSizePopup, self).__init__(**kwargs)
