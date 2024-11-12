# %%
import numpy as np
import re
import requests

from article import Article # Relative import from article.py
from os import makedirs

# %%
def main():
    save_volume_titles(path='data')
    save_sources(path='data')
    
    sources = np.load('data/sources.npz')['sources']
    articles = [Article(source) for source in sources]
    articles = sorted(articles, key=lambda article: (article.volume, article.start_page))
    authors_list = [article.authors for article in articles]
    authors = [author for sublist in authors_list for author in sublist]
    
    save_author_ids(authors, path='data')
    save_metadata(articles, path='data')

# %%
def save_volume_titles(*, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    source = requests.get('http://www.tac.mta.ca/tac/').text
    source_iter = (line.strip() for line in source.split('\n'))
    
    reg = re.compile(r'Vol[.] \d+')
    line = next(line for line in source_iter if re.search(reg, line) is not None)
    volume_titles = {}
    
    while re.search(reg, line) is not None:
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
        makedirs(path, exist_ok = True)
    
    metadata = [article.get_XML(i) for i, article in enumerate(articles, 1)]
    
    with open(f'{path}/XML_files.txt', 'w') as f:
        for i, xml in enumerate(metadata, 1):
            f.write(f'ARTICLE NO. {i}:\n')
            f.write(f'{"-" * 92}\n')
            f.write(xml + '\n')
            f.write(f'{"-" * 92}\n\n')
    
    np.savez_compressed(f'{path}/metadata.npz', metadata=metadata)

# %%
main()

# %% For future debugging
# metadata = np.load('data/metadata.npz')['metadata']

# authors = np.load('data/author_ids.npz')['author_ids'].keys()
# authors_temp, idxs = np.unique(authors, return_index=True)
# authors_unique = authors_temp[np.argsort(idxs)]

# family_names = [author.split()[-1] for author in authors_unique]
# repeats = [name for name in family_names if family_names.count(name) > 1]
# flags = [author for author in authors_unique if author.split()[-1] in repeats]

