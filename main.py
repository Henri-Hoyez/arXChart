from typing import Mapping
import requests
from xml.etree import ElementTree
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import matplotlib.pyplot as plt

import seaborn as sns
sns.set()

import argparse

MAX_ARTICLES = 1000
ARTICLE_PEER_QUERY = 50
TITLES = ['Domain Adaptation', 'Domain adaptation Time Series']
DOMAIN = 'cs.LG'


def process_query(query_url):
    response = requests.get(query_url)
    df = pd.DataFrame(columns=['published','title', 'category'])

    root = ElementTree.fromstring(response.content)
    
    for child in root:
        if 'entry' in child.tag:
            d = {}
            for child_attr in child:
                if "published" in child_attr.tag:
                    #print(child_attr.text)
                    #print(datetime.strptime(child_attr.text, "%Y-%m-%dT%H:%M:%SZ"))
                    d['published'] = datetime.strptime(child_attr.text, "%Y-%m-%dT%H:%M:%SZ")

                if "category" in child_attr.tag:
                    d['category'] = child_attr.attrib['term']

                if 'title' in child_attr.tag:
                    d['title'] = child_attr.text
            df = df.append(d, ignore_index=True)

    return df

def get_publication_dataset(title:str, domain:str, max_article:int=10, article_peer_query:int=50):
    title_words = title.lower().split(' ')
    
    query_title = 'ti:'
    for i in range(len(title_words)):
        word = title_words[i]
        if i < len(title_words) -1:
            query_title += word + '+AND+ti:'
        else:
            query_title += word
                
    url = 'http://export.arxiv.org/api/query?search_query={}+cat:{}&max_results={}'.format(query_title, domain, article_peer_query)
    
    res_df = None
    
    for i in tqdm(range(0, max_article, article_peer_query)):
        query_url = url + "&start={}".format(i)
        
        responce_df = process_query(query_url)
        responce_df['query_title'] = title
        
        if res_df is None:
            res_df = responce_df
        else:
            res_df = res_df.append(responce_df, ignore_index=True)
    return res_df

def show_research_trends(titles:list, domain:str, max_articles, article_peer_query):
    paper_df = None
    
    for title in titles:
        print("[+] Collect article from", title)

        df = get_publication_dataset(title, domain, max_articles, article_peer_query)
        
        if paper_df is None:
            paper_df = df
        else:
            paper_df = paper_df.append(df)
        
    # Make the trends
    paper_df['year'] = paper_df['published'].dt.year
    trends = paper_df.groupby(['query_title', 'year']).count().reset_index()

    plt.figure(figsize=(18,10))
    sns.lineplot(data=trends, x='year', y='published', hue='query_title')
    plt.show()
    


if __name__ == "__main__":
    # Command example:
    # python main.py "Domain Adaptation" "Domain Adaptation Time Series"
    parser = argparse.ArgumentParser(description="Make research trend giving part of paper title ('Domain Adaptation').")
    parser.add_argument('titles', metavar='N', type=str, nargs='+', help='paper titles.')
    parser.add_argument('--domain', type=str, help='paper domain (default: \'cs.LG\').', default='cs.LG')
    parser.add_argument('--max-articles', type=int, help='Specify the maximum number of paper to make the trend.', default=1000)
    parser.add_argument('--paper-peer-query', type=int, help='Specify the maximum paper in one query.', default=50)

    args = parser.parse_args()

    paper_df = show_research_trends(args.titles, args.domain, args.max_articles, args.paper_peer_query)