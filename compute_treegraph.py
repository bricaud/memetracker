#!/usr/bin/env python

"""compute_treegraph.py: 
	from the pickle file containing the filtered texts
	extract the ngrams made out of a chosen word
	Create a tree graph of ngrams of different lengths
	save the data as a tree graph to a json file
	the folders where to find and save the data are given by the memeconfig.ini file
"""

__author__      = "Benjamin Ricaud"
__copyright__   = "Copyright 2016, Benjamin Ricaud"

import pandas as pd
import memebox.treegraph as mtg
import configparser
config = configparser.ConfigParser()
config.read('memeconfig.ini')
#data_path = config['DEFAULT']['data_path']
pickle_data_path = config['DEFAULT']['pickle_data_path']
viz_path = config['DEFAULT']['viz_data_path']


# Series name
#series_name = 'marseille'
series_name = 'LBDL'

pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
text_data = pd.read_pickle(pickle_file)

# Word to search ngrams form:
candidat_word = "légendes"
# Number n of n-grams
n_grams = 5

print('Search for the candidat word: {}'.format(candidat_word))
print('Extracting ngrams...')
dic_of_ngrams = mtg.find_ngrams_dic(candidat_word,text_data,direction='forward',n_grams=n_grams)
info_dic_of_ngrams = mtg.get_ngram_infos(dic_of_ngrams,text_data)
print('Nb of occurences of {} : {}'.format(candidat_word,info_dic_of_ngrams[candidat_word]['nb_occur']))
print('Medias where it appears: {}'.format(info_dic_of_ngrams[candidat_word]['medias']))

print('Constructing the tree graph.')
G,root_id = mtg.createTreeGraph_fromdic(info_dic_of_ngrams,candidat_word,threshold=35)
# save the graph
json_filename = "treegraph"+series_name+".json"
filename = viz_path + json_filename
print('saving the graph to {}'.format(filename))
mtg.save_graph(G,root_id,filename)


# show it on a web browser
url =  'http://localhost:8008/treegraphmeme.html'+'?'+'file='+json_filename
mtg.web_viz(url)
