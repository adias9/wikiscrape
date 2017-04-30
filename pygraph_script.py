import json
# import pygraphviz as pg
import networkx as nx
from matplotlib import pyplot as plt

def loadgraph(fname, labeldict):
        G=nx.Graph()
        with open(fname) as data_file:  
            data = json.load(data_file)
            for line in data:
                if "prev_link" in line:
                    url=line["link"]
                    G.add_node(url)
                    labeldict[url] = line["title"]
                    linked_url=line["prev_link"]
                    G.add_edge(url,linked_url)
                else:
                    url=line["source_link"]
                    linked_url=line["existent_link"]
                    G.add_edge(url,linked_url)
        return G


# This may be useful
# response.request.meta['redirect_urls']
# The urls which the request goes through (while being redirected) can be found in the redirect_urls Request.meta key.
# https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#std:reqmeta-redirect_urls

if __name__=='__main__':
        labeldict = {}
        G=loadgraph("wikiscrape.json", labeldict)
        if G is not None:
            print "graph: %s" % G
        pr = nx.pagerank(G)
        print "pageRank = %s" % pr
        nx.draw(G, labels=labeldict, with_labels = True)
        plt.show()