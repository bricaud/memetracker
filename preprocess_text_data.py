#!/usr/bin/env python

"""preprocess_text_data.py: 
	extract text data from csv files given by radarly,
	filter the texts to get rid of stop words,
	perform ML to get the most relevant words: word count and tfidf,
	save the data to pickles files
	the folders where to find and save the data are given by the memeconfig.ini file
"""

__author__      = "Benjamin Ricaud"
__copyright__   = "Copyright 2016, Benjamin Ricaud"

import memebox.clean as clean
import configparser
config = configparser.ConfigParser()
config.read('memeconfig.ini')
data_path = config['DEFAULT']['data_path']
pickle_data_path = config['DEFAULT']['pickle_data_path']

series_name = 'marseille'
series_name = 'baron_noir'
#series_name = 'versailles'

csvfile = data_path+series_name+'.csv'
print('Loading {}'.format(csvfile))
df_data = clean.load_csv(csvfile)
print('Filtering texts ...')
df_filtered = clean.filter_text(df_data)
pickle_file = pickle_data_path+series_name+'_texts'+'.pkl'
print('saving to {}'.format(pickle_file))
clean.save_data(df_filtered,pickle_file)
# ML part
print('Performing ML')
dataML = clean.format_data_for_ML(df_filtered)
vocab_df = clean.bag_of_words(dataML)
vocab_tfidf = clean.tfidf(dataML)
# Saving the data
print('saving to file:')
print(pickle_data_path+series_name+'_vocab_bow'+'.pkl')
vocab_df.to_pickle(pickle_data_path+series_name+'_vocab_bow'+'.pkl')
print(pickle_data_path+series_name+'_vocab_tfidf'+'.pkl')
vocab_tfidf.to_pickle(pickle_data_path+series_name+'_vocab_tfidf'+'.pkl')