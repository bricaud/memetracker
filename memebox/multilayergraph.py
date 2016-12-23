#!/usr/bin/env python
##################################################################################
#   Functions for constructing the multilayer graph from the dataframes of n-grams
##################################################################################
import networkx as nx

def time_slice(df,start_date,end_date):
    # df must have a column 'date
    # date are in datetime format
    mask = (df['date'] > start_date) & (df['date'] <= end_date)
    df_slice = df.loc[mask]
    return df_slice

def layer_graph(df,timestamp,date_delta):
# for each text, create node for each keyword and connect to its following word
# date_delta = 'day' our 'hour'
    if date_delta == 'day': 
        timestamp_str = '_'+timestamp.strftime("%Y-%m-%d")
    elif date_delta =='hour':
        timestamp_str = '_'+timestamp.strftime("%Y-%m-%d-%H")
    else:
        raise ValueError("date-delta not recognized. Use 'day' or 'hour'. ")
    G = nx.DiGraph()
    for row in df.itertuples():
        text = row.filtered_text
        media = row.platform
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
                    medialist = G[word_id][next_word_id]['media_list']
                    medialist.append(media)
                    G[word_id][next_word_id]['media_list'] = medialist
                else:
                    # new edge. add with weight=1
                    new_list = []
                    new_list.append(row.date)
                    new_media_list = []
                    new_media_list.append(media)
                    G.add_edge(word_id, next_word_id, label='intralayer',
                        weight=1,time_series=new_list, media_list=new_media_list)
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

def date_to_int(date, start, end,date_delta):
    # return an int in[0,1]
    # from a date between [start, end]
    # date_delta = 'day' or 'hour'
    from datetime import timedelta
    if date_delta=='day':
        list_dates =[n for n in range_date(start, end+timedelta(days=1), timedelta(days=1))]
    elif date_delta=='hour':
        list_dates =[n for n in range_date(start, end+timedelta(hours=1), timedelta(hours=1))]
    else:
        raise ValueError("time delta must be 'day' or 'hour'.")
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
    """ add a property to the nodes of graph G, giving the time of appearance relative to the appearance of the first node
    """
    import datetime
    date_delta=G.graph['date_delta']
    if nx.number_of_nodes(G)>0:
        date_list = [ datetime.datetime.strptime(m,"%d-%m-%Y") for n,m in nx.get_node_attributes(G,'start_time').items()]
        start_date = min(date_list)
        end_date = max(date_list)
        for (node,props) in G.nodes(data=True):
            G.node[node]['color_rel'] = date_to_int(datetime.datetime.strptime(props['start_time'],"%d-%m-%Y"),start_date,end_date,date_delta)
    return G

def compress_component(G,threshold):
    """ Merge together nodes of G with the same name but different time of appearance.
        G is a multilayer graph.
        filter out the nodes with a name that appears in the multilayer graph less time than the threshold
        attach a unique component id to each node.
    """
    from collections import Counter
    # extract the names from the node ids (the id contain the name and the date)
    node_list = [get_node_name(node) for node in G.nodes()] # name from id
    # make a list of unique names and count their occurence in G
    nodes_dic = Counter(node_list) # list of unique names with the number of appearance
    # get rid of the names that do not occur often (less than threshold):
    nodes_t = [(name,{'nb_occur':nb_occur}) for (name,nb_occur) in nodes_dic.items() if nb_occur>threshold]
    # make a list of names to iterate on
    node_list = [name for (name,prop) in nodes_t]

    if len(node_list)>1: # at least 2 nodes with distinct names in the component!
        # get the edges between nodes in node_list
        edge_list = [(get_node_name(u),get_node_name(v)) for (u,v) in G.edges()]
        edge_list = [(u,v) for (u,v) in edge_list if (u in node_list and v in node_list)]
        edge_list = [(u,v) for (u,v) in edge_list if not (u == v)]
        # create a new graph for the compressed component
        G2 = nx.DiGraph()
        G2.graph['start_date']=G.graph['start_date'].strftime("%d-%m-%Y")
        G2.graph['end_date']=G.graph['end_date'].strftime("%d-%m-%Y")
        date_delta = G.graph['date_delta']
        G2.graph['date_delta']=G.graph['date_delta']
        # add the nodes and edges
        G2.add_nodes_from(nodes_t)
        G2.add_edges_from(edge_list)
        # get rid of the isolated nodes
        G2.remove_nodes_from(nx.isolates(G2))
        # add properties to the nodes
        # component id
        component_id = create_cc_id(G) #unique id for the component    
        #G2.set_node_attributes('component_id',component_id)
        for node in G2.nodes():
            G2.node[node]['component_id'] = component_id
        # time property
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
            G2.node[node]['color'] = date_to_int(time_list[0],G.graph['start_date'],G.graph['end_date'],date_delta)
            #print(date_to_int(time_list[0],start_date,end_date))
            G2.node[node]['color_rel_full'] = date_to_int(time_list[0],start_date,end_date,date_delta)
            #G2.node[node]['time_length'] = len(time_list)
        # add relative date property: for the date relative to the beginning of the component
        G2 = add_relative_date(G2)
        # relabel the nodes to take into account the first time stamp
        dic_of_names = {name:name+'_'+props['start_time']+'_'+component_id for(name,props) in G2.nodes(data=True) }
        G3 = nx.relabel_nodes(G2,dic_of_names)
        return G3
    else:
        return nx.DiGraph()

