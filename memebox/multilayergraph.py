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
