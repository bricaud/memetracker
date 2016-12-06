#!/usr/bin/env python
##############################################################################
#   Functions for finding n-grams in the texts
##############################################################################

def find_ngrams(word,df_texts,direction='forward',n_grams=3):
    # find the words that follow (direction='forward') or precede (direction='backward')
    # the keyword 'word' in the texts 'df_texts'. Record the ngrams up to length 'n_grams'
    # n_grams: number of successive words
    # return 
    # * A list of Pandas dataframes 
    #   where each PD contain the list of ngrams with their occurence
    # * the list of texts where the word has been found
    # Example:
    #         word_list,texts_list = find_ngrams(word,df_texts,direction='forward',n_grams=3)
    
    import pandas as pd
    list_texts_subset = []
    list_of_ngram_list = []
    for n in range(n_grams):
        list_of_ngram_list.append([])
    #print(word)
    for row in df_texts.itertuples():
        #print(row)
        text = row.filtered_text
        if (not pd.isnull(text)):
            text = text.lower()
            wordlist = str(text).split()
            if direction=='forward':
                pass
            elif direction=='backward':
                wordlist.reverse()
            else :
                raise NameError('Unknown direction. Only \'forward\' or \'backward\' are allowed.')
            if len(set(wordlist)&set([word]))>0:
                word_indices = [i for i, x in enumerate(wordlist) if x == word]
                list_texts_subset.append(row.Index)
                for word_ind in word_indices:
                    word_chain = chain_of_grams(word_ind,wordlist,n_grams)
                    #word_chain = ' '.join(word_chain)
                    list_of_ngram_list = append_chain(list_of_ngram_list,word_chain)
                    #neighbour_list.append(wordlist[word_ind+1])
    df_texts_subset =df_texts.loc[list_texts_subset]
    list_of_ngram_df_merged = merge_ngrams(list_of_ngram_list)
    return list_of_ngram_df_merged,df_texts_subset


def find_ngrams_dic(word,df_texts,direction='forward',n_grams=3):
    # find the words that follow (direction='forward') or precede (direction='backward')
    # the keyword 'word' in the texts 'texts'
    # n_grams: number of successive words
    # return 
    # * A dictionary of ngrams as keys and the list of indices where to find the n-grams as values.
    #   The ngram keys are string of words separated by a space.
    # Example:
    #         dic_of_ngrams = find_ngrams_dic(word,texts,direction='forward')
    
    import pandas as pd
    dic_of_ngrams = {}
    #print(word)
    for row in df_texts.itertuples():
        #print(row)
        text = row.filtered_text
        if (not pd.isnull(text)):
            text = text.lower()
            wordlist = str(text).split()
            if direction=='forward':
                pass
            elif direction=='backward':
                wordlist.reverse()
            else :
                raise NameError('Unknown direction. Only \'forward\' or \'backward\' are allowed.')
            if len(set(wordlist)&set([word]))>0:
                word_indices = [i for i, x in enumerate(wordlist) if x == word]
                for word_ind in word_indices:
                    word_chain = chain_of_grams(word_ind,wordlist,n_grams)
                    #word_chain = ' '.join(word_chain)
                    dic_of_ngrams = append_chains_to_dic(dic_of_ngrams,word_chain,row.Index)
                    #neighbour_list.append(wordlist[word_ind+1])
    return dic_of_ngrams

def chain_of_grams(word_ind,wordlist,n_grams):
    # chain the words that follow the word in wordlist with index word_ind
    # n_grams give length of the chain
    # return a list of words
    n = 0
    word_chain = []
    while (n<=n_grams and (word_ind+n<len(wordlist))):
        word_chain.append(wordlist[word_ind+n])
        n+=1
    return word_chain

def append_chain(list_of_ngram_list,word_chain):
    # for each dataframe, corresponding to the n-grams
    # turn the list of words into a string of the size of the n-gram
    # add it to its dataframe
    for n in range(len(word_chain)-1):
        n_gram = ' '.join(word_chain[:n+1])
        list_of_ngram_list[n].append(n_gram)
    return list_of_ngram_list

def append_chains_to_dic(dic_of_ngrams,word_chain,text_index):
    # for each dataframe, corresponding to the n-grams
    # turn the list of words into a string of the size of the n-gram
    # add it to a dictionary as well as the df index where the ngram is located
    for n in range(len(word_chain)-1):
        n_gram = ' '.join(word_chain[:n+1])
        if n_gram in dic_of_ngrams:
            dic_of_ngrams[n_gram].append(text_index)
        else:
            dic_of_ngrams[n_gram] = [text_index]
    return dic_of_ngrams

