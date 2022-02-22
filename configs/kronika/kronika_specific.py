#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab: ts=4 -*

import re

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://kronikaonline.ro/'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'cikkocka'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}

SOURCE = ['Hírösszefoglaló', 'Krónika', 'MTI', 'Székelyhon']


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    article_root = bs.find('div', class_='cikkocka')
    meta_root = bs.find('div', class_='cikktext cikkpage')
    if article_root is not None:
        if meta_root is not None:
            author_date_tag = meta_root.find('div', class_='author')
            if author_date_tag is not None:
                author_tag = author_date_tag.find_all('a')
                if author_tag is not None:
                    a_s_list = [t.text.strip() for t in author_tag]
                    data['sch:author'] = list(set(a_s_list) - set(SOURCE))
                    data['sch:source'] = list(set(a_s_list) & set(SOURCE))
                else:
                    tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
                date_val = re.search(r'(?<!: )\d{4}.+?\d{2}.+?\d{2}:\d{2}', author_date_tag.text.strip())
                moddate_val = re.search(r'(?<=: )\d{4}.+?\d{2}.+?\d{2}:\d{2}', author_date_tag.text.strip())
                if date_val is not None:
                    date_val = date_val.group(0)
                    parsed_date = parse_date(date_val, '%Y. %B %d. %A %H:%M')
                    if parsed_date is not None:
                        data['sch:datePublished'] = parsed_date
                    else:
                        tei_logger.log('WARNING', f'{url}: DATE TEXT FORMAT ERROR!')
                if moddate_val is not None:
                    moddate_val = moddate_val.group(0)
                    parsed_modified_date = parse_date(moddate_val, '%Y. %B %d. %A %H:%M')
                    if parsed_modified_date is not None:
                        data['sch:dateModified'] = parsed_modified_date
                    else:
                        tei_logger.log('WARNING', f'{url}: MODIFIED DATE TEXT FORMAT ERROR!')
            else:
                tei_logger.log('WARNING', f'{url}: AUTHOR & DATE TAG NOT FOUND!')
            title = meta_root.find('h1', class_='menucolor_fr maintitle titlefont')
            if title is not None:
                data['sch:name'] = title.text.strip()
            else:
                tei_logger.log('WARNING', f'{url}: TITLE NOT FOUND IN URL!')
            keywords_root = meta_root.find('div', class_='tags_con1')
            if keywords_root is not None:
                keywords_list = [t.text.strip() for t in keywords_root.find_all('a')]
                if len(keywords_list) > 0:
                    data['sch:keywords'] = keywords_list[:]
            else:
                tei_logger.log('DEBUG', f'{url}: TAGS NOT FOUND!')
            return data
        else:
            tei_logger.log('WARNING', f'{url}: META INFORMATION NOT FOUND!')
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
DECOMP = [(('div',), {'class': 'share_cikk2 share_cikkbox'}),
          (('div',), {'class': 'clear'}),
          (('div',), {'class': 'votenew'}),
          (('div',), {'class': 'bulleti'}),
          (('div',), {'class': 'cikkocka22 addblockp hide-phone'}),
          (('div',), {'class': 'tags_con1'}),
          (('div',), {'class': 'author'}),
          (('h1',), {'class': 'menucolor_fr maintitle titlefont'}),
          (('script',), {})]

MEDIA_LIST = [(('div',), {'class': 'itemsContainer'}),
              (('div',), {'class': 'innernew'}),
              (('table',), {}),
              (('iframe',), {})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = ['https://kronikaonline.ro/erdelyi-hirek/hataron-tuli'
                  '-orvosok-szamara-szerveztek-tovabbkepzest-szegeden']

LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
