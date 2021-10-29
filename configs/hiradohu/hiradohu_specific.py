#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re
from os.path import join as os_path_join, dirname as os_path_dirname, abspath as os_path_abspath

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://hirado.hu'


ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'articleContent'}),
                            (('div',), {'class': 'videoPlayer'}),
                            (('div',), {'class': 'newGallery'}),
                            (('article',), {'class': 'article'})]
# (('tagname',), {'attribute_key': 'attribute_value'})

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    meta_root = bs.find('div', class_='articleHead')
    meta_root_vid = bs.find('div', class_='videoInfo')
    meta_root_gallery = bs.find('div', class_='galleryHead')
    meta_root_blog = bs.find('article', class_='article')
    if meta_root is not None:
        date_tag = bs.find('div', class_='artTime')
        if date_tag is not None:
            date_text = date_tag.text.strip()
            if date_text is not None:
                data['sch:datePublished'] = parse_date(date_text, '%Y. %m. %d. - %H:%M')
            else:
                tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        title = meta_root.find('h1')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        author = bs.find('div', class_='artAuthor')
        if author is not None:
            author.decomp('span')
            author_list = [t.strip() for t in author.text.split(',')]
            if author_list is not None:
                data['sch:author'] = author_list
        source = bs.find('div', class_='artSource')
        if source is not None:
            source.decomp('span')
            source_list = [t.strip() for t in source.text.split(',')]
            if source_list is not None:
                data['sch:source'] = source_list
        return data
    elif meta_root_vid is not None:
        title = meta_root_vid.find('h2')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        return data
    elif meta_root_gallery is not None:
        title = meta_root_vid.find('h2')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        return data
    elif meta_root_blog is not None:
        date_tag = meta_root_blog.find('time')
        if date_tag is not None:
            date_text = date_tag.text.strip()
            if date_text is not None:
                data['sch:datePublished'] = parse_date(date_text, '%Y. %B %d.')
            else:
                tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        title = meta_root_blog.find('h1')
        if title is not None:
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        author = meta_root_blog.find('span', class_='identity')
        if author is not None:
            author_list = [t.strip() for t in author.text.split('-')]
            if author_list is not None:
                data['sch:author'] = author_list
            else:
                tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        tag_root = meta_root_blog.find('ul', class_='list-inline')
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
LINKS_SPEC = BASIC_LINK_ATTRS
DECOMP = [(('div',), {'class': 'articleSocial'}),
          (('div',), {'class': 'interestingRecommended'}),
          (('div',), {'class': 'hms-banner-wrapper roadblock'}),
          (('script',), {})]

LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))
MEDIA_LIST = [(('div',), {'class': 'video'}),
              (('div',), {'class': 'galleryContener'}),
              (('div',), {'class': 'galleryHeadContener'}),
              (('div',), {'class': 'hms_fb_post_embed'}),
              (('div',), {'class': 'articlePic aligncenter'}),
              (('div',), {'class': 'live-player-container'}),
              (('div',), {'class': 'twitter-tweet twitter-tweet-rendered'}),
              (('div',), {'role': 'img'}),
              (('div',), {'class': 'embed-container'}),
              (('div',), {'class': 'articlePic articleGallery'}),
              (('div',), {'style': 'display: none;'}),
              (('img',), {}),
              (('iframe',), {})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = [url.strip() for url in open(os_path_join(os_path_dirname(os_path_abspath(__file__)),
                                                           'hiradohu_BLACKLIST.txt')).readlines()]

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
