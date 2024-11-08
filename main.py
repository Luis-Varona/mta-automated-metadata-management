# %%
import numpy as np
import re
import requests

from datetime import datetime as dt
from io import StringIO
from os import makedirs

makedirs('data', exist_ok = True)

# %%
class StringBuilder:
    def __init__(self):
        self._file_str = StringIO()
    
    def append(self, str):
        self._file_str.write(str)
    
    def to_string(self):
        return self._file_str.getvalue()

# %%
def get_volume_titles() -> None:
    resp = requests.get('http://www.tac.mta.ca/tac/')
    source = [line.strip() for line in resp.text.split('\n')]
    source_iter = iter(source)
    
    reg = re.compile(r'Vol[.] \d+')
    line = next(line for line in source_iter if re.search(reg, line) is not None)
    volume_titles = {}
    
    while re.search(reg, line) is not None:
        vol = int(re.search(r'\d+', re.search(reg, line).group()).group())
        title = re.search(r'[-]\s[^<]+</a>', line).group()[2:-4]
        volume_titles[vol] = title
        line = next(source_iter)
    
    volume_titles = dict(reversed(list(volume_titles.items())))
    np.save('data/volume_titles.npy', volume_titles)

get_volume_titles()

def volume_title(n: int) -> str:
    volume_titles = np.load('data/volume_titles.npy', allow_pickle = True).item()
    title = volume_titles[n]
    
    if title.isdigit():
        title = None
    
    return title

# %%
class Article:
    def __init__(self, source: str):
        self.pdf_src = get_pdf_src(source)
        self.title = get_title(source)
        self.authors = get_authors(source)
        self.abstract = get_abstract(source)
        self.keywords = get_keywords(source)
        self.volume, self.year = get_issue_ident(source)
        self.start_page, self.end_page = get_pages(source)
    
    def __repr__(self) -> str:
        return f'{self.authors_to_string()} ({self.year})'
    
    def authors_to_string(self) -> str:
        return str(self.authors)[1:-1].replace("'", '')
    
    def keywords_to_string(self) -> str:
        return str(self.keywords)[1:-1].replace("'", '')
    
    def to_XML(self, file_id: int) -> str:
        date = dt.now().strftime('%Y-%m-%d')
        filesize = int(requests.head(self.pdf_src).headers['Content-Length'])
        vol_title = volume_title(self.volume)
        tab = '  '
        
        XML = StringBuilder()
        XML.append('<?xml version="1.0" encoding="utf-8"?>\n')
        XML.append(f'<article PUSHEEN="MEOW" locale="en" date_submitted="{date}" PUSHEEN="MEOW">\n')
        
        XML.append(f'{tab}<id type="internal" advice="ignore">{"MEOW"}</id>\n')
        XML.append(f'{tab}<submission_file PUSHEEN="MEOW" id="{file_id}" PUSHEEN="MEOW">\n')
        XML.append(f'{tab * 2}<name locale="en">{article.pdf_src.split("/")[-1]}</name>\n')
        XML.append(f'{tab * 2}<file id="{file_id}" filesize="{filesize}" extension="pdf">\n')
        XML.append(f'{tab * 3}<href src="{article.pdf_src}"/>\n')
        XML.append(f'{tab * 2}</file>\n')
        XML.append(f'{tab}</submission_file>\n')
        
        XML.append(f'{tab}<publication PUSHEEN="MEOW">\n')
        
        XML.append(f'{tab * 2}<id type="internal" advice="ignore">{"MEOW"}</id>\n')
        XML.append(f'{tab * 2}<id type="doi" advice="update">{"MEOW"}</id>\n')
        XML.append(f'{tab * 2}<title locale="en">{self.title}</title>\n')
        XML.append(f'{tab * 2}<abstract locale="en">&lt;p&gt;{self.abstract}{"MEOW"}&lt;/p&gt;</abstract>\n')
        XML.append(f'{tab * 2}<licenseUrl>http://www.tac.mta.ca/tac/consent.html</licenseUrl>\n')
        XML.append(f'{tab * 2}<copyrightHolder locale="en">author</copyrightHolder>\n')
        XML.append(f'{tab * 2}<copyrightYear>{self.year}</copyrightYear>\n')
        
        XML.append(f'{tab * 2}<keywords locale="en">\n')
        for word in self.keywords:
            XML.append(f'{tab * 3}<keyword>{word}</keyword>\n')
        XML.append(f'{tab * 2}</keywords>\n')
        
        XML.append(f'{tab * 2}<authors PUSHEEN="MEOW">\n')
        for i, author in enumerate(self.authors):
            names = author.split()
            given_name = ' '.join(names[:-1])
            family_name = names[-1]
            XML.append(f'{tab * 3}<author include_in_browse="true" user_group_ref="Author" seq="{i}" id="{get_author_id(author)}">\n')
            XML.append(f'{tab * 4}<givenname locale="en">{given_name}</givenname>\n')
            XML.append(f'{tab * 4}<familyname locale="en">{family_name}</familyname>\n')
            XML.append(f'{tab * 4}<email>{"MEOW"}</email>\n')
            XML.append(f'{tab * 3}</author>\n')
        XML.append(f'{tab * 2}</authors>\n')
        
        XML.append(f'{tab * 2}<article_galley PUSHEEN="MEOW">\n')
        XML.append(f'{tab * 3}<id type="internal" advice="ignore">{"MEOW"}</id>\n')
        XML.append(f'{tab * 3}<name locale="en">PDF</name>\n')
        XML.append(f'{tab * 3}<seq>{"MEOW"}</seq>\n')
        XML.append(f'{tab * 3}<submission_file_ref id="{file_id}"/>\n')
        XML.append(f'{tab * 2}</article_galley>\n')
        
        XML.append(f'{tab * 2}<issue_identification>\n')
        XML.append(f'{tab * 3}<volume>{self.volume}</volume>\n')
        XML.append(f'{tab * 3}<year>{self.year}</year>\n')
        if vol_title is not None:
            XML.append(f'{tab * 3}<title locale="en">{volume_title(self.volume)}</title>\n')
        XML.append(f'{tab * 2}</issue_identification>\n')
        XML.append(f'{tab * 2}<pages>{self.start_page}-{self.end_page}</pages>\n')
        
        XML.append(f'{tab}</publication>\n')
        XML.append('</article>\n')
        
        return XML.to_string()

