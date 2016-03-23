#!/usr/bin/env python3

import logging
import os
import json
import requests
import time
import random
import datetime
from lxml import html


DOWNLOAD_PATH = 'videos'
VIDEOS_URL = 'https://virtualrealporn.com/videos/'
COOKIES_JSON_PATH = 'cookies/vrp-cookies.json'

TIMEOUT = 15
MAX_RETRY = 3

DETAIL_PAGES_XPATH = '//a[@class="w-portfolio-item-anchor"]/attribute::href'
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
        for video_url in info['video_urls']:
            with_retry(download_file, video_url, cookies)
            files_urls.append(video_url)

    with open("log/urls-{}.json".format(datetime.datetime.now().isoformat()), 'w') as f:
        json.dump(files_urls, f)


def get_video_page_info(page_url, cookies):
    info = {
        'video_urls': []
    }
    
    try:
        page = with_retry(requests.get, page_url, cookies=cookies, timeout=TIMEOUT)
        tree = html.fromstring(page.content)
        for xpath in FORMAT_XPATHS:
            info['video_urls'].append(tree.xpath(xpath)[0])
    except:
        log.exception('Unhandled error on page {}'.format(page_url))

    return info

        
def download_file(url, cookies=None):
    log.info('Downloading file: {}'.format(url))
    fp = os.path.join(DOWNLOAD_PATH, url.split('/')[-1])
    
    if os.path.exists(fp):
        log.info('File exists, skipping')
        return
    else:
        try:
            r = requests.get(url, cookies=cookies, stream=True, timeout=TIMEOUT)
            with open(fp, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except:
            os.unlink(fp)
            raise


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
