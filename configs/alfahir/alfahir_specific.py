#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re
from os.path import join as os_path_join, dirname as os_path_dirname, abspath as os_path_abspath

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://alfahir.hu'


# (('tagname',), {'attribute_key': 'attribute_value'})
ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'region region-content'})]
HTML_BASICS = {'p', 'h1', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'blockquote', 'div', 'wbr', 
               'figure', 'iframe', 'script', 'noscript', 'a', 'span'}


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    source_dict = {"Alfahír": "Alfahír"}
    data['sch:url'] = url
    article_root = bs.find('div', class_='article-content-elements')
    percrol_root = bs.find('div', class_='group-right')
    author_root = bs.find('div', class_='field--items')
    tag_root = bs.find('div', class_='field field--name-field-tags'
                                     ' field--type-entity-reference field--label-hidden field--items')
    if article_root is not None:
        if percrol_root is not None:
            percrol_h4_title = bs.find_all('h4', class_='esemeny-title')
            percrol_h4_author = list(set(bs.find_all('h4')) - set(percrol_h4_title))
            if percrol_h4_author is not None:
                authors_perc_list = list(dict.fromkeys([t.text.strip() for t in percrol_h4_author]))
                if authors_perc_list is not None:
                    data['sch:source'] = set(authors_perc_list).intersection(source_dict)
                    data['sch:author'] = list(set(authors_perc_list) - set(data['sch:source']))
                else:
                    tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
            else:
                tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        date_tag = bs.find('div', class_='article-dates')
        if date_tag is not None:
            date_text = date_tag.text.strip()
            if date_text is not None:
                data['sch:datePublished'] = parse_date(date_text.replace(' |', ''), '%Y. %B %d. %H:%M')
            else:
                tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        title = bs.find('h1', class_='page-title')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        if author_root is not None:
            author_list = [t.text.strip() for t in author_root.find_all('h4')]
            if author_list is not None:
                source_temp = list(set(author_list).intersection(source_dict))
                data['sch:author'] = list(set(author_list)-set(source_temp))
        if tag_root is not None:
            keywords_list = [t.text.strip() for t in tag_root.find_all('a')]
            if len(keywords_list) > 0:
                data['sch:keywords'] = keywords_list[:]
        else:
            tei_logger.log('DEBUG', f'{url}: TITLE TAG NOT FOUND!')
        source_intext_1 = article_root.find('div', class_='field field--name-field-forras'
                                                          ' field--type-string field--label-inline')
        if source_intext_1 is not None:
            data['sch:source'] = source_intext_1.find('div', class_='field--item').text.strip()
        else:
            tei_logger.log('DEBUG', f'{url}: SOURCE TAG NOT FOUND!')
        if len(article_root.find_all("p")) > 0:
            source_intext_2 = article_root.find_all("p")[-1].text.strip()
            if len(source_intext_2) > 0:
                if source_intext_2[0] == '(' and source_intext_2[-1] == ')':
                    data['sch:source'] = source_intext_2[1:-1]
                elif ' - ' in source_intext_2:
                    data['sch:source'] = source_intext_2.strip()
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
LINKS_SPEC = BASIC_LINK_ATTRS
DECOMP = [(('div',), {'class': 'article-footer'}),
          (('script',), {}),
          (('noscript',), {}),
          (('div',), {'class': 'article-dates'}),
          (('div',), {'class': 'field field-name-field-media-index-foto-video'}),
          (('div',), {'class': 'field field--name-dynamic-token-fieldnode-fb-buttons field--type-ds'
                               ' field--label-hidden field--item'}),
          (('div',), {'class': 'article-content-authors'}),
          (('div',), {'class': 'field field--name-dynamic-copy-fieldnode-fb-buttons2 field--type-ds'
                               ' field--label-hidden field--item'}),
          (('div',), {'class': 'field field--name-dynamic-token-fieldnode-minute-html-hook'
                               ' field--type-ds field--label-hidden field--item'}),
          (('div',), {'class': 'field field--name-dynamic-block-fieldnode-legolvasottabbak'
                               ' field--type-ds field--label-above'}),
          (('div',), {'class': 'group-left'}),
          (('div',), {'class': 'group-header'}),
          (('div',), {'class': 'group-footer'}),
          (('h4',), {'class': 'esemeny-title'}),
          (('ins',), {}),
          (('div',), {'class': 'advert_block advert_wrapper advert_mobile mobiladvert4'}),
          (('div',), {'class': 'advert_block advert_wrapper leaderboard2 advert_dektop'}),
          (('section',), {}),
          (('div',), {'class': 'article-content-authors'}),
          (('div',), {'class': 'fb-like'}),
          (('div',), {'class': 'view-header'})]

LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))
MEDIA_LIST = [(('iframe',), {}),
              (('div',), {'class': 'fb-page fb_iframe_widget'}),
              (('blockquote',), {'class': 'embedly-card'}),
              (('img',), {}),
              (('figure',), {}),
              (('div',), {'class': 'fb-page fb_iframe_widget'}),
              (('div',), {'class': 'video-embed-field-provider-youtube video-embed-field-responsive-video form-group'})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = [url.strip() for url in open(os_path_join(os_path_dirname(os_path_abspath(__file__)),
                                                           'alfahir_BLACKLIST.txt')).readlines()]

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
