#!/usr/bin/env python3

import logging
import os
import json
import requests
import time
import random
import datetime
import string
from lxml import html


DOWNLOAD_PATH = 'videos'
VIDEOS_URL = 'https://virtualrealporn.com/videos/'
COOKIES_JSON_PATH = 'cookies/vrp-cookies.json'

TIMEOUT = 15
MAX_RETRY = 3

DETAIL_PAGES_XPATH = '//a[@class="w-portfolio-item-anchor"]/attribute::href'

TITLE_XPATH = '//div[@class="w-pagehead"]/h1/text()|//div[@class="w-pagehead"]/p/text()'
HIGH_XPATH = '//td[a="3200×1600 High"]/a/attribute::href'
ANDROID_XPATH = '//td[a="1080p"]/a/attribute::href'
FORMAT_XPATHS = (HIGH_XPATH, ANDROID_XPATH)


log_format = '%(asctime)16s %(levelname)6s %(message)s'
logging.basicConfig(format=log_format,
                    filename='log/grabber.log',
                    level=logging.INFO)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(log_format))
logging.getLogger('').addHandler(console)
log = logging.getLogger(__name__)


def main():
    cookies = json.load(open(COOKIES_JSON_PATH))
    page = with_retry(requests.get, VIDEOS_URL, cookies=cookies, timeout=TIMEOUT)
    tree = html.fromstring(page.content)
    detail_pages = tree.xpath(DETAIL_PAGES_XPATH)

    files_urls = []
    for url in detail_pages:
        time.sleep(random.random() + 2)
        info = get_video_page_info(url, cookies)
        download_dir = os.path.join(DOWNLOAD_PATH, safe_path_name(info['title']))
        os.makedirs(download_dir, exist_ok=True)
        for video_url in info['video_urls']:
            fp = os.path.join(download_dir, url.split('/')[-1])
            with_retry(download_file, video_url, fp, cookies)
            files_urls.append(video_url)

    with open("log/urls-{}.json".format(datetime.datetime.now().isoformat()), 'w') as f:
        json.dump(files_urls, f)


def get_video_page_info(page_url, cookies):
    info = {
        'video_urls': [],
    }
    
    try:
        page = with_retry(requests.get, page_url, cookies=cookies, timeout=TIMEOUT)
        tree = html.fromstring(page.content)

        info['title'] = '{} ({})'.format(*tree.xpath(TITLE_XPATH))

        for xpath in FORMAT_XPATHS:
            info['video_urls'].append(tree.xpath(xpath)[0])

    except:
        log.exception('Unhandled error on page {}'.format(page_url))

    return info


def download_file(src_url, dst_path, cookies=None):
    log.info('Downloading file: {}'.format(src_url))
    
    if os.path.exists(dst_path):
        log.info('File exists, skipping')
        return
    else:
        try:
            r = requests.get(src_url, cookies=cookies, stream=True, timeout=TIMEOUT)
            with open(dst_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except:
            os.unlink(dst_path)
            raise


def safe_path_name(name):
    name = name.replace('&', 'and')
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    safe_name = ''.join(c for c in name if c in valid_chars)
    return safe_name


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
