import argparse
from lib.googleplay_scraper import GooglePlayScraper

if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser(description='Scrape and store Google Play Store rankings',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('cmd',
                        type=str,
                        choices=['create_credentials',
                                 'verify_credentials',
                                 'scrape',
                                 'details'
                                 ],
                        help='''
create_credential - Create new GSF_ID and AUTH_SUB_TOKEN
verify_credentials - Verify provided GSF_ID and AUTH_SUB_TOKEN
scrape - Scrape the entire Google Play Store
details - Scrape details'''
                        )

    args = parser.parse_args()
    gps = GooglePlayScraper()

    if args.cmd == 'create_credentials':
        gps.create_credentials()
    elif args.cmd == 'verify_credentials':
        gps.verify_credentials()
    elif args.cmd == 'scrape':
        gps.scrape()                    # Scrape rankings
        gps.scrape_additional_details() # Scrape details of specific app
        gps.backup_todays_data()
    elif args.cmd == 'details':
        gps.scrape_missing_details()    # Scrape details of apps
