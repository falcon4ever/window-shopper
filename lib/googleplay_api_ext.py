import time
from time import strftime
import os
import json

from lib.simple_logger import SimpleLogger
from config import config

from gpapi import utils
from gpapi.googleplay import GooglePlayAPI, FDFE, LoginError, SecurityCheckError, RequestError


# An extension to the 'original' scraper using the newer undocumented Google Play Store APIs
# https://github.com/NoMore201/googleplay-api
class GooglePlayAPIext(GooglePlayAPI):

    def __init__(self, locale, timezone, device_codename):
        super().__init__(locale, timezone, device_codename)
        self.log = SimpleLogger(__name__)
        self.log_api_calls = config.log_api_calls
        self.scrape_delay = config.scrape_delay
        self.locale = config.LOCALE

    def get_rankings(self, scat, stcid, sets=1000, fetch_new_apps=False):
        self.log.info(f'Fetching ({self.locale}): {stcid} - {scat} - Top New?: {fetch_new_apps}')
        apps, next_url = self.get_list_top_chart_items(scat, stcid, fetch_new_apps)
        n = 1

        while n < sets:
            # We're done!
            if next_url == '':
                break
            time.sleep(self.scrape_delay)

            # self.log.info(f'Fetching page {str(n)}')
            new_apps, new_next_url = self.get_cluster(next_url, scat, stcid, fetch_new_apps, n)
            apps.extend(new_apps)
            next_url = new_next_url
            n += 1

        self.log.info(f'Fetched pages {n}')
        return apps, n

    def get_list_top_chart_items(self, scat, stcid, fetch_new_apps=False):
        path = f'{FDFE}listTopChartItems?c=3'  # unknown required parameter
        path += f'&n=3'  # unknown required parameter
        path += f'&stcid={stcid}'
        path += f'&scat={scat}'
        if fetch_new_apps:
            path += '&stcreltype=1'

        data = self.executeRequestApi2(path)
        if self.log_api_calls:
            self.save_raw_response(path, scat, stcid, fetch_new_apps, 0, data)
        return self.unpack_data(data)

    def get_cluster(self, path, scat, stcid, fetch_new_apps, page):
        data = self.executeRequestApi2(FDFE + path)
        if self.log_api_calls:
            self.save_raw_response(FDFE + path, scat, stcid, fetch_new_apps, page, data)
        return self.unpack_data(data)

    def unpack_data(self, data):
        apps = []
        next_url = ''
        ordered = True
        for d in data.payload.listResponse.doc:
            for c in d.child:
                for app in c.child:
                    apps.append(utils.parseProtobufObj(app))
                next_url = c.containerMetadata.nextPageUrl
                ordered = c.containerMetadata.ordered

        if ordered is False:
            self.log.error('Warning data not ordered')

        return apps, next_url

    def save_raw_response(self, path, scat, stcid, fetch_new_apps, page, data):

        if not os.path.exists(config.SCRAPE_LOG_PATH):
            os.makedirs(config.SCRAPE_LOG_PATH)

        date = strftime("%Y-%m-%d")
        filename = f'{config.SCRAPE_LOG_PATH}/{date}_{self.locale}_{stcid}_{scat}_{fetch_new_apps}_{page}.json'
        with open(filename, 'w') as outfile:
            outfile.write(f'Scrape timestamp: {time.ctime()}\n')
            outfile.write(f'URL: {path}\n')
            outfile.write(f'Response:\n')
            json.dump(utils.parseProtobufObj(data), outfile, indent=4)