def days_of_month(year,month):
    """ return a list of the days of the chosen month
        elements are in the datetime format
    """
    import datetime
    from dateutil.relativedelta import relativedelta
    # Choose the year
    base = datetime.datetime(year,1,1)
    #three_mon_rel = relativedelta(months=3)
    month_list = [base + relativedelta(month=x) for x in range(1, 13)]
    month_list = month_list+[datetime.datetime(year+1,1,1)]
    # day list
    day_list = [month_list[month-1]+datetime.timedelta(days=n) for n in range(31) 
            if month_list[month-1]+datetime.timedelta(days=n)<month_list[month]]
    start_date=day_list[0].strftime("%d-%m-%Y")
    end_date=day_list[-1].strftime("%d-%m-%Y")
    print('Dates are from {} to {}.'.format(start_date,end_date))
    return day_list

def hours_of_month(year,month):
    """ return a list of the hours of the chosen month
        elements are in the datetime format
    """
    import datetime
    from dateutil.relativedelta import relativedelta
    # Choose the year
    base = datetime.datetime(year,1,1)
    #three_mon_rel = relativedelta(months=3)
    month_list = [base + relativedelta(month=x) for x in range(1, 13)]
    month_list = month_list+[datetime.datetime(year+1,1,1)] # Add january of next year to handle december
    # hour list
    hour_list = [month_list[month-1]+datetime.timedelta(hours=n) for n in range(31*24) 
            if month_list[month-1]+datetime.timedelta(hours=n)<month_list[month]]
    start_date=hour_list[0].strftime("%H-%d-%m-%Y")
    end_date=hour_list[-1].strftime("%H-%d-%m-%Y")
    print('Dates are from {} to {}.'.format(start_date,end_date))
    return hour_list

def multilayergraph(text_data,date_list,threshold):
    """ return the multi layer graph of activated components
        in the text_data, over the days or hours of date_list
        The activity below the threshold is not recorded as active:
        threshold = minimal number of occurences during a day
    """
    import datetime
    if len(date_list)<2:
        raise ValueError('the list of dates must contain at least 2 dates.')
    DELTA = date_list[1]-date_list[0]
    if DELTA > datetime.timedelta(hours=1):
        date_delta='day'
    else:
        date_delta='hour'
    H = nx.DiGraph(start_date=date_list[0],end_date=date_list[-1],date_delta=date_delta)
    #start_date = pd.datetime(2015,1,1)
    #increment = datetime.timedelta(days=1)
    #end_date = start_date + increment
    G_old = nx.DiGraph()
    for idx,date in enumerate(date_list):
        # Compute the graph layer
        if date_delta == 'day':
            data = time_slice(text_data,date,date+datetime.timedelta(days=1))
        else:
            data = time_slice(text_data,date,date+datetime.timedelta(hours=1))
        G = layer_graph(data,date,date_delta=date_delta)
        degrees = G.degree(weight='weight')
        nx.set_node_attributes(G,'degree',degrees)
        G = drop_edges(G,threshold)
        G.remove_nodes_from(nx.isolates(G)) # get rid of isolated nodes on the layer
        # the color number corresponds to the layer (time)
        color = idx/len(date_list)
        nx.set_node_attributes(G,'color',color)
        # Add the layer to the global graph
        H.add_nodes_from(G.nodes(data=True))
        H.add_edges_from(G.edges(data=True))
        # Connect the layer
        H = connect_layer(H,G_old,G)
        G_old = G
    H.remove_nodes_from(nx.isolates(H))
    print('Nb of edges: {}, nb of nodes: {}.'.format(H.size(),len(H.nodes())))
    return H

