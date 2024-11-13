# %%
import numpy as np
import re
import requests

from publications import Article, Volume # Relative import from publications.py
from os import makedirs

# %%
def main():
    save_volume_titles(path='data')
    save_sources(path='data')
    
    sources = np.load('data/sources.npz')['sources']
    articles = [Article(source) for source in sources]
    articles = sorted(articles, key=lambda article: (article.volume, article.start_page))
    
    author_lists = [article.authors for article in articles]
    authors = [author for author_list in author_lists for author in author_list]
    save_author_ids(authors, path='data')
    save_metadata(articles, path='data')

# %%
def save_volume_titles(*, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    source = requests.get('http://www.tac.mta.ca/tac/').text
    source_iter = (line.strip() for line in source.split('\n'))
    
    reg = re.compile(r'Vol[.] \d+')
    line = next(line for line in source_iter if re.search(reg, line))
    volume_titles = {}
    
    while re.search(reg, line):
        vol = int(re.search(r'\d+', re.search(reg, line).group()).group())
        title = re.search(r'[-]\s[^<]+</a>', line).group()[2:-4]
        volume_titles[vol] = title
        line = next(source_iter)
    
    volume_titles = dict(reversed(list(volume_titles.items())))
    np.savez_compressed(f'{path}/volume_titles.npz', volume_titles=volume_titles)

# %%
def save_sources(*, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    site = 'http://www.tac.mta.ca/tac/'
    site_source = [line.strip() for line in requests.get(site).text.split('\n')]
    links = np.unique([line.split('"')[1] for line in site_source if 'abs.html' in line])
    sources = [requests.get(site + link).text for link in links]
    np.savez_compressed(f'{path}/sources.npz', sources=sources)

# %%
def save_author_ids(authors: list[str], *, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    author_ids = {}
    author_id = 1
    
    for author in authors:
        if author not in author_ids:
            author_ids[author] = author_id
            author_id += 1
    
    np.savez_compressed(f'{path}/author_ids.npz', author_ids=author_ids)

# %%
def save_metadata(articles: list, *, path: str = '') -> None:
    if path != '':
        makedirs(f'{path}/xml_files', exist_ok = True)
    
    vol_nums = np.load('data/volume_titles.npz',
                       allow_pickle=True)['volume_titles'].item().keys()
    metadata = [''] * len(vol_nums)
    article_iter = iter(articles)
    article = next(article_iter)
    first_id = 1
    
    for vol in vol_nums:
        article_list = []
        ct = 0
        
        while article and article.volume == vol:
            article_list.append(article)
            article = next(article_iter, None)
            ct += 1
        
        metadata[vol - 1] = Volume(article_list, first_id).get_XML()
        first_id += ct
    
    for vol, xml in enumerate(metadata, 1):
        with open(f'{path}/xml_files/TAC_vol{vol}.xml', 'w') as f:
            f.write(xml)
    
    np.savez_compressed(f'{path}/metadata.npz', metadata=metadata)

# %%
main()