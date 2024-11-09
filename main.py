# %%
import numpy as np
from article import Article
from save_data import save_volume_titles, save_sources, save_author_ids, save_metadata

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

main()

# %% For future debugging
# metadata = np.load('data/metadata.npz')['metadata']
# authors_temp, idxs = np.unique(authors, return_index=True)
# authors_unique = authors_temp[np.argsort(idxs)]
# family_names = [author.split()[-1] for author in authors_unique]
# repeats = [name for name in family_names if family_names.count(name) > 1]
# flags = [author for author in authors_unique if author.split()[-1] in repeats]