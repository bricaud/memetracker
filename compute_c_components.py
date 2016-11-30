#!/usr/bin/env python

"""compute_c_components.py: 
	extract text data from csv files given by radarly,
	filter the texts to get rid of stop words,
	perform ML to get the most relevant words: word count and tfidf,
	save the data to pickles files
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

series_name = 'LBDL'

pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
text_data = pd.read_pickle(pickle_file)

# month of the analysis
day_list = mlg.days_of_month(2015,5)
# compute the components
print('Computing the multilayer graph.')
H = mlg.multilayergraph(text_data,day_list,threshold=30)
print('Compressing the connected components.')
G_all = mlg.compress_multilayer(H)
G_all.graph['series_name'] = series_name
# save the graph
json_filename = 'ccomponent.json'
filename = viz_path + json_filename
mlg.save_graph(G_all,filename)
print('Graph written to file: {}'.format(filename))

# show it with networkx
mlg.draw_graph(G_all)

# show it on a web browser
url =  'http://localhost:8008/forcegraphmeme.html'+'?'+'file='+json_filename
mlg.web_viz(G_all,url)
