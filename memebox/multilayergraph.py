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
    # day list
    day_list = [month_list[month-1]+datetime.timedelta(days=n) for n in range(31) 
            if month_list[month-1]+datetime.timedelta(days=n)<month_list[month]]
    start_date=day_list[0].strftime("%d-%m-%Y")
    end_date=day_list[-1].strftime("%d-%m-%Y")
    print('Dates are from {} to {}.'.format(start_date,end_date))
    return day_list

def multilayergraph(text_data,day_list,threshold):
    """ return the multi layer graph of activated components
        in the text_data, over the days of day_list
        The activity below the threshold is not recorded as active:
        threshold = minimal number of occurences during a day
    """
    import datetime
    H = nx.DiGraph(start_date=day_list[0],end_date=day_list[-1])
    #start_date = pd.datetime(2015,1,1)
    #increment = datetime.timedelta(days=1)
    #end_date = start_date + increment
    G_old = nx.DiGraph()
    for idx,day in enumerate(day_list):
        # Compute the graph layer
        data = time_slice(text_data,day,day+datetime.timedelta(days=1))
        G = layer_graph(data,day)
        G = drop_edges(G,threshold)
        # the color number corresponds to the layer (time)
        color = idx/len(day_list)
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
    for c in nx.weakly_connected_component_subgraphs(graph):
        cc = compress_component(c,threshold)
        G_all = nx.compose(G_all,cc)
    return G_all

def save_graph(graph,filename):
    from networkx.readwrite import json_graph
    import json
    json_filename = filename
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
