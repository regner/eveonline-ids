
import json
import logging
import asyncio

from aiohttp import ClientSession

logging.basicConfig(level=logging.INFO)

PER_REQUEST = 300
INFO = {
    'characters': {
        'url': 'https://esi.tech.ccp.is/latest/characters/names/',
        'parameter': 'character_id',
        'ranges': [
            # [   90_000_000,    97_999_999],
            [  100_000_000,   249_999_999],
            # [  250_000_000,   499_999_999],
            # [  500_000_000,   749_999_999],
            # [  750_000_000,   999_999_999],
            # [1_000_000_000, 1_249_999_999],
            # [1_250_000_000, 1_499_999_999],
            # [1_500_000_000, 1_749_999_999],
            # [1_750_000_000, 1_999_999_999],
            # [2_000_000_000, 2_111_999_999],
            # [2_100_000_000, 2_111_999_999],
            # [2_112_000_000, 2_119_999_999],  # Actually goes a lot further but will do for now
        ],
    },
    # 'corporations': {
    #     'url': 'https://esi.tech.ccp.is/latest/corporations/names/',
    #     'parameter': 'corporation_id',
    #     'ranges': [
    #         [   98_000_000,    98_999_999],
    #         [  100_000_000, 2_099_999_999],
    #     ],
    # },
    # 'alliances': {
    #     'url': 'https://esi.tech.ccp.is/latest/alliances/names/',
    #     'parameter': 'alliance_id',
    #     'ranges': [
    #         [   99_000_000,    99_999_999],
    #         [  100_000_000, 2_099_999_999],
    #     ],
    # },
}


def get_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def step_size(start, stop):
    return int((stop - start) / PER_REQUEST)


def get_request_bundles():
    bundles = []

    for id_type in INFO.keys():
        base_url = INFO[id_type]['url']

        for r in INFO[id_type]['ranges']:
            start = r[0]
            stop = r[1]

            chunks = get_chunks(range(start, stop), PER_REQUEST)
            
            for chunk in chunks:
                bundles.append((base_url, INFO[id_type]['parameter'], chunk))

    return bundles


async def fetch(session, url, parameter, chunk):
    params = {
        'datasource': 'tranquility',
        f'{parameter}s': ','.join(str(x) for x in chunk),
    }

    start = chunk[0]
    stop = chunk[-1]

    logging.info(f'Making request for {parameter}s with chunk {start}-{stop}.')

    while True:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.read()

        except:
            pass

        await asyncio.sleep(1)



async def handle_response(response, parameter, chunk):
    data = json.loads(response.decode('utf-8'))

    if len(data) > 0:
        start = chunk[0]
        stop = chunk[-1]

        logging.info(f'Got {len(data)} IDs in range {start}-{stop}.')

        
        range_start = start - (start % 1_000_000)

        out_file = f'test/{parameter}s_{range_start:_}.txt'
        combined_data = '\n'.join(str(x[parameter]) for x in data)

        with open(out_file, 'a') as f:
            f.write('\n')
            f.write(combined_data)



async def bound_fetch(sem, session, url, parameter, chunk):
    async with sem:
        response = await fetch(session, url, parameter, chunk)
        await handle_response(response, parameter, chunk)


async def run():
    tasks = []
    sem = asyncio.Semaphore(10000)

    logging.info('Building bundles...')
    request_bundles = get_request_bundles()

    logging.info('Creating async tasks...')
    headers = {
        'User-Agent': '<3 Regner <3',
    }

    async with ClientSession(headers=headers) as session:
        for rb in request_bundles:
            task = asyncio.ensure_future(bound_fetch(sem, session, rb[0], rb[1], rb[2]))
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        await responses


loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run())
loop.run_until_complete(future)

