# window-shopper
A scraper for mobile app stores

## Google Play Store Scraper

Scrape the entire play store and store the result in a SQLite database for easy data analysis. Unlike other scrapers that can only fetch the first 100 or 200 results, this implementation can scrape the full top charts (just like on a real device).

The script also allows you to automatically make a backup (in JSON format) for easy archiving and future dataprocessing.

This script assumes you are running Python 3.9.2 and SQLite with the JSON1 extension enabled.

### Gmail account

First, we need a gmail account that will be used with this scraper. It's probably a good idea to create a new one.

* Create a new Gmail account
* Updated `config/account.py` with your credentials


### Setup the project and the python environment
* Clone this repository `git clone git@github.com:falcon4ever/window-shopper.git`
* `cd window-shopper`
* `virtualenv --python=python3 .venv`
* `source .venv/bin/activate`
* `pip install -r requirements.txt`
* `export PYTHONPATH=$PYTHONPATH:/xxx/window-shopper`

### Fetching our credentials
To use the API we need to obtain a GSF ID and a Sub Auth token. To create your credentials, run:

* `python bin/scrape_playstore.py create_credentials`

You should only do this once. Each time you run this, new credentials are created and a new virtual Android device is added to your Google account. You can manage the (virtual) devices you created here: [My Account](https://myaccount.google.com/device-activity)

### Verifiying our credentials
To check if your new credentials work or at a later time to see if they are still valid, you can run:

* `python bin/scrape_playstore.py create_credentials`

### Scraping
To start scraping, run:

* `python bin/scrape_playstore.py scrape`

By default the entire play store and store the ranking and summary data in a SQL database. If you want additional information on certain apps, you can modify the `ADDITIONAL_APP_IDS` in the config file and add the app_ids. Please note that scraping details of the apps increase the time to scrape and increases the risk of getting throttled. You should review if the SQLite database (app_summary_json column contains sufficient information for your needs)

### (Advanced) Scraping details

If you want to scrape additional details of apps stored in the database, you can run:

* `python bin/scrape_playstore.py details`

You should review the SQL query that feeds this function before running.

Warning: you probably only want to fetch a subset and not the details of every app as you will most likely get throttled.


### Automation with crontab:
If you're interested in collecting daily app rankings, you should create a crontab entry like this and run it once a day (modify the paths as needed):

* `cd /XXX/window-shopper ; source .venv/bin/activate; export PYTHONPATH=$PYTHONPATH:/XXX/window-shopper ; python bin/scrape_playstore.py scrape ; deactivate`

It will probably take 1h or more to scrape all categories.

### Advanced config
* `store_in_file = True/False` Store results in a json file in `SCRAPE_TEMP_PATH` with a daily consolidated backup in `SCRAPE_BACKUP_PATH`
* `store_in_sqlite = True/False` Store results in sqlite db located in `SQLITE_PATH`
* `scrape_delay = .150` Scrape delay (pause between api calls)
* `log_api_calls = True/False` Log raw api calls to `SCRAPE_LOG_PATH`

### Additional tips

#### Installing Python and Virtualenv

Some helpful tips on how to set things up on a linux box:

* [Installing a custom version of Python 3](https://help.dreamhost.com/hc/en-us/articles/115000702772-Installing-a-custom-version-of-Python-3)
* [Installing and using virtualenv with Python 3](https://help.dreamhost.com/hc/en-us/articles/115000695551-Installing-and-using-virtualenv-with-Python-3)

#### Installing a pre-compiled protobuf compiler in `/opt`:
* `wget https://github.com/protocolbuffers/protobuf/releases/download/v3.15.6/protoc-3.15.6-linux-x86_64.zip && \
    unzip protoc-3.15.6-linux-x86_64.zip -d /opt`
* `export PATH=$PATH:/opt/bin`

#### Installing a protobuf compiler (from scratch):
* `sudo apt-get install autoconf automake libtool curl make g++ unzip`
* Download a release: [Google protocolbuffers](https://github.com/protocolbuffers/protobuf/releases)
* Unpack the file
* `./configure --prefix=$HOME/opt`
* `make`
* `make check`
* `make install`
* update your `$PATH`

## App Store Scraper

coming soon.