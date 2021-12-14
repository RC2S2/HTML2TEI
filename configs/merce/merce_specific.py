#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
from os.path import join as os_path_join, dirname as os_path_dirname, abspath as os_path_abspath

from html2tei import parse_date, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://merce.hu'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'main-article-text'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript', 'a',
               'span', 'div', 'p', 'blockquote'}

def get_meta_from_articles_spec(tei_logger, url, bs):
    source_set = {'A Város Mindenkié csoport', 'AVarosMindenkie', 'kps14', 'LeftEast', 'VoB', 'Robin Pajtás Kollektíva',
                  'Közélet iskolája', 'Sixfeet', 'Snowflake', 'Progresszív Internacionálé', 'Napvilág Kiadó',
                  'E.A.S.T.', 'A Város Mindenkié', 'Magyar Helsinki Bizottság', 'Hallgatói Szakszervezet',
                  'Nemzetközi Marxista Irányzat', 'Szolidáris Gazdaság Központ', 'Balraadmin', 'Nemnövekedés Projekt',
                  'Szolidaritási Akciócsoport', 'Angry Workers', 'Másállapotot a szülészetben', 'Autonómia Mozgalom',
                  'Levelező Elvtárs', 'K-Monitor', 'Utcajogász', 'Deviszont Közösségi Tér', 'Green European Journal',
                  'Új Egyenlőség', 'Fridays for Future Magyarország', 'Fridays for Future Csehország',
                  'Forradalmi Forrás', 'Székely és szórvány szituacionisták', 'VOMS', 'Partizán',
                  'NEM! - Nők Egymásért Mozgalom', 'Politikatörténeti Intézet', 'Fordulat',
                  'Önállóan lakni - közösségben élni', 'Rákóczi Kollektíva', 'Szabadságot a röszkei 11-nek!',
                  'MigSzol', 'Helyzet Műhely', 'Mérce'}
    data = tei_defaultdict()
    data['sch:url'] = url
    meta_root = bs.find('div', class_='meta-left')
    tag_root = bs.find('ul', class_='tag-links')
    pp_root = bs.find('div', class_='pplive__posts track-cat')
    if meta_root is not None:
        date_tag = meta_root.find('div', class_='meta-time').find('time')
        if date_tag is not None:
            parsed_date = parse_date(date_tag['title'].strip(), '%Y.%m.%d. %H:%M')
            if parsed_date is not None:
                data['sch:datePublished'] = parsed_date
            else:
                tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        if pp_root is not None:
            # The first found element is the last modification of the coverage, based on the structure of the article
            pp_lastdate_tag = pp_root.find('div', class_='ppitm__time time').find('time')
            if pp_lastdate_tag is not None:
                pp_parsed_date = parse_date(pp_lastdate_tag['title'].strip(), '%Y.%m.%d. %H:%M')
                if pp_parsed_date is not None:
                    data['sch:dateModified'] = pp_parsed_date
                else:
                    tei_logger.log('WARNING', f'{url}: DATE FORMAT ERROR!')
        subsect_tag = bs.find('div', class_='article_description')
        if subsect_tag is not None:
            data['sch:articleSection'] = subsect_tag.text.strip()
        else:
            tei_logger.log('DEBUG', f'{url}: ARTICLE SECTION TAG NOT FOUND!')
        title = bs.find('h1', class_='entry-title')
        if title is not None:
            subtitle = title.find('span', class_='entry-subtitle')
            if subtitle is not None:
                subtitle.extract()
                data['sch:alternateName'] = subtitle.text.strip()
            data['sch:name'] = title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        author_tag = bs.find_all('a', rel='author')
        if author_tag is not None:
            author_list = [t.text.strip() for t in author_tag]
            author_list = list(dict.fromkeys(author_list))
            source_list = []
            for author in author_list:
                if author in source_set:
                    source_list.extend(author)
                    author_list.remove(author)
                elif ' és ' in author:
                    author_duo = author.split(' és ')  # A singular instance of two authors under a single account
                    author_list.remove(author)
                    author_list += author_duo
                data['sch:author'] = author_list
        else:
            tei_logger.log('WARNING', f'{url}: AUTHOR TAG NOT FOUND!')
        if tag_root is not None:
            keywords_list = [t.text.strip() for t in tag_root.find_all('a', {'data-act': 'tag'})]
            if len(keywords_list) > 0:
                data['sch:keywords'] = keywords_list
        else:
            tei_logger.log('WARNING', f'{url}: KEYWORDS TAG NOT FOUND!')
        return data
    else:
        tei_logger.log('WARNING', f'{url}: ARTICLE BODY NOT FOUND OR UNKNOWN ARTICLE SCHEME!')
        return None


def excluded_tags_spec(tag):
    return tag


BLOCK_RULES_SPEC = {}
BIGRAM_RULES_SPEC = {}
LINKS_SPEC = {}
DECOMP = [(('script',), {}),
          (('noscript',), {}),
          (('form',), {}),
          (('div',), {'data-place': 'article_begin'}),
          (('div',), {'data-place': 'article_inside'}),
          (('div',), {'data-place': 'article_text_end'}),
          (('div',), {'data-place': 'pp_inner'}),
          (('div',), {'class': 'attachment-credit'}),
          (('div',), {'class': 'entry-meta single-meta'}),
          (('div',), {'class': 'main-article-footer track-cat'}),
          (('div',), {'data-place': 'pp_begin'}),
          (('div',), {'id': 'pplive__header'}),
          (('div',), {'data-cat': 'pp-key-events'}),
          (('div',), {'id': 'pplive__data'}),
          (('div',), {'id': 'ppitm__meta'}),
          (('div',), {'class': 'template-skeleton'}),
          (('div',), {'class': 'pplive__loadmore-wrap text-center  d-none'})
          ]
MEDIA_LIST = [
    (('figure',), {}),
    (('div',), {'class': 'entry-asset-place asset-placed'}),
    (('div',), {'class': 'entry-asset-wrap entry-asset-iframe '}),
    (('div',), {'class': 'entry-content-asset'}),
    (('iframe',), {})]


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = [url.strip() for url in open(os_path_join(os_path_dirname(os_path_abspath(__file__)),
                                                           'merce_BLACKLIST.txt')).readlines()]
LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))

MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None
