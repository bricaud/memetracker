
import pandas as pd
import networkx as nx
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
    #import pandas as pd

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
    # * A dictionary of ngrams as keys ans the list of indices where to find the n-grams as values
    # Example:
    #         dic_of_ngrams = find_ngrams_dic(word,texts,direction='forward')
    #import pandas as pd

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
    # if popularity=0 the is no limit.
    
    # root word
    root_id = '_'+root_word
    print('Create the graph and add the root node \'{}\'.'.format(root_word))
    G = nx.DiGraph()
    # compute the number of occurences of the word:
    nb_occur = dic_of_ngrams[root_word]['nb_occur']#int(list_of_df_of_ngrams[0].nb_occur[0])
    #nb_occur = 0
    G.add_node(root_id,name=root_word, occur=nb_occur)
    print('Add children nodes from the n-grams dataset.')
    for k in dic_of_ngrams.keys():
        infos_k = dic_of_ngrams[k]
        add_node_layer_fromdic(G,k,infos_k,threshold)
    return G,root_id

def add_node_layer_fromdic(G,ngram,info_ngram,threshold=0):
    # Add all the nodes of a layer
    # Add them only if the nb of occur is above the threshold
    # ngram_df is the dataframe containing the ngrams with their occurence
    # layer is the graph layer ()

    word_list = ngram.split()
    root_node = word_list[0]
    nb_occur = info_ngram['nb_occur']
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
                    #if popularity:
                    #    if idx>=popularity-1:
                    #        break

        


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

##################################################################################
#   Functions for constructing the multilayer graph from the dataframes of n-grams
##################################################################################

def time_slice(df,start_date,end_date):
    # df must have a column 'date
    # date are in datetime format
    mask = (df['date'] > start_date) & (df['date'] <= end_date)
    df_slice = df.loc[mask]
    return df_slice

def layer_graph(df,timestamp):
# for each text, create node for each keyword and connect to its following word 
    timestamp_str = '_'+timestamp.strftime("%Y-%m-%d")
    G = nx.DiGraph()
    for row in df.itertuples():
        text = row.filtered_text
        #text = row.text
        textlist = str(text).split()
        for idx,word in enumerate(textlist):
            #print(idx)
            if (idx+1)<len(textlist):
                next_word = textlist[idx+1]
                word_id = word+timestamp_str
                next_word_id = next_word+timestamp_str
                # Adding the nodes
                if not G.has_node(word_id):
                    G.add_node(word_id,name=word,timestamp=timestamp)
                if not G.has_node(next_word_id):
                    G.add_node(next_word_id,name=next_word,timestamp=timestamp)
                # Adding an edge
                if G.has_edge(word_id,next_word_id):
                    # we added this one before, just increase the weight by one
                    G[word_id][next_word_id]['weight'] += 1
                    tseries = G[word_id][next_word_id]['time_series']
                    #print(tseries)
                    #print(type(tseries))
                    #print(type(row.date))
                    tseries.append(row.date)
                    #.append(row.date.strftime('%Y-%m-%d'))
                    G[word_id][next_word_id]['time_series'] = tseries
                else:
                    # new edge. add with weight=1
                    new_list = []
                    new_list.append(row.date)
                    G.add_edge(word_id, next_word_id, weight=1,time_series=new_list)
    return G

def drop_edges(G,threshold=4):
    for u,v,a in G.edges(data=True):
        if a['weight']<threshold:
            G.remove_edge(u,v)
    return G

def get_node_name(node):
    # return the name before the date (separated by a '_')
    idx = node.rfind('_')
    return node[:idx]

def connect_layer(H,G_old,G):
    old_nodes = G_old.nodes()
    for new_node in G.nodes():
        new_node_name = get_node_name(new_node)
        for old_node in G_old.nodes():
            old_node_name = get_node_name(old_node)
            if new_node_name == old_node_name:
                H.add_edge(old_node,new_node,weight=100,label='interlayer')
    return H

def range_date(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta

def date_to_int(date, start, end):
    # return an int in[0,1]
    # from a date between [start, end]
    from datetime import timedelta
    list_dates =[n for n in range_date(start, end+timedelta(days=1), timedelta(days=1))]
    idx = list_dates.index(date)
    if (len(list_dates)-1)>0:
        value = idx/(len(list_dates)-1)
    else:
        value = 0
    return value

def find_dates(G):
    date_list = [ m for n,m in nx.get_node_attributes(G,'timestamp').items()]
    start_date = min(date_list)
    end_date = max(date_list)
    return start_date,end_date

def add_relative_date(G):
    import datetime
    if nx.number_of_nodes(G)>0:
        date_list = [ datetime.datetime.strptime(m,"%d-%m-%Y") for n,m in nx.get_node_attributes(G,'start_time').items()]
        start_date = min(date_list)
        end_date = max(date_list)
        for (node,props) in G.nodes(data=True):
            G.node[node]['color_rel'] = date_to_int(datetime.datetime.strptime(props['start_time'],"%d-%m-%Y"),start_date,end_date)
    return G

def compress_component(G,threshold):
    from collections import Counter
    # nodes
    node_list = [get_node_name(node) for node in G.nodes()] # name from id
    nodes_dic = Counter(node_list)
    nodes_t = [(name,{'nb_occur':nb_occur}) for (name,nb_occur) in nodes_dic.items() if nb_occur>threshold]
    node_list = [name for (name,prop) in nodes_t]
    if len(node_list)>0:
        #node time
        node_data = G.nodes(data=True)
        #edges
        edge_list = [(get_node_name(u),get_node_name(v)) for (u,v) in G.edges()]
        edge_list = [(u,v) for (u,v) in edge_list if (u in node_list and v in node_list)]
        edge_list = [(u,v) for (u,v) in edge_list if not (u == v)]
        #graph
        G2 = nx.DiGraph()
        G2.graph['start_date']=G.graph['start_date'].strftime("%d-%m-%Y")
        G2.graph['end_date']=G.graph['end_date'].strftime("%d-%m-%Y")
        G2.add_nodes_from(nodes_t)
        G2.add_edges_from(edge_list)
        #G2 = max(nx.weakly_connected_component_subgraphs(G2), key=len)
        G2.remove_nodes_from(nx.isolates(G2))
        # time property
        node_data = G.nodes(data=True)
        start_date,end_date = find_dates(G)
        #print(start_date,end_date)
        for node in G2.nodes():
            time_list = []
            for (G_node,properties) in G.nodes(data=True):
                if node in G_node:
                    time_list.append(properties['timestamp'])
            time_list.sort()
            G2.node[node]['start_time']=time_list[0].strftime("%d-%m-%Y")
            G2.node[node]['name'] = node
            G2.node[node]['color'] = date_to_int(time_list[0],G.graph['start_date'],G.graph['end_date'])
            #print(date_to_int(time_list[0],start_date,end_date))
            G2.node[node]['color_rel_full'] = date_to_int(time_list[0],start_date,end_date)
            #G2.node[node]['time_length'] = len(time_list)
            # relabel the nodes to take into account the first time stamp
        G2 = add_relative_date(G2)
        #[ print(props) for(name,props) in G2.nodes(data=True)]
        dic_of_names = {name:name+'_'+props['start_time'] for(name,props) in G2.nodes(data=True) }
        G3 = nx.relabel_nodes(G2,dic_of_names)
        return G3
    else:
        return nx.DiGraph()
