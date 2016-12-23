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
import memebox.multilayergraph as mlg
import configparser
import argparse
import datetime

parser = argparse.ArgumentParser(description='Compute the tree graph of a given word from the corpus.')
parser.add_argument('word',
                   help='a word to find in the corpus')
parser.add_argument('series',
                   help='The series where to find the word')
parser.add_argument('start_date',
                   help='The start date of the corpus')
parser.add_argument('end_date',
                   help='The end date of the corpus')
#parser.add_argument('file', metavar='file', help='file containing the corpus')

args = parser.parse_args()
input_dic = vars(args)
print(input_dic)
candidat_word = input_dic['word'] 
series_name = input_dic['series']

print('Series {}'.format(series_name))

config = configparser.ConfigParser()
config.read('/home/benjamin/Documents/memetracker/memeconfig.ini')
#data_path = config['DEFAULT']['data_path']
pickle_data_path = config['DEFAULT']['pickle_data_path']
viz_path = config['DEFAULT']['viz_data_path']


# Series name
#series_name = 'marseille'
#series_name = 'LBDL'

pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
text_data = pd.read_pickle(pickle_file)

# time slice of text data
start_date = input_dic['start_date'] 
end_date = input_dic['end_date'] 
text_data = mlg.time_slice(text_data,datetime.datetime.strptime(start_date,"%d-%m-%Y"),
							datetime.datetime.strptime(end_date,"%d-%m-%Y"))

# Word to search ngrams form:
#candidat_word = "légendes"
#candidat_word = "depardieu"

# Number n of n-grams
n_grams = 5

print('Series {}'.format(series_name))
candidat_word = candidat_word.lower()
print('Search for the candidat word: {}'.format(candidat_word))
print('Extracting ngrams...')
dic_of_ngrams = mtg.find_ngrams_dic(candidat_word,text_data,direction='forward',n_grams=n_grams)
info_dic_of_ngrams = mtg.get_ngram_infos(dic_of_ngrams,text_data)
print('Nb of occurences of {} : {}'.format(candidat_word,info_dic_of_ngrams[candidat_word]['nb_occur']))
print('Medias where it appears: {}'.format(info_dic_of_ngrams[candidat_word]['medias']))

print('Constructing the tree graph.')
G,root_id = mtg.createTreeGraph_fromdic(info_dic_of_ngrams,candidat_word,threshold=2)
# save the graph
json_filename = "treegraph"+series_name+"_"+candidat_word+".json"
filename = viz_path + json_filename
print('saving the graph to {}'.format(filename))
mtg.save_graph(G,root_id,filename)


# show it on a web browser
#url =  'http://localhost:8008/treegraphmeme.html'+'?'+'file='+json_filename
#mtg.web_viz(url)
