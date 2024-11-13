# %%
import numpy as np
import re
import requests

from datetime import datetime as dt
from io import StringIO
from typing import Optional

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
        return re.sub(r"\[|\]|[']", '', f'{self.authors} ({self.year})')
    
    def get_XML_block(self, file_id: int, seq_in_vol: int, vol_title: Optional[str]) -> str:
        date = dt.now().strftime('%Y-%m-%d')
        size = int(requests.head(self.pdf_src).headers['Content-Length'])
        author_ids = np.load('data/author_ids.npz', allow_pickle=True)['author_ids'].item()
        ids_this = [author_ids[author] for author in self.authors]
        t = '  '
        
        out = StringIO()
        out.write(f'{t}<article xmlns="http://pkp.sfu.ca" ' \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="en" ' \
                  'date_submitted="{date}" status="3" submission_progress="" ' \
                  'current_publication_id="1" stage="production" ' \
                  'xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        out.write(f'{t * 2}<id type="internal" advice="ignore">{file_id}</id>\n')
        
        out.write(f'{t * 2}<submission_file ' \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="{file_id}" ' \
                  'created_at="{date}" date_created="" file_id="{file_id}" ' \
                  'stage="submission" updated_at="{date}" viewable="true" ' \
                  'genre="Article Text" source_submission_file_id="{file_id}" ' \
                  'uploader="admin" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        out.write(f'{t * 3}<name locale="en">{self.pdf_src.split("/")[-1]}</name>\n')
        out.write(f'{t * 3}<file id="{file_id}" filesize="{size}" extension="pdf">\n')
        out.write(f'{t * 4}<href src="{self.pdf_src}"/>\n')
        out.write(f'{t * 3}</file>\n')
        out.write(f'{t * 2}</submission_file>\n')
        
        out.write(f'{t * 2}<publication ' \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="MEOW" ' \
                  'status="3" primary_contact_id="{ids_this[0]}" url_path="" ' \
                  'seq="{seq_in_vol}" access_status="0" date_published="{date}" ' \
                  'section_ref="ART" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        
        out.write(f'{t * 3}<id type="internal" advice="ignore">{file_id}</id>\n')
        out.write(f'{t * 3}<id type="doi" advice="update">10.1119/5.0158200</id>\n')
        out.write(f'{t * 3}<title locale="en">{self.title}</title>\n')
        out.write(f'{t * 3}<abstract locale="en">{self.abstract}</abstract>\n')
        out.write(f'{t * 3}<licenseUrl>http://www.tac.mta.ca/tac/consent.html' \
                  '</licenseUrl>\n')
        out.write(f'{t * 3}<copyrightHolder locale="en">author</copyrightHolder>\n')
        out.write(f'{t * 3}<copyrightYear>{self.year}</copyrightYear>\n')
        
        out.write(f'{t * 3}<keywords locale="en">\n')
        for word in self.keywords:
            out.write(f'{t * 4}<keyword>{word}</keyword>\n')
        out.write(f'{t * 3}</keywords>\n')
        
        out.write(f'{t * 3}<authors xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                  'xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        for i, author in enumerate(self.authors):
            author_id = ids_this[i]
            names = author.split()
            given_name = ' '.join(names[:-1])
            family_name = names[-1]
            out.write(f'{t * 4}<author include_in_browse="true" user_group_ref="Author" ' \
                      'seq="{i}" id="{author_id}">\n')
            out.write(f'{t * 5}<givenname locale="en">{given_name}</givenname>\n')
            out.write(f'{t * 5}<familyname locale="en">{family_name}</familyname>\n')
            out.write(f'{t * 5}<email>madeup@email.org</email>\n')
            out.write(f'{t * 4}</author>\n')
        out.write(f'{t * 3}</authors>\n')
        
        out.write(f'{t * 3}<article_galley ' \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="en" ' \
                  'url_path="" approved="false" ' \
                  'xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        out.write(f'{t * 4}<id type="internal" advice="ignore">{file_id}</id>\n')
        out.write(f'{t * 4}<name locale="en">PDF</name>\n')
        out.write(f'{t * 4}<seq>{seq_in_vol}</seq>\n')
        out.write(f'{t * 4}<submission_file_ref id="{file_id}"/>\n')
        out.write(f'{t * 3}</article_galley>\n')
        
        out.write(f'{t * 3}<issue_identification>\n')
        out.write(f'{t * 4}<volume>{self.volume}</volume>\n')
        out.write(f'{t * 4}<year>{self.year}</year>\n')
        if vol_title:
            out.write(f'{t * 4}<title locale="en">{vol_title}</title>\n')
        out.write(f'{t * 3}</issue_identification>\n')
        
        out.write(f'{t * 3}<pages>{self.start_page}-{self.end_page}</pages>\n')
        out.write(f'{t * 2}</publication>\n')
        out.write(f'{t}</article>\n')
        
        return out.getvalue()
    
    def __set_pdf_src__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
        
        try:
            valid = lambda line: 'citation_pdf_url' not in line
            target = lambda line: re.search(r'\d[.]pdf', line)
            src_line = next(line for line in source_iter if valid(line) and target(line))
            src = src_line.split('"')[1]
        except StopIteration:
            source_iter = (line.strip() for line in source.split('\n'))
            target = lambda line: re.search(r'\d[.](dvi|ps)', line)
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
        
        title = re.sub(r'\s+|<p>|</p>', ' ', ' '.join(title_lines)).strip(' ,')
        self.title = title
    
    def __set_authors__(self, source: str) -> None:
        source_iter = (line.strip() for line in source.split('\n'))
        author_lines = []
        next(line for line in source_iter if '</h1>' in line)
        line = next(source_iter)
        
        while line == '' or '<h2>' in line:
            line = next(source_iter)
        
        while '<h2>' not in line and '</h2>' not in line:
            author_lines.append(line)
            line = next(source_iter)
        
        authors = ' '.join(author_lines).replace(' and ', ',').split(',')
        authors = [re.sub(r'\s+', ' ', author.strip(' ,')) for author in authors]
        authors = [author for author in authors if author != '']
        
        if 'Jr.' in authors:
            idx = authors.index('Jr.')
            authors[idx - 1] = f'{authors[idx - 1]}, Jr.'
            authors.pop(idx)
        
        self.authors = authors
    
    def __set_abstract__(self, source: str) -> str:
        source_iter = (line.strip() for line in source.split('\n'))
        next(line for line in source_iter if '</h2>' in line)
        next(line for line in source_iter if '<p>' in line)
        line = next(source_iter)
        abstract_lines = []
        
        while 'Keywords:' not in line:
            abstract_lines.append(line)
            line = next(source_iter)
        
        abstract = re.sub(r'<p>|</p>', ' ', ' '.join(abstract_lines)).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        abstract = re.sub(r'\s<br>\s|\s<br>|<br>\s', '<br>', abstract)
        classif_lines = []
        
        if 'Keywords:' not in line:
            line = next(line for line in source_iter if 'Keywords:' in line)
        
        line = next(line for line in source_iter if '<p>' in line)
        
        if line == '<p>':
            line = next(source_iter)
        
        while '</p>' not in line:
            classif_lines.append(line)
            line = next(source_iter)
        
        if line != '</p>':
            classif_lines.append(line)
        
        classif = re.sub(r'<p>|</p>', ' ', ' '.join(classif_lines)).strip()
        classif = classif.replace(',', ', ')
        classif = re.sub(r'\s+', ' ', classif)
        
        if not classif.endswith('.'):
            classif += '.'
        
        abstract = f'<p>{abstract}</p><p>{classif}</p>'
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
        keywords = re.split(r',|;', keywords_line)
        keywords = [re.sub(r'Keywords:|<p>|</p>', '', word) for word in keywords]
        keywords = [word.strip(' .') for word in keywords]
        keywords = [re.sub(r'\s+', ' ', word) for word in keywords]
        keywords = [re.sub(r'\s[-]\s|[-]\s|\s[-]', '-', word) for word in keywords]
        keywords = [word for word in keywords if word != '']
        
        for i, word in enumerate(keywords):
            if word.endswith('-'):
                keywords[i] = word + keywords[i + 1]
                keywords.pop(i + 1)
        
        self.keywords = keywords
    
    def __set_issue_ident__(self, source: str) -> None:
        source_iter = iter([line.strip() for line in source.split('\n')])
        next(line for line in source_iter if 'Keywords:' in line)
        info = next(line for line in source_iter if 'Vol.' in line).split(' ')
        info = [bit.strip(' ,') for bit in info]
        
        vol_idx = info.index('Vol.') + 1
        volume, year = int(info[vol_idx]), info[vol_idx + 1]
        
        year = int(year[2:]) if year.startswith('CT') else int(year)
        self.volume, self.year = volume, year
    
    def __set_page_range__(self, source: str) -> None:
        def pp_idxs(line: str) -> tuple[int, int]:
            search1 = re.search(r'pp \d+-+\d+', line)
            search2 = re.search(r'pp\d+-+\d+', line)
            search3 = re.search(r'pp[.] \d+-+\d+', line)
            search4 = re.search(r'pp[.]\d+-+\d+', line)
            search5 = re.search(r'pp [.]\d+-+\d+', line)
            
            if search1:
                idxs = (search1.start() + 3, search1.end())
            elif search2:
                idxs = (search2.start() + 2, search2.end())
            elif search3:
                idxs = (search3.start() + 4, search3.end())
            elif search4:
                idxs = (search4.start() + 3, search4.end())
            elif search5:
                idxs = search5.start() + 4, search5.end()
            else:
                idxs = None
            
            return idxs
        
        source_iter = iter(reversed([line.strip() for line in source.split('\n')]))
        pp_line = next(line for line in source_iter if pp_idxs(line))
        idxs = pp_idxs(pp_line)
        pp_range = pp_line[idxs[0]:idxs[1]].split('-')
        
        # Cases where the page range was incorrectly entered in the TAC HTML source
        if self.title == 'Distributive laws for pseudomonads':
            start_page, end_page = 91, 147
        elif self.title == r'An algebraic definition of ($\infty$,n)-categories':
            start_page, end_page = 775, 807
        else:
            start_page, end_page = int(pp_range[0]), int(pp_range[-1])
        
        self.start_page, self.end_page = start_page, end_page

# %%
class Volume:
    def __init__(self, articles: list[Article], first_id: int):
        self.volume = articles[0].volume
        vol_err = 'Each article must be from the same volume.'
        assert all(article.volume == self.volume for article in articles), vol_err
        sort_err = 'Articles must be sorted by page range.'
        assert all(articles[i].start_page < articles[i + 1].start_page
                   for i in range(len(articles) - 1)), sort_err
        
        self.year = articles[0].year
        
        vol_title = np.load('data/volume_titles.npz', allow_pickle=True) \
            ['volume_titles'].item()[self.volume]
        self.title = None if vol_title.isdigit() else vol_title
        
        self.articles = articles
        self.file_ids = list(range(first_id, first_id + len(articles)))
    
    def __repr__(self):
        return (f'Volume {self.volume} - {self.title} ({self.year})' if self.title
                else f'Volume {self.volume} ({self.year})')
    
    def get_XML(self) -> str:
        first_id = self.file_ids[0]
        XML = StringIO()
        XML.write('<?xml version="1.0" encoding="utf-8"?>\n')
        XML.write('<articles xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                  'xsi:schemaLocation="http://pkp.sfu.ca native.xsd">\n')
        XML.write('\n'.join(article.get_XML_block(first_id + i, i, self.title)
                            for i, article in enumerate(self.articles)))
        XML.write('</articles>')
        return XML.getvalue()