def merge_ngrams(list_of_ngram_list):
    # merge the diplucates in all the dataframes of n-grams
    # return a list of dataframe, one for each n-gram length
    # each dataframe has two columns, one with the n-gram, one with its occurence
    import pandas as pd
    from collections import Counter
    list_of_ngram_df_merged = []
    for n in range(len(list_of_ngram_list)):
        list_of_ngram_df_merged.append([])
    for n in range(len(list_of_ngram_list)):
        N_uniquedic = Counter(list_of_ngram_list[n])
        # optionally: filter the dic for removing the lowest values
        N_words = {k:v for (k,v) in N_uniquedic.items() if v > 0}
        Ndf = pd.DataFrame(list(N_words.items()), columns=['ngram','nb_occur'])
        Ndf = Ndf.sort_values('nb_occur',ascending=False)
        Ndf = Ndf.reset_index(drop=True)
        list_of_ngram_df_merged[n] = Ndf
    return list_of_ngram_df_merged

def get_ngram_infos(dic_of_ngrams,text_data):
    """ create a new dic of ngrams containing information about 
        * nb of occurences of the ngram
        * medias where the ngram appear
        * a time series of ngram appearance
        input a dic with ngrams as keys and list of indices where the ngram appear as value
    """
    info_dic_of_ngrams = {}
    for k in dic_of_ngrams.keys():
        list_k = dic_of_ngrams[k]
        info_dic_k = {}
        info_dic_k['nb_occur'] = len(list_k)
        info_dic_k['medias'] = text_data.loc[list_k].platform.value_counts().to_dict()
        timeseries = text_data.loc[list_k].date.sort_values()
        start_time = timeseries.iloc[0]
        timeseries = timeseries.groupby(timeseries.dt.strftime('%d-%m-%Y')).size()
        info_dic_k['timeseries'] = timeseries.to_dict()
        info_dic_k['start_time'] = start_time.strftime('%d-%m-%Y')
        info_dic_of_ngrams[k]=info_dic_k
    return info_dic_of_ngrams

##################################################################################
#   Functions for constructing the tree graph from the dataframes of n-grams
##################################################################################

def createTreeGraph(list_of_df_of_ngrams,threshold=0,popularity=0):
    # Create the tree graph from the list of dataframes containing the ngrams
    # each dataframe has 2 columns, 'ngram' and 'nb_occur' for the n-gram and its occurence in the texts
    # the root word is contained in list_of_df_of_ngrams[0].ngram[0]
    # threshold (int) set the number of occurences above which a ngram is included in the graph
    # popularity (int) limits the number of n-gram added to the graph to the top m=popularity**n
    # if popularity=0 the is no limit.
    
    import networkx
    # root word
    root_word = list_of_df_of_ngrams[0].ngram[0]
    root_id = '_'+root_word
    print('Create the graph and add the root node \'{}\'.'.format(root_word))
    G = nx.DiGraph()
    # compute the number of occurences of the word:
    nb_occur = int(list_of_df_of_ngrams[0].nb_occur[0])
    #nb_occur = 0
    G.add_node(root_id,name=root_word, occur=nb_occur)
    n_grams = len(list_of_df_of_ngrams[1:])
    print('Add children nodes in the {}-grams dataset.'.format(n_grams))
    for n in range(n_grams):
        layer = n+1
        ngram_df = list_of_df_of_ngrams[layer]
        add_node_layer(G,ngram_df,threshold,popularity=popularity**layer)
    return G,root_id

def createTreeGraph_fromdic(dic_of_ngrams,root_word,threshold=0):
    # Create the tree graph from the list of dataframes containing the ngrams
    # each dataframe has 2 columns, 'ngram' and 'nb_occur' for the n-gram and its occurence in the texts
    # the root word is contained in list_of_df_of_ngrams[0].ngram[0]
    # threshold (int) set the number of occurences above which a ngram is included in the graph
    # popularity (int) limits the number of n-gram added to the graph to the top m=popularity**n
    # if popularity=0 there is no limit.
    
    import networkx as nx
    # root word
    root_id = '_'+root_word
    print('Create the graph and add the root node \'{}\'.'.format(root_word))
    G = nx.DiGraph()
    # get the number of occurences of the word:
    nb_occur = dic_of_ngrams[root_word]['nb_occur']#int(list_of_df_of_ngrams[0].nb_occur[0])
    # find the main media for the word
    main_media,nb_occur_m_media = get_main_media(dic_of_ngrams[root_word]['medias'])
    start_time = dic_of_ngrams[root_word]['start_time']
    G.add_node(root_id,name=root_word, occur=nb_occur, main_media=main_media, 
        nb_occur_m_media=nb_occur_m_media, start_time=start_time, relative_time=0)
    print('Add children nodes from the n-grams dataset.')
    for k in dic_of_ngrams.keys():
        infos_k = dic_of_ngrams[k]
        add_node_layer_fromdic(G,root_id,k,infos_k,threshold)
    return G,root_id


