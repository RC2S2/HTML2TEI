#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://www.vadhajtasok.hu/'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'entry-content content-article'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    article_root = bs.find('div', class_='entry-content content-article')
    info_root = bs.find('div', class_='cs-entry__header-info')
    if article_root is not None:
        if info_root is not None:
            section_date_tag = info_root.find('div', class_='cs-entry__post-meta f16 meta-tiny')
            if section_date_tag is not None:
                section_main = section_date_tag.find('a', class_='meta-categories')
                if section_main is not None:
                    data['sch:articleSection'] = section_main.text.strip()
                else:
                    tei_logger.log('WARNING', f'{url}: SECTION TAG NOT FOUND!')
                date_tag = section_date_tag.find('div', class_='cs-meta-date',
                                                 string=re.compile(r'\d{4}\. .*\d{2}:\d{2}'))
                if date_tag is not None:
                    parsed_date = parse_date(date_tag.text.strip(), '%Y. %B %d. - %H:%M')
                    if parsed_date is not None:
                        data['sch:datePublished'] = parsed_date
                    else:
                        tei_logger.log('WARNING', f'{url}: DATE TEXT FORMAT ERROR!')
                else:
                    tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
            else:
                tei_logger.log('WARNING', f'{url}: SECTION & DATE TAG NOT FOUND!')
            modified_date_tag = info_root.find('span', class_='pk-badge pk-badge-no-danger',
                                               string=re.compile(r'Frissítve! - \d{4}\. .*\d{2}:\d{2}'))
            if modified_date_tag is not None:
                modified_date_text = modified_date_tag.text.replace('Frissítve! - ', '').strip()
                parsed_modified_date = parse_date(modified_date_text,  '%Y. %B %d. - %H:%M')
                if parsed_modified_date is not None:
                    data['sch:dateModified'] = parsed_modified_date
                else:
                    tei_logger.log('WARNING', f'{url}: MODIFIED DATE TEXT FORMAT ERROR!')
            title = info_root.find('h1', class_='cs-entry__title')
            if title is not None:
                article_title = title.find('span')
                data['sch:name'] = article_title.text.strip()
            else:
                tei_logger.log('WARNING', f'{url}: TITLE NOT FOUND IN URL!')
        keywords_root = bs.find('ul', class_='post-categories')
        if keywords_root is not None:
            keywords_list = [t.text.strip() for t in keywords_root.find_all('a', class_='news-tag')]
            if len(keywords_list) > 0:
                data['sch:keywords'] = keywords_list
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
DECOMP = [(('script',), {})]

MEDIA_LIST = [(('table',), {}),
              (('figure',), {}),
              (('img',), {}),
              (('iframe',), {}),
              (('div',), {'class': 'twitter-tweet twitter-tweet-rendered'})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = []

LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
