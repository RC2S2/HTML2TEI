#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://hang.hu'

ARTICLE_ROOT_PARAMS_SPEC = [(('article',), {'class': 'post-wrap post-single mt-3 icms-content'}),
                            (('article',), {'class': 'post-wrap post-single wide mt-3 icms-content'})]


HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe'}


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    article_root = bs.find('article')
    if article_root is not None:
        date_tag = article_root.find('ul', class_='d-flex flex-row')
        if date_tag is not None:
            date_tag = date_tag.find_all('li')[1]
            if date_tag is not None:
                article_date_text = date_tag.text
                if article_date_text is not None:
                    parsed_date = parse_date(article_date_text, '%Y. %B %d., %H:%M')
                    if parsed_date is not None:
                        data['sch:datePublished'] = parsed_date
                    else:
                        tei_logger.log('WARNING', f'{url}: DATE TEXT FORMAT ERROR!')
                else:
                    tei_logger.log('WARNING', f'{url}: DATE TEXT NOT FOUND!')
            else:
                tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        # data['sch:dateModified'] = write_it
        # else: tei_logger.log('WARNING', f'{url}: MODIFIED DATE TEXT FORMAT ERROR!')
        author_tag = article_root.find('span', class_='author-name')
        if author_tag is not None:
            author_text = author_tag.text
            if author_text is not None:
                author_text = author_text.strip()
                if author_text == 'Magyar Hang':
                    data['sch:source'] = [author_text]
                else:
                    data['sch:author'] = author_text.split(',')
            else:
                tei_logger.log('WARNING', f'{url}: AUTHOR TEXT NOT FOUND!')
        else:
            tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        name_tag = article_root.find('div', class_='entry-title')
        if name_tag is not None:
            name_text = name_tag.h1.text
            if name_text is not None:
                data['sch:name'] = name_text.strip()
            else:
                tei_logger.log('WARNING', f'{url}: TITLE TEXT NOT FOUND IN URL!')
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND IN URL!')
        section_line = article_root.find('div', class_='entry-meta')
        if section_line is not None:
            sections = [a.text for a in section_line.find_all('a') if a is not None]
            if sections is not None:
                data['sch:articleSection'] = sections
            else:
                tei_logger.log('DEBUG', f'{url}: SECTION TEXT NOT FOUND!')
        else:
            tei_logger.log('DEBUG', f'{url}: SECTION TAG NOT FOUND!')
        keywords_line = article_root.find('div', class_='widget widget-tags mb-5')
        if keywords_line is not None:
            keywords_sections = [a.text.strip() for a in section_line.find_all('a') if a is not None]
            if keywords_sections is not None:
                data['sch:keywords'] = keywords_sections
            else:
                tei_logger.log('DEBUG', f'{url}: KEYWORDS TEXT NOT FOUND!')
        else:
            tei_logger.log('DEBUG', f'{url}: KEYWORDS TAG NOT FOUND!')
        # else: tei_logger.log('WARNING', f'{url}: TAGS NOT FOUND!')
        return data
        # tei_logger.log('WARNING', f'{url}: METADATA CONTAINER NOT FOUND!')
        # tei_logger.log('WARNING', f'{url}: ARTICLE BODY NOT FOUND!')
        # return None
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
DECOMP = [(('div',), {'class': 'widget'}),
          (('div',), {'class': 'widget-tamogatas-box'}),
          (('div',), {'class': 'banner-wrapper'}),
          (('div',), {'id': 'videoad'}),
          (('div',), {'class': 'widget widget-tamogatas-box'}),
          (('div',), {'class': 'banner-wrapper'}),
          (('div',), {'class': 'img-container'}),
          (('div',), {'id': 'pa_videoslider'}),
          (('div',), {'id': 'widget-image'}),
          (('div',), {'class': 'sidebar-col'}),
          (('div',), {'class': 'entry-meta'}),
          (('div',), {'class': 'entry-image'}),
          (('div',), {'class': 'oygrvhab'}),
          (('script',), {}),
          (('iframe',), {})]

MEDIA_LIST = []


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = ['https://hang.hu/kultura/reg-keszult-olyan-felkavaro-kamaszokrol-szolo-sorozat-mint-az-euforia-'
                  '107933']  # just a picture

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
