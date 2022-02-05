#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://hvg.hu/'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'article-main'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}


SOURCE_LIST = ['hvg.hu', 'MTI', 'Marabu', 'HVG', 'Eduline', 'Reuters', 'honvedelem.hu', 'BBC', 'Euronews', 'EUrologus',
               'OS', 'Dow Jones', 'DPA', 'DW', 'Hszinhua', 'MTA', 'AP', 'AFP', 'HVG Konferencia', 'Zgut Edit',
               'Index', 'foodnetwork', 'mult-kor.hu', 'MT Zrt.', 'élelmiszer online', 'atlatszo.blog.hu',
               'Blikk', 'HVG Extra Business', 'Origo', 'Bors', '- esel -', 'Magyar Nemzet', 'EFE', 'merites.hu',
               'Népszabadság', 'Inforádió', 'HVG Extra Pszichológia', 'MTI-OS', 'MLF', 'ITAR-TASZSZ', 'MNO',
               'MR1-Kossuth Rádió', 'HavariaPress', 'CNN', 'Bank360.hu', 'Bankmonitor.hu']


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    article_root = bs.find('div', class_='article-content')
    info_root = bs.find('div', class_='info')
    if article_root is not None:
        if info_root is not None:
            date_tag = bs.find('time', class_='article-datetime')
            if date_tag is not None:
                # parsed_date = parse_date(article_date_text, '%Y. %B %d. %A %H:%M')
                parsed_date = parse_date(date_tag['datetime'].strftime('%Y. %B %d. %A %H:%M'), '%Y. %B %d. %A %H:%M')
                if parsed_date is not None:
                    data['sch:datePublished'] = parsed_date
                else:
                    tei_logger.log('WARNING', f'{url}: DATE TEXT FORMAT ERROR!')
            else:
                tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
            modified_date_tag = bs.find('time', class_='lastdate')
            if modified_date_tag is not None:
                # parsed_modified_date = parse_date(modified_date_text, '%Y. %m. %d. %H:%M')
                parsed_modified_date = parse_date(modified_date_tag['datetime'].strftime('%Y. %B %d. %A %H:%M'),
                                                  '%Y. %B %d. %A %H:%M')
                if parsed_modified_date is not None:
                    data['sch:dateModified'] = parsed_modified_date
                else:
                    tei_logger.log('WARNING', f'{url}: MODIFIED DATE TEXT FORMAT ERROR!')
            section_main = info_root.find('a')
            if section_main is not None:
                data['sch:articleSection'] = section_main.text.strip()
            else:
                tei_logger.log('WARNING', f'{url}: SECTION TAG NOT FOUND!')
        else:
            tei_logger.log('WARNING', f'{url}: INFO BLOCK NOT FOUND!')
        title = article_root.find('div', class_='article-title article-title')
        if title is not None:
            article_title = title.find('h1')
            data['sch:name'] = article_title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE NOT FOUND IN URL!')
        author = article_root.find('div', class_='author-name')
        if author is not None:
            author = author.button.decompose()
            author_raw = author.text.strip().replace(' - ', '/')
            if author_raw == 'Vértessy Péter / Brüsszel':
                a_s_list = ['Vértessy Péter / Brüsszel']
            else:
                a_s_list = author.split('/')
                a_s_list = [i.strip() for i in a_s_list]
            data['sch:author'] = list(set(a_s_list) - set(SOURCE_LIST))
            data['sch:source'] = list(set(a_s_list) & set(SOURCE_LIST))
        else:
            tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        keywords_root = article_root.find('div', class_='article-tags')
        if keywords_root is not None:
            keywords_list = [t.text.strip() for t in keywords_root.find_all('a')]
            if len(keywords_list) == 1:
                data['sch:subsection'] = keywords_list
            elif len(keywords_list) > 1:
                data['sch:subsection'] = keywords_list[:1]
                data['sch:keywords'] = keywords_list[1:]
        else:
            tei_logger.log('DEBUG', f'{url}: TAGS NOT FOUND!')
        return data
    else:
        tei_logger.log('WARNING', f'{url}: ARTICLE BODY NOT FOUND!')
        return None


def excluded_tags_spec(tag):
    if tag.name not in HTML_BASICS:
        tag.name = 'else'
    tag.attrs = {}
    return tag


BLOCK_RULES_SPEC = {}
BIGRAM_RULES_SPEC = {}
LINKS_SPEC = BASIC_LINK_ATTRS
DECOMP = [(('script',), {}),
          (('div',), {'class': 'placeholder-ad'}),
          (('div',), {'class': 'article-series-box'})
          ]
LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))
MEDIA_LIST = [(('div',), {'class': 'article-img-holder  '}),
              (('div',), {'class': 'embed-container'}),
              (('div',), {'class': 'content video-container'}),
              (('div',), {'class': 'embedly-card'}),
              (('iframe',), {}),
              ]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = ['https://hvg.hu/360/20210704_Hatvanpuszta_major_orban_Viktor_orban_Gyozo',
                  'https://hvg.hu/360/20200217_Orbanertekeles_2020',
                  'https://hvg.hu/360/20190619_Koszeg_Ferenc_velemeny']

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
