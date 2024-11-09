# %%
import numpy as np
import re
import requests

from datetime import datetime as dt
from io import StringIO

# %%
class Article:
    def __init__(self, source: str):
        self.__set_pdf_src__(source)
        self.__set_title__(source)
        self.__set_authors__(source)
        self.__set_abstract__(source)
        self.__set_keywords__(source)
        self.__set_issue_ident__(source)
        self.__set_page_range__(source)
    
    def __repr__(self):
        return re.sub(f"\[|\]|[']", '', f'{self.authors}, ({self.year})')
    
    def get_XML(self, file_id: int) -> str:
        volume_titles = np.load(
            'data/volume_titles.npz', allow_pickle=True
        )['volume_titles'].item()
        
        author_ids = np.load(
            'data/author_ids.npz', allow_pickle=True
        )['author_ids'].item()
        
        date = dt.now().strftime('%Y-%m-%d')
        filesize = int(requests.head(self.pdf_src).headers['Content-Length'])
        tab = '  '
        
        XML = StringBuilder()
        XML.append('<?xml version="1.0" encoding="utf-8"?>\n')
        XML.append(f'<article PUSHEEN="MEOW" locale="en" date_submitted="{date}" PUSHEEN="MEOW">\n')
        
        XML.append(f'{tab}<id type="internal" advice="ignore">{"MEOW"}</id>\n')
        XML.append(f'{tab}<submission_file PUSHEEN="MEOW" id="{file_id}" PUSHEEN="MEOW">\n')
        XML.append(f'{tab * 2}<name locale="en">{self.pdf_src.split("/")[-1]}</name>\n')
        XML.append(f'{tab * 2}<file id="{file_id}" filesize="{filesize}" extension="pdf">\n')
        XML.append(f'{tab * 3}<href src="{self.pdf_src}"/>\n')
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
            author_id = author_ids[author]
            names = author.split()
            given_name = ' '.join(names[:-1])
            family_name = names[-1]
            XML.append(f'{tab * 3}<author include_in_browse="true" user_group_ref="Author" seq="{i}" id="{author_id}">\n')
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
        volume_title = volume_titles[self.volume]
        if not volume_title.isdigit():
            XML.append(f'{tab * 3}<title locale="en">{volume_title}</title>\n')
        XML.append(f'{tab * 2}</issue_identification>\n')
        XML.append(f'{tab * 2}<pages>{self.start_page}-{self.end_page}</pages>\n')
        
        XML.append(f'{tab}</publication>\n')
        XML.append('</article>\n')
        
        return XML.to_string()
    
    def __set_pdf_src__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
        
        try:
            valid = lambda line: 'citation_pdf_url' not in line
            target = lambda line: re.search(r'\d[.]pdf', line) is not None
            src_line = next(line for line in source_iter if valid(line) and target(line))
        except StopIteration:
            source_iter = (line.strip() for line in source.split('\n'))
            target = lambda line: re.search(r'\d[.](dvi|ps)', line) is not None
            src_line = next(line for line in source_iter if target(line))   
        
        src = src_line.split('"')[1]
        src = re.sub(r'[.](dvi|ps)', '.pdf', src)
        self.pdf_src = src
    
    def __set_title__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
        next(line for line in source_iter if '<title>' in line)
        line = next(source_iter)
        title_lines = []
        
        while '</title>' not in line:
            title_lines.append(line)
            line = next(source_iter)
        
        title = re.sub(' +', ' ', ' '.join(title_lines)).strip(' ,')
        self.title = title
    
    def __set_authors__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
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
        
        self.authors = authors
    
    def __set_abstract__(self, source: str) -> str:
        source_iter = (line.strip() for line in source.split('\n'))
        next(line for line in source_iter if '</h2>' in line)
        next(line for line in source_iter if '<p>' in line)
        line = next(source_iter)
        abstract_lines = []
        
        while '</p>' not in line:
            abstract_lines.append(line)
            line = next(source_iter)
        
        abstract = re.sub(' +', ' ', ' '.join(abstract_lines)).strip()
        self.abstract = abstract
    
    def __set_keywords__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
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
        keywords = [word for word in keywords if word != '']
        
        for i, word in enumerate(keywords):
            if word.endswith('-'):
                keywords[i] = word + keywords[i + 1]
                keywords.pop(i + 1)
        
        self.keywords = keywords
    
    def __set_issue_ident__(self, source: str) -> None:
        source_iter = iter(reversed([line.strip() for line in source.split('\n')]))
        info = next(line for line in source_iter if 'Vol.' in line).split(' ')
        info = [bit.strip(' ,') for bit in info]
        
        vol_idx = info.index('Vol.') + 1
        volume, year = int(info[vol_idx]), info[vol_idx + 1]
        
        if year.startswith('CT'):
            year = int(year[2:])
        else:
            year = int(year)
        
        self.volume, self.year = volume, year
    
    def __set_page_range__(self, source: str) -> None:
        def pp_idxs(line: str) -> tuple[int, int]:
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
        
        source_iter = iter(reversed([line.strip() for line in source.split('\n')]))
        pp_line = next(line for line in source_iter if pp_idxs(line) is not None)
        idxs = pp_idxs(pp_line)
        
        pp_range = pp_line[idxs[0]:idxs[1]].split('-')
        start_page = int(pp_range[0])
        end_page = int(pp_range[-1])
        
        self.start_page, self.end_page = start_page, end_page

# %%
class StringBuilder:
    def __init__(self):
        self._file_str = StringIO()
    
    def append(self, str):
        self._file_str.write(str)
    
    def to_string(self):
        return self._file_str.getvalue()