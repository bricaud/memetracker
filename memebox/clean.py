##############################################################################
#   Functions for cleaning/filtering the texts
##############################################################################
import pandas as pd
#import nltk

def stopword_set():
	""" return a set of stop words
	"""
	from nltk.corpus import stopwords
	# chargement des stopwords français
	french_stopwords = set(stopwords.words('french'))
	# add custom stop words
	french_stopwords.update(['les','cette','http','https','fait','tout','tous','est','entre','dont','autour','\''])
	return french_stopwords

def load_csv(csvfile):
	""" Load the csv file containing the data from radarly
	and return a pandas dataframe with date,text,title,platform and hashtags
	"""
	Dataf = pd.read_csv(csvfile,sep=';',dtype='unicode')
	# Extract a subset of the data
	filtered_data = Dataf[["date","text","title", "platform","hashtags"]].copy()
	# the entries of the date column are dates:
	filtered_data['date'] = pd.to_datetime(filtered_data['date'])#,infer_datetime_format=True)
	return filtered_data

def reject_stopwords(tokens,stopwords):
	""" reject the stopwords and the words smaller than 3 chars and return a new list of tokens
	input: list of tokens
	"""
	tokens_ns = [token for token in tokens if ((token.lower() not in stopwords) 
		and (len(token)>2) and ('http' not in token) and ('\'' not in token))] # length greater than 2 and not http inside the string (get rid of the urls)
	# the last requirement avoid "ai" to appear because "j'ai" was not filtered in the twitter tokenizer
	return tokens_ns

def filter_text(dataframe):
	""" filter the texts in column dataframe.text (tokenize and get rid of stopwords)
	return a copy of the dataframe with a additional column: 'filtered_text'
	"""
	import re
	import nltk
	from nltk.tokenize import TweetTokenizer
	from nltk.tokenize import word_tokenize
	tknzr = TweetTokenizer()
	# initialize the dataframe receiving the filtered texts
	texts = dataframe.text
	filtered_text_list=texts.copy()
	stopwords = stopword_set()
	#print(stopwords)
	# itearating over all texts
	for row in dataframe.itertuples():
		# print(ind)
		idx = row.Index
		texte = row.text
		platform = row.platform
		if (not pd.isnull(texte)):
			if platform == 'Twitter':
				tokens = tknzr.tokenize(texte)
			else:
				# filter out the chars that are not alphabet letters
				texte = re.findall(r"\w+", texte)
				texte = " ".join( texte )
				# Cut the text in tokens
				tokens = nltk.tokenize.word_tokenize(texte, language='french')
			tokens_ns = reject_stopwords(tokens,stopwords)
			filtered_text = " ".join( tokens_ns )
		else:
			filtered_text = " "
		filtered_text_list[idx] = filtered_text
	dataframe_f = dataframe.copy()
	dataframe_f.loc[:,'filtered_text'] = filtered_text_list
	return dataframe_f

def save_data(dataframe,filename):
	dataframe.to_pickle(filename)

#################################################################################
### Machine learning
#################################################################################

def format_data_for_ML(dataframe):
	""" Make a list of texts from the dataframe
		uses the column 'filtered_text' of the dataframe
	"""
	clean_train_reviews = []
	for text in dataframe.filtered_text:
		clean_train_reviews.append(text)
	return clean_train_reviews

def bag_of_words(data):
	""" Perform a bag of words analysis of the dataset
		return a dataframe with the vocabulary and the occurence of each word
		example:
		vocab_dataframe = bag_of_words(data)
	"""
	print("Creating the bag of words...\n")
	import numpy as np
	from sklearn.feature_extraction.text import CountVectorizer

	# Initialize the "CountVectorizer" object, which is scikit-learn's
	# bag of words tool.  
	vectorizer = CountVectorizer(analyzer = "word", tokenizer = None,
		preprocessor = None, stop_words = None,max_features = 5000) 

	# fit_transform() does two functions: First, it fits the model
	# and learns the vocabulary; second, it transforms our training data
	# into feature vectors. The input to fit_transform should be a list of 
	# strings.
	train_data_features = vectorizer.fit_transform(data)

	# Numpy arrays are easy to work with, so convert the result to an 
	# array
	train_data_features = train_data_features.toarray()
	# Take a look at the words in the vocabulary
	vocab = vectorizer.get_feature_names()
	print('Nb of documents: '+str(train_data_features.shape[0])+', '+
		'Nb of features: '+str(train_data_features.shape[1]))
	print('Computing the most frequent words.')
	# Sum up the counts of each vocabulary word
	dist = np.sum(train_data_features, axis=0)
	# create a dataframe with the most frequent words and their occurence
	vocabdf = pd.DataFrame()
	vocabdf['words'] = vocab
	vocabdf['count'] = dist
	vocabdf = vocabdf.sort_values('count',ascending=False)
	vocabdf = vocabdf.reset_index(drop=True)
	return vocabdf

def tfidf(data):
	""" Perform a tf-idf analysis of the dataset
		return a dataframe with the vocabulary and the occurence of each word
		example:
		vocab_dataframe = tfidf(data)
	"""
	import numpy as np
	print("Creating the TFIDF vectors...\n")
	from sklearn.feature_extraction.text import TfidfVectorizer
	# Initialize the "CountVectorizer" object, which is scikit-learn's
	# bag of words tool.  
	vectorizer = TfidfVectorizer(analyzer = "word", tokenizer = None,
		preprocessor = None, stop_words = None,max_features = 5000) 

	# fit_transform() does two functions: First, it fits the model
	# and learns the vocabulary; second, it transforms our training data
	# into feature vectors. The input to fit_transform should be a list of 
	# strings.
	train_data_features_tfidf = vectorizer.fit_transform(data)

	# Numpy arrays are easy to work with, so convert the result to an 
	# array
	train_data_features_tfidf = train_data_features_tfidf.toarray()
	vocab_tfidf = vectorizer.get_feature_names()
	print('Nb of documents: '+str(train_data_features_tfidf.shape[0])+', '+
		'Nb of features: '+str(train_data_features_tfidf.shape[1]))
	print('Computing the most frequent words.')
	# Sum up the counts of each vocabulary word
	dist_tfidf = np.sum(train_data_features_tfidf, axis=0)
	vocabdf = pd.DataFrame()
	vocabdf['words'] = vocab_tfidf
	vocabdf['count'] = dist_tfidf
	vocabdf = vocabdf.sort_values('count',ascending=False)
	vocabdf = vocabdf.reset_index(drop=True)
	return vocabdf