# %%
def get_abstract_sources() -> list[str]:
    site = 'http://www.tac.mta.ca/tac/'
    resp = requests.get(site)
    site_source = [line.strip() for line in resp.text.split('\n')]
    
    links = [line.split('"')[1] for line in site_source if 'abs.html' in line]
    links = np.unique(links)
    
    sources = [requests.get(site + link).text.split('\n') for link in links]
    return sources

# %%
def get_pdf_src(source: str) -> str:
    source_iter = iter([line.strip() for line in source])
    
    try:
        valid = lambda line: 'citation_pdf_url' not in line
        target = lambda line: re.search(r'\d[.]pdf', line) is not None
        src_line = next(line for line in source_iter if valid(line) and target(line))
    except StopIteration:
        source_iter = iter([line.strip() for line in source])
        target = lambda line: re.search(r'\d[.](dvi|ps)', line) is not None
        src_line = next(line for line in source_iter if target(line))   
    
    src = src_line.split('"')[1]
    src = re.sub(r'[.](dvi|ps)', '.pdf', src)
    return src

# %%
def get_title(source: str) -> str:
    source_iter = iter([line.strip() for line in source])
    next(line for line in source_iter if '<title>' in line)
    line = next(source_iter)
    title_lines = []
    
    while '</title>' not in line:
        title_lines.append(line)
        line = next(source_iter)
    
    title = re.sub(' +', ' ', ' '.join(title_lines)).strip(' ,')
    return title

# %%
def get_authors(source: str) -> list[str]:
    source_iter = iter([line.strip() for line in source])
    next(line for line in source_iter if '<h2>' in line)
    line = next(source_iter)
    author_lines = []
    
    while '</h2>' not in line:
        author_lines.append(line)
        line = next(source_iter)
    
    authors = ' '.join(author_lines).replace(' and ', ',').split(',')
    authors = [re.sub(r'\s+', ' ', author.strip(' ,')) for author in authors]
    authors = [author for author in authors if author != '']
    authors = [re.sub(r'(?<=[A-Z])[.](?=[A-Z])', '. ', author) for author in authors]
    
    if 'Jr.' in authors:
        idx = authors.index('Jr.')
        authors[idx - 1] = authors[idx - 1] + ', Jr.'
        authors.pop(idx)
    
    return authors

# %%
def get_abstract(source: str) -> str:
    source_iter = iter([line.strip() for line in source])
    next(line for line in source_iter if '</h2>' in line)
    next(line for line in source_iter if '<p>' in line)
    line = next(source_iter)
    abstract_lines = []
    
    while '</p>' not in line:
        abstract_lines.append(line)
        line = next(source_iter)
    
    abstract = re.sub(' +', ' ', ' '.join(abstract_lines)).strip()
    return abstract

