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
from plot_density import tab_1_maker
from plot_sensitivity import sensitivity_maker
from bokeh.models.widgets import Panel, Tabs, TextInput

my_1_maker = tab_1_maker(400)
tab1 = Panel(child = my_1_maker.main(org="H"), title = "update prior")

my_2_maker_a, my_2_maker_b, my_2_maker_c = tab_1_maker(300), tab_1_maker(300), tab_1_maker(300)
tab2 = Panel( child =layout(
	[[my_2_maker_a.main(org = "V"), 
	my_2_maker_b.main(org = "V"), 
	my_2_maker_c.main(org = "V")]]), title = "compare parameters")


my_sensitivity_maker = sensitivity_maker()
tab3 = Panel (child = my_sensitivity_maker.main(), title = "Explore Across Priors")


tabs = Tabs(tabs=[tab1, tab2, tab3])
curdoc().add_root(tabs)
curdoc().title = "BayesArea"