from time import strftime

# Android Virtual Device Properties
LOCALE = 'en_US'                # Which locale to scrape. Server should also be located in that region.
TIMEZONE = 'America/New_York'   # Your timezone
DEVICE_CODENAME = 'crosshatch'  # Pretend to be a Google Pixel 3 XL (api30)

# Scraper
store_in_file = True
store_in_sqlite = True
scrape_delay = .150
scrape_date = strftime("%Y-%m-%d")

# Data paths
SCRAPE_BACKUP_PATH = f'data/backup'
SCRAPE_TEMP_PATH = f'data/scrape_tmp/{scrape_date}'
SQLITE_PATH = f'data/sqlite'

# Debug
log_api_calls = False
SCRAPE_LOG_PATH = f'data/scrape_log/{scrape_date}'

# Add non ranked apps
ADDITIONAL_APP_IDS = [
    'com.facebook.katana' # Facebook
    'com.waze',  # Waze
    'com.ubercab',  # Uber
    'me.lyft.android'  # Lyft
]