# %%
def get_keywords(source: str) -> list[str]:
    source_iter = iter([line.strip() for line in source])
    line = next(line for line in source_iter if 'Keywords:' in line)
    keyword_lines = []
    
    if line.endswith('Keywords:'):
        line = next(source_iter)
    
    while '</p>' not in line:
        keyword_lines.append(line)
        line = next(source_iter)
    
    keywords_line = ' '.join(keyword_lines)
    keywords = [word for word in re.split(r',|;', keywords_line)]
    keywords = [word.replace('Keywords:', ',') for word in keywords]
    keywords = [word.strip(' ,;.') for word in keywords]
    keywords = [re.sub(r'\s+|[\"]|[\']', ' ', word) for word in keywords]
    keywords = [word.replace('- ', '-') for word in keywords]
    
    try:
        keywords.remove('')
    except ValueError:
        pass
    
    for i, word in enumerate(keywords):
        if word.endswith('-'):
            keywords[i] = word + keywords[i + 1]
            keywords.pop(i + 1)
    
    return keywords

# %%
def get_issue_ident(source: str) -> tuple[int, int]:
    source_iter = iter(reversed([line.strip() for line in source]))
    info = next(line for line in source_iter if 'Vol.' in line).split(' ')
    info = [bit.strip(' ,') for bit in info]
    
    vol_idx = info.index('Vol.') + 1
    volume, year = int(info[vol_idx]), info[vol_idx + 1]
    
    if year.startswith('CT'):
        year = int(year[2:])
    else:
        year = int(year)
    
    return volume, year

# %%
def get_pages(source: str) -> tuple[int, int]:
    def pp_idxs(line : str) -> tuple[int, int]:
        search1 = re.search(r'pp \d+-+\d+', line)
        search2 = re.search(r'pp\d+-+\d+', line)
        search3 = re.search(r'pp[.] \d+-+\d+', line)
        search4 = re.search(r'pp[.]\d+-+\d+', line)
        search5 = re.search(r'pp [.]\d+-+\d+', line)
        
        if search1 is not None:
            idxs = search1.start() + 3, search1.end()
        elif search2 is not None:
            idxs = search2.start() + 2, search2.end()
        elif search3 is not None:
            idxs = search3.start() + 4, search3.end()
        elif search4 is not None:
            idxs = search4.start() + 3, search4.end()
        elif search5 is not None:
            idxs = search5.start() + 4, search5.end()
        else:
            idxs = None
        
        return idxs
    
    source_iter = iter(reversed([line.strip() for line in source]))
    pp_line = next(line for line in source_iter if pp_idxs(line) is not None)
    idxs = pp_idxs(pp_line)
    
    pp_range = pp_line[idxs[0]:idxs[1]].split('-')
    start_page = int(pp_range[0])
    end_page = int(pp_range[-1])
    
    return start_page, end_page

# %%
sources = get_abstract_sources()
comparator = lambda article: (article.volume, article.start_page)
articles = [Article(source) for source in sources]
articles = sorted(articles, key = comparator)

# %%
authors_list = [article.authors for article in articles]
authors = [author for sublist in authors_list for author in sublist]

def save_author_ids(authors: list[str]) -> None:
    author_ids = {}
    id = 1
    
    for author in authors:
        if author not in author_ids:
            author_ids[author] = id
            id += 1
    
    np.save('data/author_ids.npy', author_ids)

save_author_ids(authors)

def get_author_id(author: str) -> int:
    author_ids = np.load('data/author_ids.npy', allow_pickle = True).item()
    return author_ids[author]

# %%
f = open('data/article_metadata.txt', 'w')

for article in articles:
    f.write(f'File source: {article.pdf_src}\n')
    f.write(f'Title: {article.title}\n')
    f.write(f'Authors: {article.authors_to_string()}\n')
    f.write(f'Abstract: {article.abstract}\n')
    f.write(f'Keywords: {article.keywords_to_string()}\n')
    f.write(f'Vol. {article.volume}, {article.year}, ')
    f.write(f'pp. {article.start_page}-{article.end_page}\n\n')

f.close()

# %%
f = open('data/XML_files.txt', 'w')

for i, article in enumerate(articles):
    f.write(f'FILE #{i + 1}:\n')
    f.write(f'{"-" * 80}\n')
    f.write(article.to_XML(i + 1))
    f.write(f'{"-" * 80}\n\n')

f.close()

# %%
authors_temp, idxs = np.unique(authors, return_index = True)
authors_unique = authors_temp[np.argsort(idxs)]
family_names = [author.split()[-1] for author in authors_unique]
repeats = [name for name in family_names if family_names.count(name) > 1]
flags = [author for author in authors_unique if author.split()[-1] in repeats]