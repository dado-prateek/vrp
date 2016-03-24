#!/usr/bin/env python3

import logging
import os
import json
import time
import random
import datetime
import string
import urllib.parse

import requests
from lxml import html


DOWNLOAD_PATH = '~/Downloads'
VIDEOS_URL = 'https://virtualrealporn.com/videos/'

COVERS_DIR = 'covers'
COOKIES_JSON_PATH = 'cookies.json'

TIMEOUT = 15
MAX_RETRY = 3

DETAIL_PAGES_XPATH = '//a[@class="w-portfolio-item-anchor"]/attribute::href'

TITLE_XPATH = '//div[@class="w-pagehead"]/h1/text()|//div[@class="w-pagehead"]/p/text()'
COVERS_XPATH = '//img[@class="attachment-gallery-full size-gallery-full"]/attribute::src'

DESIRED_FORMATS = {
    'Best': '//table[@class="downloads"]/tbody/tr[2]/td/a/attribute::href',
    'Android': '//tr[td/strong[text()="Android / iOS"]]/following-sibling::tr[1]/td/a/attribute::href',
    # 'All': '//table[@class="downloads"]/tbody/tr/td/a/attribute::href',
}


log_format = '%(asctime)16s %(levelname)6s %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    site_name = urllib.parse.urlsplit(VIDEOS_URL).netloc
    download_dir = safe_path_join(os.path.expanduser(DOWNLOAD_PATH),
                                  site_name)
    log.info('Starting grabbing {} into {}'.format(VIDEOS_URL, download_dir))

    cookies = json.load(open(COOKIES_JSON_PATH))
    page = with_retry(requests.get, VIDEOS_URL, cookies=cookies, timeout=TIMEOUT)
    tree = html.fromstring(page.content)
    detail_pages = tree.xpath(DETAIL_PAGES_XPATH)

    for url in detail_pages:
        time.sleep(random.random() + 2)

        info = get_video_page_info(url, cookies)
        videos_dir = safe_path_join(download_dir, info['title'])
        covers_dir = safe_path_join(videos_dir, COVERS_DIR)
        os.makedirs(covers_dir, exist_ok=True)

        for cover_url in info['cover_urls']:
            with_retry(download_file, cover_url, covers_dir, cookies)

        for video_url in info['video_urls']:
            with_retry(download_file, video_url, videos_dir, cookies)


def get_video_page_info(page_url, cookies):
    info = {
        'video_urls': [],
        'cover_urls': [],
    }

    try:
        page = with_retry(requests.get, page_url, cookies=cookies, timeout=TIMEOUT)
        tree = html.fromstring(page.content)

        info['title'] = '{} ({})'.format(*tree.xpath(TITLE_XPATH))

        for name, xpath in DESIRED_FORMATS.items():
            try:
                info['video_urls'].append(tree.xpath(xpath)[0])
            except IndexError:
                log.warn('No format "{}" for video {}'.format(name, title))
        info['cover_urls'] =  tree.xpath(COVERS_XPATH)

    except:
        log.exception('Unhandled error on page {}'.format(page_url))

    return info


def download_file(src_url, dst_dir, cookies=None):
    log.info('Downloading file: {}'.format(src_url))
    fp = os.path.join(dst_dir, src_url.split('/')[-1])

    if os.path.exists(fp):
        log.info('File exists, skipping')
        return
    else:
        try:
            r = requests.get(src_url, cookies=cookies, stream=True, timeout=TIMEOUT)
            with open(fp, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except:
            os.unlink(fp)
            raise


def safe_path_join(*args):
    return safe_path(os.path.join(*args))


def safe_path(path):
    path = path.replace('&', 'and')
    valid_chars = '-_.()/\ {}{}'.format(string.ascii_letters, string.digits)
    return ''.join(c for c in path if c in valid_chars)


def with_retry(func, *args, **kwargs):
    retry_count = 0
    while retry_count < MAX_RETRY:
        try:
            return func(*args, **kwargs)
        except:
            log.exception('Try failed with exception:')
            retry_count += 1
            log.info('Retrying ({})'.format(retry_count))
            
    raise Exception('MAX_RETRY count exeeded')
                      

if __name__ == '__main__':
    main()
