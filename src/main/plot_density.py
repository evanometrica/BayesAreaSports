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
from bokeh.models import Range1d
my_predicter = predicter("../../data/nba.db")



"""
Tab 2: Totaly Flexible
"""
# Create Input controls

class tab_1_maker (object):
    def __init__ (self, size=400):
        self.size = size
        self.min_percentile= Slider(title="Lower Bound of Historical Team", value=.9, start=0, end=1, step=.01)
        self.max_percentile= Slider(title="Upper Bound of Historical Team", value=1, start=0, end=1, step=.01)
        self.game_equivalent= Slider(title="Number of Games to weight prior", value=10, start=1, end=200, step=1)
        self.select_team = Select(title="Current_Team:", value="GSW", options=my_predicter.get_teams_list())

# Create Column Data Source that will be used by the plot
        self.hist_source = ColumnDataSource(data=dict(
                    top =[],
                    left = [],
                    right = []
                    ))
                    
        self.pdf_source = ColumnDataSource( data = dict(
                    pdf_x=[], 
                    prior_y = [],
                    rescaled_y = [],
                    post_y = []
                    ))
        self.cdf_source =ColumnDataSource(data = dict(
                    cdf_x = [],
                    cdf_y =[]
                    ))



        self.p1 = figure(title="Density Fuctions", tools="save",
                   background_fill_color="#E8DDCB", width= self.size, plot_height=self.size)
        self.p1.legend.location = "top_right"
        self.p1.xaxis.axis_label = 'Winning Percentage'
        self.p1.yaxis.axis_label = 'Likelihod of prior'
        self.p1.quad(top="top", bottom=0, left="left", right="right", source= self.hist_source, line_color="#033649")
        self.p1.line(x = "pdf_x", y = "prior_y", source= self.pdf_source, line_color="#D95B43", line_width=8, alpha=0.7, legend="prior PDF")
        self.p1.line(x = "pdf_x", y = "rescaled_y", source= self.pdf_source, line_color="red", line_width=8, alpha=0.7, legend="rescaled PDF")
        self.p1.line(x = "pdf_x", y= "post_y", source= self.pdf_source, line_color="green", line_width=8, alpha=0.7, legend="posterior PDF")


        self.p2_hover = HoverTool(
            tooltips=[
                ("wins", "@cdf_x"),
                ("prob", "@cdf_y"),
            ]
        )

        self.p2 = figure(title="Cumulitive Wins", tools=[self.p2_hover,"save"],
                   background_fill_color="#E8DDCB",  width= self.size, plot_height=self.size)
        self.p2.xaxis.axis_label = 'Number of Wins in 82 game seasons'
        self.p2.yaxis.axis_label = 'Probabily of Wins'
        self.p2.circle(x='cdf_x', y='cdf_y', source = self.cdf_source, size = 20)
        self.p2.x_range=Range1d(-2, 84)
        self.p2.y_range=Range1d(-3, 103)

        self.textbox = PreText(text='', width=self.size)
    def select_data(self):
        return my_predicter.vis_data (
            self.min_percentile.value,
            self.max_percentile.value, 
            self.select_team.value,
            self.game_equivalent.value )


    def update(self):
        data_dict = self.select_data()
        hist, edges = np.histogram(data_dict['prior_hist'].pct, density=True, bins=25)
        x = np.linspace(0, 1, 1000)
        self.hist_source.data = dict(
                top = hist,
                left = edges[:-1],
                right = edges[1:])

        self.pdf_source.data = dict(
                pdf_x= x,
                prior_y =  x**(data_dict['prior'][0]-1) * (1-x)**(data_dict['prior'][1]-1)/ \
                 scipy.special.beta(data_dict['prior'][0], data_dict['prior'][1]) ,
                rescaled_y = x**(data_dict['prior_rescaled'][0]-1) * (1-x)**(data_dict['prior_rescaled'][1]-1)/ \
                 scipy.special.beta(data_dict['prior_rescaled'][0], data_dict['prior_rescaled'][1]),
                post_y = x**(data_dict['posterior'][0]-1) * (1-x)**(data_dict['posterior'][1]-1)/ \
                 scipy.special.beta(data_dict['posterior'][0], data_dict['posterior'][1]),
                )
        self.cdf_source.data= dict(
                cdf_x = data_dict['cdf'].wins ,
                cdf_y = data_dict['cdf'].prob
        )
        stats = data_dict['stats']
        text_str = ( "Wins: "+ str(stats['wins']) + '\n' +
            "Losses: "+ str(stats['losses']) + '\n' +
            "Emperical Win Pct: "+ str(stats['emperical_win_pct']) + '%' + '\n' +
            "Emperical Game Equivalent: "+ str(stats['prior_ge'])) 
        self.textbox.text = text_str

    def main(self, org="H"):
        controls = [self.min_percentile, self.max_percentile, self.select_team, self.game_equivalent]
        for control in controls:
            control.on_change('value', lambda attr, old, new: self.update())

        sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example

        inputs = widgetbox(*controls, sizing_mode=sizing_mode)
        if org== "H":
            l1 = layout([
            [inputs],
            [self.textbox],
            [self.p1, self.p2],
            ], sizing_mode=sizing_mode)

        else:
            l1 = layout([
            [inputs],
            [self.textbox],
            [self.p1], 
            [self.p2],
            ], sizing_mode=sizing_mode)
        self.update()  # initial load of the data
        return l1

