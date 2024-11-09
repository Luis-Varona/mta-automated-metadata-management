
# %%
import numpy as np
import re
import requests
from os import makedirs

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
    np.savez_compressed(path + '/volume_titles.npz', volume_titles=volume_titles)

# %%
def save_sources(*, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    site = 'http://www.tac.mta.ca/tac/'
    site_source = [line.strip() for line in requests.get(site).text.split('\n')]
    links = np.unique([line.split('"')[1] for line in site_source if 'abs.html' in line])
    sources = [requests.get(site + link).text for link in links]
    np.savez_compressed(path + '/sources.npz', sources=sources)

# %%
def save_author_ids(authors: list[str], *, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    author_ids = {}
    id = 1
    
    for author in authors:
        if author not in author_ids:
            author_ids[author] = id
            id += 1
    
    makedirs(path, exist_ok = True)
    np.savez_compressed(path + '/author_ids.npz', author_ids=author_ids)

# %%
def save_metadata(articles: list, *, path: str = '') -> None:
    if path != '':
        makedirs(path, exist_ok = True)
    
    metadata = [article.get_XML(i) for i, article in enumerate(articles, 1)]
    f = open(path + '/XML_files.txt', 'w')
    
    for i, xml in enumerate(metadata, 1):
        f.write(f'ARTICLE NO. {i}:\n')
        f.write(f'{"-" * 92}\n')
        f.write(xml + '\n')
        f.write(f'{"-" * 92}\n\n')
    
    f.close()
    np.savez_compressed(path + '/metadata.npz', metadata=metadata)