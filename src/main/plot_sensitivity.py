from os.path import dirname, join

import numpy as np
import pandas.io.sql as psql
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc
import numpy as np
import scipy
import pandas as pd
from predicter import predicter
from bokeh.models.widgets import Panel, Tabs, TextInput, PreText
from bokeh.models import Range1d, LinearColorMapper,  BasicTicker, ColorBar
from bokeh.palettes import RdYlGn11 as palette

my_predicter = predicter("nba.db")


"""
Tab 2: Totaly Flexible
"""
# Create Input controls

class sensitivity_maker (object):
    def __init__ (self, size=500):
        self.size = size
        self.game_thresh= Slider(title="Probability of Winning at Least Games", value=50, start=0, end=82, step=1)
        self.select_team = Select(title="Current_Team:", value="GSW", options=my_predicter.get_teams_list())

# Create Column Data Source that will be used by the plot
        self.scatter_source = ColumnDataSource(data=dict(
                    pct =[],
                    we = [],
                    prob = []))
                    

        self.p2_hover = HoverTool(
            tooltips=[
                ("win percentage", "@pct"),
                ("game equivalent", "@we"),
                ("probability of winnin N games", "@prob"),
            ]
        )

        palette_r = palette[::-1]
        color_mapper = LinearColorMapper(palette=palette_r, low = 0.0, high = 100.0)
        self.p2 = figure(title="Probability of winning at least n games", tools=[self.p2_hover,"save"],
                   background_fill_color="#E8DDCB",  width= self.size, plot_height=self.size, toolbar_location="below")
        self.p2.xaxis.axis_label = 'Prior Expected Win Pct'
        self.p2.yaxis.axis_label = 'Prior Game Equivalent'

        #self.scatter_course.data['c' = "red"
        self.p2.circle(x='pct', y='we', color= {'field': 'prob', 'transform': color_mapper}, line_color="black", source = self.scatter_source, size = 12)
        color_bar = ColorBar(color_mapper=color_mapper, ticker=BasicTicker(),
                     label_standoff=12, border_line_color=None, location=(0,0))
        self.p2.add_layout(color_bar, 'right')
        text_string = """
        From the previous tab, it is clear your prior beliefs should strongly influence
        your future projections. This tab lets you explore different beliefs based on your
        prior. Choose a team, and a number of wins you wish to project them achieving. This plot
        tells you the probability they achieve those wins (color), conditional on a prior expected
        winning percentage (x-axis) and a strength of that prior (y-axis)
        """
        self.sample_text = PreText (text = text_string, height = 50, width =800)

    def select_data(self):
        return my_predicter.calc_sensitivity (
            self.select_team.value,
            self.game_thresh.value)


    def update(self):
        data_dict = self.select_data()
        self.scatter_source.data = data_dict


    def main(self):
        controls = [self.game_thresh, self.select_team]
        for control in controls:
            control.on_change('value', lambda attr, old, new: self.update())

        sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example
        inputs = widgetbox(*controls, sizing_mode=sizing_mode)
        l1 = layout([[self.sample_text],[inputs],[self.p2]], sizing_mode=sizing_mode)
        self.update()  # initial load of the data
        return l1

