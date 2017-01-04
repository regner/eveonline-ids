
import os
import logging
import argparse
import requests
import subprocess

from time import sleep

logging.basicConfig(level=logging.INFO)


def main(lookup: str, starting: int, ending: int):
    # URL Setup
    if lookup == 'corporations':
        url = 'https://esi.tech.ccp.is/latest/corporations/names/'
        parameter_name = 'corporation'

    else:
        url = 'https://esi.tech.ccp.is/latest/characters/names/'
        parameter_name = 'character'

    logging.info(f'Using URL {url}')

    # File Setup
    out_file = f'{lookup}/{lookup}_ids_{starting}_{ending}.txt'

    # Adjust ID Range Start
    if os.path.isfile(out_file):
        starting = int(subprocess.check_output(['tail', '-1', out_file]))

    # Some Extra Defaults
    per_request = 300
    sleep_time = 10

    default_parameters = {
        'datasource': 'tranquility'
    }

    headers = {
        'User-Agent': '<3 Regner <3'
    }

    # GO TIME!
    while True:
        if starting > ending:
            logging.info('Seems we are trying to start but already have everything...')
            break

        logging.info(f'Going with start of {starting:,}.')
        character_ids = [str(x) for x in range(starting, starting + per_request)]

        params = default_parameters.copy()
        params[f'{parameter_name}_ids'] = ','.join(character_ids)

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != requests.codes.ok:
            logging.info(f'Had bad status code, sleeping for {sleep_time} and trying again.')
            logging.info(f'Status code was: {response.status_code}')
            logging.info(f'Message was: {response.text}')
            sleep(sleep_time)
            continue

        data = response.json()
        logging.info(f'Got good response with {len(data)} {lookup}.')
        combined_data = '\n'.join(str(x[f'{parameter_name}_id']) for x in data)

        if len(data) > 0:
            with open(out_file, 'a') as f:
                f.write('\n')
                f.write(combined_data)

        starting += per_request

        if starting > ending:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl some character IDs.')
    parser.add_argument('--starting', type=int, help='Starting ID.', default=90_000_000)
    parser.add_argument('--ending', type=int, help='Ending ID.', default=97_999_999)
    parser.add_argument(
        '--lookup',
        type=str,
        help='Valid values: "characters", "corporations", "alliances". Defaults to "characters"',
        default='characters'
    )

    args = parser.parse_args()

    main(args.lookup, args.starting, args.ending)