def compress_multilayer(graph,threshold=0):
    """ Compress all the weakly connected components of the multilayer graph
        and return a graph union of the compressed components
        compressed components means flattened graphs over the time axis.
        In each component, the nodes appearing over time less than the threshold are discarded
    """
    import networkx as nx
    G_all = nx.DiGraph()
    for cc in nx.weakly_connected_component_subgraphs(graph):
        comp_cc = compress_component(cc,threshold)
        G_all = nx.compose(G_all,comp_cc)
    return G_all

def save_graph(graph,filename):
    from networkx.readwrite import json_graph
    import json
    json_filename = filename
    if graph.size()!=0:
        data = json_graph.node_link_data(graph)
        #,attrs={'source': 'source', 'target': 'target','key': 'key', 'id': 'id', 'nb_occur':'nb_occur','start_time':'start_time','name':'name', 'color':'color'})#,'time_length':'time_length'})
        data['links'] = [
                {
                    'source': data['nodes'][link['source']]['id'],
                    'target': data['nodes'][link['target']]['id']
                }
                for link in data['links']]
        data['name'] = graph.graph['series_name']
        data['start_date'] = graph.graph['start_date']
        data['end_date'] = graph.graph['end_date']
        s = json.dumps(data)
        with open(filename, "w") as f:
            f.write(s)
    else:
        print('====================')
        print('Warning: empty graph')
        print('====================')
        data = json_graph.node_link_data(graph)
        s = json.dumps(data)
        with open(filename, "w") as f:
            f.write(s)


def draw_graph(graph):
    import networkx as nx
    import matplotlib.pyplot as plt
    nx.draw_networkx(graph)
    plt.show()

def web_viz(url):
    """
    open a new tab on the web browser with url 'url' to display the graph
    It is needed to run a webserver in the folder where the json file has been saved
    using for example: python3 -m http.server --bind 127.0.0.1 8008
    """
    import webbrowser
    #webbrowser.open_new_tab(url)
    webbrowser.open_new(url)

def create_cc_id(ccomponent):
    """ create a unique id for the connected component
    """
    node_list = ccomponent.nodes()
    sorted_node_list = sorted(node_list)
    ccomponent_id = sorted_node_list[0] #unique id for the component (can be any node of the component)
    ccomponent_id = encode_cc_id(ccomponent_id)
    return ccomponent_id

def encode_cc_id(component_id):
    """ Return a string encoded in base 64 that do not contain any special character
        and allows to be used as a filename
    """
    import base64
    return base64.urlsafe_b64encode(component_id.encode('UTF-8')).decode('UTF-8')

def decode_cc_id(encoded_id):
    """ Decode the id encoded with 'encode_cc_id'
    """
    import base64
    return base64.urlsafe_b64decode(encoded_id).decode('UTF-8')

