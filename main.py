# %%
import gzip
import pickle
import re
import requests

from publications import Article, Volume # Relative imports from publications.py
from os import makedirs

# %%
def main():
    save_volume_titles(path='data')
    save_sources(path='data')
    
    with gzip.open('data/sources.gz', 'rb') as f:
        sources = pickle.load(f)
    
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
    
    with gzip.open(f'{path}/volume_titles.gz', 'wb') as f:
        pickle.dump(volume_titles, f)

# %%
def save_sources(*, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    site = 'http://www.tac.mta.ca/tac/'
    
    with requests.Session() as session:
        site_source = [line.strip() for line in session.get(site).text.split('\n')]
        links = {line.split('"')[1] for line in site_source if 'abs.html' in line}
        sources = [session.get(f'{site}{link}').text for link in links]
    
    with gzip.open(f'{path}/sources.gz', 'wb') as f:
        pickle.dump(sources, f)

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
    
    with gzip.open(f'{path}/author_ids.gz', 'wb') as f:
        pickle.dump(author_ids, f)

# %%
def save_metadata(articles: list, *, path: str = '') -> None:
    if path != '':
        makedirs(f'{path}/xml_files', exist_ok = True)
    
    with gzip.open('data/volume_titles.gz', 'rb') as f:
        vol_nums = pickle.load(f).keys()
    
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
    
    with gzip.open(f'{path}/metadata.gz', 'wb') as f:
        pickle.dump(metadata, f)

# %%
main()