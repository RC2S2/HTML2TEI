#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re
from os.path import join as os_path_join, dirname as os_path_dirname, abspath as os_path_abspath

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://magyarnarancs.hu/'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class':'card-body'})]  # (('tagname',), {'attribute_key': 'attribute_value'})
#ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'article-lead'}), (('div',), {'class': 'article-content'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    source_2_dict = {'FIZETETT TARTALOM': 'FIZETETT TARTALOM'}
    #Distinction between source and author is based on the absence of first/last name and the content of source_2_dict
    meta_root = bs.find('div', class_='card-info')
    tag_root = bs.find('ul', class_='tags my-5')
    if meta_root is not None:
        date_tag = meta_root.findAll('li')[-1]
        if date_tag is not None:
            date_text = date_tag.text.strip()
            if date_text is not None:
                data['sch:datePublished'] = parse_date(date_text, '%Y.%m.%d %H:%M')
            else:
                tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        section_tag = meta_root.find('h4', class_='card-topic')
        if section_tag is not None:
            data['sch:articleSection'] = section_tag.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: SECTION TAG NOT FOUND!')
        title = bs.find('h1', class_='card-title')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        subtitle = bs.find('h3', class_='card-subtitle')
        if subtitle is not None:
            data['sch:alternateName'] = subtitle.text.strip()
        author_list = [re.split('[,/]', (t.text.strip())) for t in meta_root.find_all('span', class_='author-name')]
        if author_list is not None:
            flat_author_list = [item for sublist in author_list for item in sublist]
            [data['sch:source'].append(author) if InStr(author, " ") < 1 or author in source_2_dict else
             data['sch:author'].append(author) for author in flat_author_list]
        else:
            tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        if tag_root is not None:
            keywords_list = [t.text.strip() for t in tag_root.find_all('a')]
            if len(keywords_list) > 0:
                data['sch:keywords'] = keywords_list[:]
            else:
                tei_logger.log('WARNING', f'{url}: SUBJECT TAG NOT FOUND!')
        else:
            tei_logger.log('WARNING', f'{url}: SUBJECT TAG NOT FOUND!')
        return data
    else:
        tei_logger.log('WARNING', f'{url}: ARTICLE BODY NOT FOUND OR UNKNOWN ARTICLE SCHEME!')
        return None


def excluded_tags_spec(tag):
    if tag.name not in HTML_BASICS:
        tag.name = 'unwrap'
    tag.attrs = {}
    return tag


BLOCK_RULES_SPEC = {}
BIGRAM_RULES_SPEC = {}
#LINKS_SPEC = BASIC_LINK_ATTRS
LINKS_SPEC = {'a', '0_MDESC_a', 'img', '0_MDESC_img', 'iframe', '0_MDESC_meta', 'div'}
DECOMP = [(('div',), {'class': 'blockquote orange'}),
          (('script',), {}),
          (('div',), {'class': 'share-box'}),
          (('div',), {'class': 'fb-like'}),
          (('div',), {'class': 'banner-wrapper bgr mb-2 mt-2'}),
          (('div',), {'class': 'wrap'}),
          (('div',), {'class': 'fb-like mb-4'}),
          (('h1',), {'class': 'card-title'}),
          (('ul',), {'class': 'tags my-5'}),
          (('div',), {'class': 'card-info'})]

MEDIA_LIST = [(('div',), {'class': 'image image-div inner'}),
              (('div',), {'data-blocktype': 'Cikk_Oldal_Embed'}),
              (('div',), {'class': 'inner-cikkbox cikkbox-img align-left'}),
              (('table',), {})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)

    return article_dec


BLACKLIST_SPEC = [url.strip() for url in open(os_path_join(os_path_dirname(os_path_abspath(__file__)),
                                                           'magyarnarancs_BLACKLIST.txt')).readlines()]

LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