def CC_to_df_nodes(ccomponent,date_delta):
    """ Create a dataframe of nodes with their properties to analyse the time evolution of a component
        ccomponent is a graph, connected component of the multilayer graph.
        date_delta = 'day' or 'hour'
        returns: 
        - a dataframe containing node properties as columns
        - a component id that will be used to identify the component
            (this id is also attached to each node of the component)
    """
    import pandas
    df_nodes = pandas.DataFrame()
    ccomponent_id = create_cc_id(ccomponent) #unique id for the component
    for node,data in ccomponent.nodes(data=True):
        df_nodes.loc[node,'id']=node
        df_nodes.loc[node,'name']=data['name']
        if date_delta=='hour':
            df_nodes.loc[node,'hour']=data['timestamp'].hour
        df_nodes.loc[node,'day']=data['timestamp'].day
        df_nodes.loc[node,'month']=data['timestamp'].month
        df_nodes.loc[node,'year']=data['timestamp'].year
        df_nodes.loc[node,'degree']=data['degree']
        df_nodes.loc[node,'cc_id']=ccomponent_id
    df_nodes.day = df_nodes.day.astype(int)
    df_nodes.month = df_nodes.month.astype(int)
    df_nodes.year = df_nodes.year.astype(int)
    df_nodes.degree = df_nodes.degree.astype(int)
    if date_delta=='hour':
        df_nodes.hour = df_nodes.hour.astype(int)
    df_nodes = df_nodes.sort_values('degree',ascending=False)
    ids,indices = df_nodes.name.factorize() # associate a number to each unique node name in the component
    df_nodes['word_id_nb']=ids
    return df_nodes,ccomponent_id

def CC_to_df_edges(ccomponent,date_delta):
    """ Create a dataframe of edges with their properties to analyse the time evolution of a component
        ccomponent is a graph, connected component of the multilayer graph.
        date_delta = 'day' or 'hour'
        returns: 
        - a dataframe containing edges and edges properties as columns
        - a component id that will be used to identify the component
            (this id is also attached to each node of the component)
    """
    import pandas as pd
    import memebox.treegraph as mtg
    df_edges = pd.DataFrame()    
    ccomponent_id = create_cc_id(ccomponent) #unique id for the component
    for (node1,node2,data) in ccomponent.edges(data=True):
        node1_data,node2_data = ccomponent.node[node1],ccomponent.node[node2]
        if (node1_data['timestamp']==node2_data['timestamp']): # if this is an intra-layer edge
            edge_id = node1+'_'+node2
            #print('=='+edge_id)
            df_edges.loc[edge_id,'id']=edge_id
            df_edges.loc[edge_id,'name']=node1_data['name']+' '+node2_data['name']
            if date_delta=='hour':
                df_edges.loc[edge_id,'hour']=node1_data['timestamp'].hour
            df_edges.loc[edge_id,'day']=node1_data['timestamp'].day
            df_edges.loc[edge_id,'month']=node1_data['timestamp'].month
            df_edges.loc[edge_id,'year']=node1_data['timestamp'].year
            df_edges.loc[edge_id,'occur']=data['weight']
            medias = pd.value_counts(data['media_list']).to_dict()
            main_media,media_occur = mtg.get_main_media(medias)
            df_edges.loc[edge_id,'main_media']=main_media
            df_edges.loc[edge_id,'main_media_occur']=media_occur
            df_edges.loc[edge_id,'cc_id']=ccomponent_id
    df_edges.day = df_edges.day.astype(int)
    df_edges.month = df_edges.month.astype(int)
    df_edges.year = df_edges.year.astype(int)
    df_edges.occur = df_edges.occur.astype(int)
    if date_delta=='hour':
        df_edges.hour = df_edges.hour.astype(int)
    df_edges.main_media_occur = df_edges.main_media_occur.astype(int)
    df_edges = df_edges.sort_values('occur',ascending=False)
    ids,indices = df_edges.name.factorize() # associate a number to each unique node name in the component
    df_edges['word_id_nb']=ids # used for the visualization
    return df_edges,ccomponent_id

def extract_components_as_timetables(G,path,items):
    """ Extract the components from the multilayer graph
        and save them in files, inside the path
    """
    for ccomponent in nx.weakly_connected_component_subgraphs(G):
        name_list = [data['name'] for node,data in ccomponent.nodes(data=True)]
        if len(set(name_list))>1: # each component must have nodes with at least 2 distinct names 
            if items=='nodes':
                df,cc_id = CC_to_df_nodes(ccomponent,G.graph['date_delta'])
            elif items=='edges':
                df,cc_id = CC_to_df_edges(ccomponent,G.graph['date_delta'])
            else:
                raise ValueError("items must be 'nodes' or 'edges'.")
            #print(cc_id)
            filename = path+'timecomponent_'+cc_id+'.json'
            print('saving to {}'.format(filename))
            df.to_json(filename,orient='records')