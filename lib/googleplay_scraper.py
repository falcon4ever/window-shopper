import json
import os
import time
from time import strftime

from lib.googleplay_api_ext import GooglePlayAPIext, LoginError, SecurityCheckError, RequestError
from config import (config, account, auth)
from lib.simple_logger import SimpleLogger

if config.store_in_sqlite:
    from lib.googleplay_db_sqlite import GooglePlayDbSqlite

from lib.googleplay_const import TOP_CHARTS, APP_CATEGORIES, GAME_CATEGORIES

class GooglePlayScraper:

    def __init__(self):
        self.log = SimpleLogger(__name__)

        if config.store_in_sqlite:
            self.db = GooglePlayDbSqlite()

    def login(self):
        try:
            api = GooglePlayAPIext(locale=config.LOCALE, timezone=config.TIMEZONE,
                                   device_codename=config.DEVICE_CODENAME)
            api.login(None, None, int(auth.gsfid, 16), auth.authSubToken)
        except (LoginError, SecurityCheckError, RequestError) as e:
            # Either the device has been signed out, the token is expired or the device is temporary banned.
            if "DF-DFERH-01" in str(e):
                self.log.error('DF-DFERH-01 - Please update your GPS_SCRAPER_GSF_ID and GPS_SCRAPER_AUTH_SUB_TOKEN')
            raise

        return api

    # Create credentials, provide login/pass and get a gsf_id/auth_sub_token in return
    def create_credentials(self):
        try:
            api = GooglePlayAPIext(locale=config.LOCALE, timezone=config.TIMEZONE,
                                   device_codename=config.DEVICE_CODENAME)
            api.login(email=account.gmail_address, password=account.gmail_password)
            authSubToken = api.authSubToken
            gsfid = hex(api.gsfId).replace('0x', '')
        except (LoginError, SecurityCheckError) as e:
            if "BadAuthentication" in str(e):
                self.log.error('Wrong email address or password provided')
            raise

        f = open("config/auth.py", "w")
        f.write("# Automatically generated\n")
        f.write("gsfid=\'" + gsfid + "\'\n")
        f.write("authSubToken=\'" + authSubToken + "\'\n")
        f.close()

        self.log.info(f'Created fresh credentials for {account.gmail_address}:')
        self.log.info(f'GPS_SCRAPER_GSF_ID: {gsfid}')
        self.log.info(f'GPS_SCRAPER_AUTH_SUB_TOKEN: {authSubToken}')

    # Verify if credentials are still valid
    def verify_credentials(self):
        gapi = self.login()

        # Test query for app details
        app_list = ["com.wanderu.wanderu", "com.aa.android", "com.goeuro.rosie", "com.busbud.android"]
        details = gapi.bulkDetails(app_list)

        for app in details:
            if app is None:
                raise Exception('Data missing while fetching data from Google Play Store API')

        self.log.info('Verified credentials')

    # Scrape rankings for provided categories and top charts
    def scrape_rankings(self, gapi, categories, top_charts, fetch_new_apps=False):
        total_num_api_calls = 0

        for stcid in top_charts:
            for scat in categories:
                apps_list, num_api_calls = gapi.get_rankings(scat=scat, stcid=stcid, fetch_new_apps=fetch_new_apps)
                if len(apps_list) == 0 and fetch_new_apps == False:
                    self.log.warning(f'Warning: No apps for [{stcid}] [{scat}] - New App [{fetch_new_apps}]')
                else:
                    app_rankings_data, app_details_data = self.process_rankings(scat, stcid, apps_list,
                                                                                fetch_new_apps=fetch_new_apps)
                    self.store_rankings(app_rankings_data, app_details_data)
                    total_num_api_calls += num_api_calls

        return total_num_api_calls

    # Split data for ranking and details tables
    def process_rankings(self, scat, stcid, apps_list, fetch_new_apps):
        scrape_date = time.strftime("%Y-%m-%d")
        app_rankings_data = []
        app_details_data = []
        app_id_list = {}  # Keep track of unique entries while populating rank and prevent duplicates
        rank = 1  # We keep track of the rank, don't increment if the app was already in the list

        postfix = ''
        if fetch_new_apps:
            postfix = '_new'

        for app in apps_list:
            app_id = app['docid']

            if app_id in app_id_list:
                self.log.warning(f'Found a duplicate, {app_id} is already in the apps list')
            else:
                app_rankings_data.append({
                    'collector_date': scrape_date,
                    'locale': config.LOCALE,
                    'top_chart': stcid + postfix,
                    'category': scat,
                    'app_id': app_id,
                    'app_rank': rank
                })

                app_details_data.append({
                    'collector_date': scrape_date,
                    'locale': config.LOCALE,
                    'app_id': app_id,
                    'app_creator': app['creator'],
                    'app_title': app['title'],
                    'app_summary_json': json.dumps(app),
                    'app_details_json': ''
                })

                app_id_list[app_id] = True
                rank += 1

        return app_rankings_data, app_details_data

    # Store scraped data in files
    def store_rankings(self, app_rankings_data, app_details_data):

        if len(app_rankings_data) > 0:
            if config.store_in_file:
                collector_date = app_rankings_data[0]['collector_date']
                locale = app_rankings_data[0]['locale']
                top_chart = app_rankings_data[0]['top_chart']
                category = app_rankings_data[0]['category']
                storage_path = f'{config.SCRAPE_TEMP_PATH}'

                if not os.path.exists(storage_path):
                    os.makedirs(storage_path)

                with open(f'{storage_path}/{collector_date}_{locale}_{top_chart}_{category}_app_rankings_data.json',
                          'w') as outfile:
                    json.dump(app_rankings_data, outfile, indent=4)

                with open(f'{storage_path}/{collector_date}_{locale}_{top_chart}_{category}_app_summary_data.json',
                          'w') as outfile:
                    json.dump(app_details_data, outfile, indent=4)

            if config.store_in_sqlite:
                self.db.insert_app_rankings(app_rankings_data)
                self.db.insert_app_details(app_details_data)

    # Scrape app details (for a predefined set of app ids). We can't scrape every app out there so pick the important ones.
    def scrape_app_details(self, gapi, app_ids):
        scrape_date = time.strftime("%Y-%m-%d")
        total_num_api_calls = 0

        # Scrape additional apps for details
        for app_id in app_ids:
            self.log.info(f'Fetching app details for {app_id}')

            try:
                details_data = gapi.details(app_id)
            except RequestError as e:
                self.log.error(f'Could not fetching app details for {app_id} - {e}')
                continue

            total_num_api_calls += 1
            app_details_json = json.dumps(details_data)

            if app_details_json == '{}':
                raise Exception(f'Server has empty response for: {app_id}')

            if config.log_api_calls:
                if not os.path.exists(config.SCRAPE_LOG_PATH):
                    os.makedirs(config.SCRAPE_LOG_PATH)

                date = strftime("%Y-%m-%d")
                filename = f'{config.SCRAPE_LOG_PATH}/{date}_{config.LOCALE}_app_details_{app_id}.json'
                with open(filename, 'w') as outfile:
                    json.dump(details_data, outfile, indent=4)

            app_details_data = {
                'collector_date': scrape_date,
                'locale': config.LOCALE,
                'app_id': app_id,
                'app_creator': details_data['creator'],
                'app_title': details_data['title'],
                'app_details_json': app_details_json,
            }

            self.store_app_details(app_details_data)
            time.sleep(config.scrape_delay)  # don't scrape too fast, this endpoint seems to be throttled

        return total_num_api_calls

    def store_app_details(self, app_details_data):
        if config.store_in_file:
            collector_date = app_details_data['collector_date']
            app_id = app_details_data['app_id']
            locale = app_details_data['locale']
            storage_path = f'{config.SCRAPE_TEMP_PATH}'

            if not os.path.exists(storage_path):
                os.makedirs(storage_path)

            with open(f'{storage_path}/{collector_date}_{locale}_{app_id}_app_details_data.json',
                      'w') as outfile:
                json.dump(app_details_data, outfile, indent=4)

        if config.store_in_sqlite:
            self.db.update_app_details(app_details_data)

    # Scrape rankings
    def scrape(self):
        gapi = self.login()

        # If you're only interested in the rankings of one particular category and topchart, you could do this:
        # categories = [
        #     "APPLICATION"
        # ]
        # top_charts = [
        #     "apps_topselling_free"
        # ]

        categories = []
        categories.extend(APP_CATEGORIES)
        categories.extend(GAME_CATEGORIES)
        top_charts = []
        top_charts.extend(TOP_CHARTS)

        num_ranking_api_calls = self.scrape_rankings(gapi, categories, top_charts)
        num_ranking_api_calls_new = self.scrape_rankings(gapi, categories, top_charts, True)

        self.log.info(f'Summary for {time.strftime("%Y-%m-%d")}')
        self.log.info(
            f'Num of API calls used for scraping rankings: {num_ranking_api_calls + num_ranking_api_calls_new}')

    def scrape_additional_details(self):
        gapi = self.login()

        num_details_api_calls = self.scrape_app_details(gapi, config.ADDITIONAL_APP_IDS)

        self.log.info(f'Summary for {time.strftime("%Y-%m-%d")}')
        self.log.info(f'Num of API calls used for scraping details: {num_details_api_calls}')
        self.log.info(f'Num of items in ADDITIONAL_APP_IDS: {len(config.ADDITIONAL_APP_IDS)}')

    def scrape_missing_details(self):
        gapi = self.login()

        app_ids = self.db.select_app_no_details()
        self.log.info(f'Num of items in app_ids: {len(app_ids)}')

        num_details_api_calls = self.scrape_app_details(gapi, app_ids)

        self.log.info(f'Summary for {time.strftime("%Y-%m-%d")}')
        self.log.info(f'Num of API calls used for scraping details: {num_details_api_calls}')

    def backup_todays_data(self):
        if not os.path.exists(config.SCRAPE_BACKUP_PATH):
            os.makedirs(config.SCRAPE_BACKUP_PATH)

        # Get all files of things we scraped today
        rankings_file_list = []
        details_file_list = []
        summary_file_list = []
        for path, subdirs, files in os.walk(config.SCRAPE_TEMP_PATH):
            for name in files:
                if "app_rankings_data.json" in name:
                    rankings_file_list.append(os.path.join(path, name))
                if "app_details_data.json" in name:
                    details_file_list.append(os.path.join(path, name))
                if "app_summary_data.json" in name:
                    summary_file_list.append(os.path.join(path, name))
        rankings_file_list.sort()
        details_file_list.sort()
        summary_file_list.sort()

        # read in the data and write a new consolidated backup file
        app_rankings_data = []
        for path in rankings_file_list:
            with open(path) as json_file:
                app_rankings_data.extend(json.load(json_file))

        collector_date = app_rankings_data[0]['collector_date']
        locale = app_rankings_data[0]['locale']

        with open(f'{config.SCRAPE_BACKUP_PATH}/{collector_date}_{locale}_app_rankings_data.json', 'w') as outfile:
            json.dump(app_rankings_data, outfile, indent=4)
        del app_rankings_data

        app_details_data = []
        for path in details_file_list:
            with open(path) as json_file:
                app_details_data.append(json.load(json_file))

        with open(f'{config.SCRAPE_BACKUP_PATH}/{collector_date}_{locale}_app_details_data.json', 'w') as outfile:
            json.dump(app_details_data, outfile, indent=4)
        del app_details_data

        summary_file_data = []
        for path in summary_file_list:
            with open(path) as json_file:
                summary_file_data.extend(json.load(json_file))

        with open(f'{config.SCRAPE_BACKUP_PATH}/{collector_date}_{locale}_app_summary_data.json', 'w') as outfile:
            json.dump(summary_file_data, outfile, indent=4)
        del summary_file_data
