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
series_name = 'marseille'
series_name = 'versailles'
series_name = 'baron_noir'

pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
text_data = pd.read_pickle(pickle_file)

min_threshold = 3

def compute_components(text_data,day_list):
	# compute the components
	# return the multilayer graph and the graph of compressed components
	import numpy as np
	threshold = 3
	time_threshold = 2
	print('Computing the multilayer graph.')
	H = mlg.multilayergraph(text_data,day_list,threshold=threshold)
	print('Compressing the connected components.')
	G_all = mlg.compress_multilayer(H,time_threshold)
	#threshold2 = max(min_threshold,threshold+20*np.log2((1+G_all.size())/70.0)) # add one to avoid empty graph singularity
	#print('adapting the threshold to value: {}'.format(threshold2))
	#print('Computing the multilayer graph with new threshold.')
	#H = mlg.multilayergraph(text_data,day_list,threshold=threshold2)
	#print('Compressing the connected components.')
	#G_all = mlg.compress_multilayer(H,time_threshold)
	G_all.graph['series_name'] = series_name
	G_all.graph['threshold'] = str(threshold)#str(threshold2)
	return H,G_all

# for the year 2015
year = 2015
for month in range(1,13):
	day_list = mlg.hours_of_month(year,month)
	# compute the components, H is the multilayer grah, G_all is the graph with all the compressed components
	H,G_all = compute_components(text_data,day_list)
	# save the graph
	json_filename = 'cc_'+series_name+'_'+str(year)+'_'+str(month)+'.json'
	filename = viz_path + json_filename
	mlg.save_graph(G_all,filename)
	print('Graph written to file: {}'.format(filename))
	print('extracting the time data from the connected components')
	mlg.extract_components_as_timetables(H,time_component_path,'edges')#items='nodes')

# for the year 2016
year = 2016
for month in range(1,10):
	day_list = mlg.hours_of_month(year,month)
	H,G_all = compute_components(text_data,day_list)
	# save the graph
	json_filename = 'cc_'+series_name+'_'+str(year)+'_'+str(month)+'.json'
	filename = viz_path + json_filename
	mlg.save_graph(G_all,filename)
	print('Graph written to file: {}'.format(filename))
	print('extracting the time data from the connected components')
	mlg.extract_components_as_timetables(H,time_component_path,'edges')#items='nodes')



# show it with networkx
#mlg.draw_graph(G_all)

# show it on a web browser
#url =  'http://localhost:8008/forcegraphmeme.html'+'?'+'file='+json_filename
#mlg.web_viz(url)