def add_node_layer_fromdic(G,root_id,ngram,info_ngram,threshold=0):
    # Add all the nodes of a layer
    # Add them only if the nb of occur is above the threshold
    # ngram_df is the dataframe containing the ngrams with their occurence
    # layer is the graph layer ()
    from datetime import datetime
    date_format = "%d-%m-%Y"

    word_list = ngram.split()
    root_node = word_list[0]
    nb_occur = info_ngram['nb_occur']
    main_media,nb_occur_m_media = get_main_media(info_ngram['medias'])
    start_time = info_ngram['start_time']
    root_start_date = G.node[root_id]['start_time']
    if nb_occur>=threshold:
        if len(word_list)>=2: #not the root node
            for idx,word in enumerate(word_list):
                if idx>0: # no link for the root node
                    path_word='_'.join(word_list[:idx])
                    word_id = '_'+path_word+'_'+word
                    path_parent = '_'.join(word_list[:idx-1])
                    if len(path_parent) == 0:
                        parent_id = '_'+word_list[idx-1]
                    else:
                        parent_id = '_'+path_parent+'_'+word_list[idx-1]
                    if G.has_node(parent_id):
                        if not G.has_node(word_id):
                            G.add_node(word_id,name=word)
                        G.add_edge(parent_id, word_id)
                        if idx == len(word_list)-1:
                            G.node[word_id]['occur'] = nb_occur
                            G.node[word_id]['main_media'] = main_media
                            G.node[word_id]['nb_occur_m_media'] = nb_occur_m_media
                            G.node[word_id]['start_time'] = start_time
                            a = datetime.strptime(start_time, date_format)
                            b = datetime.strptime(root_start_date, date_format)
                            delta = a - b
                            G.node[word_id]['relative_time'] = delta.days
                    #if popularity:
                    #    if idx>=popularity-1:
                    #        break

def get_main_media(dic_of_medias):
    # find the main media where the word appears
    # return the main media and its number of appearances in ths media
    import numpy
    main_media = max(dic_of_medias, key=lambda key: dic_of_medias[key])
    return main_media,numpy.asscalar(dic_of_medias[main_media])        


def add_node_layer(G,ngram_df,threshold=0,popularity=0):
    # Add all the nodes of a layer
    # Add them only if the nb of occur is above the threshold
    # ngram_df is the dataframe containing the ngrams with their occurence
    # layer is the graph layer ()
    for idx,row in ngram_df.iterrows():
        word_list = row.ngram.split()
        if len(word_list)<2:
            raise NameError('n-grams in the dataframe must be longer than 1')
        nb_occur = row.nb_occur
        #print(row.ngram)
        word = word_list[-1]
        path_word = '_'.join(word_list[:-1])
        parent_word = word_list[-2]
        path_parent = '_'.join(word_list[:-2])
        if len(word_list)<3:
            grand_parent=''
        else:
            grand_parent = word_list[-3]
        word_id = path_word+'_'+word
        parent_id = path_parent+'_'+parent_word
        if nb_occur>=threshold and G.has_node(parent_id):
            G.add_node(word_id,name=word, occur=nb_occur)
            G.add_edge(parent_id, word_id, weight=nb_occur)
        if popularity:
            if idx>=popularity-1:
                break

def save_graph(G,root_id,filename):
    # Write the graph to a json file
    from networkx.readwrite import json_graph
    import json
    datag = json_graph.tree_data(G,root=root_id)
    #datag['links'] = [
    #        {
    #            'source': datag['nodes'][link['source']]['id'],
    #            'target': datag['nodes'][link['target']]['id']
    #        }
    #        for link in datag['links']]
    s = json.dumps(datag)
    with open(filename, "w") as f:
        f.write(s)

def web_viz(url):
    """
    open a new tab on the web browser with url 'url' to display the graph
    It is needed to run a webserver in the folder where the json file has been saved
    using for example: python3 -m http.server --bind 127.0.0.1 8008
    """
    import webbrowser
    #webbrowser.open_new_tab(url)
    webbrowser.open_new(url)
