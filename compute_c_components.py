#!/usr/bin/env python

"""compute_c_components.py: 
	from the pickle file containing the filtered texts
	extract all possible bigrams and create a multilayer graph of bigrams
	each layer corresponds to a day
	Extract the weakly connected components and compress them along the time axis
	save the data as a graph with several subgraphs (compressed connected components) to a json file
	the folders where to find and save the data are given by the memeconfig.ini file
"""

__author__      = "Benjamin Ricaud"
__copyright__   = "Copyright 2016, Benjamin Ricaud"

import pandas as pd
import memebox.multilayergraph as mlg
import configparser
config = configparser.ConfigParser()
config.read('memeconfig.ini')
#data_path = config['DEFAULT']['data_path']
pickle_data_path = config['DEFAULT']['pickle_data_path']
viz_path = config['DEFAULT']['viz_data_path']
time_component_path = config['DEFAULT']['time_data_path']

series_name = 'LBDL'

pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
text_data = pd.read_pickle(pickle_file)

# month of the analysis
month = 5
year = 2015
for month in range(1,13):
	day_list = mlg.days_of_month(year,month)
	# compute the components
	print('Computing the multilayer graph.')
	H = mlg.multilayergraph(text_data,day_list,threshold=30)
	print('Compressing the connected components.')
	G_all = mlg.compress_multilayer(H)
	G_all.graph['series_name'] = series_name
	# save the graph
	json_filename = 'ccomponents'+str(year)+'_'+str(month)+'.json'
	filename = viz_path + json_filename
	mlg.save_graph(G_all,filename)
	print('Graph written to file: {}'.format(filename))
	print('extracting the time data from the connected components')
	mlg.extract_components_as_timetables(H,time_component_path)

# show it with networkx
#mlg.draw_graph(G_all)

# show it on a web browser
#url =  'http://localhost:8008/forcegraphmeme.html'+'?'+'file='+json_filename
#mlg.web_viz(url)
