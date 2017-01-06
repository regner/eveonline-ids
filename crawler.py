
import json
import logging
import asyncio

from aiohttp import ClientSession

logging.basicConfig(level=logging.INFO)

PER_REQUEST = 300

URL = 'https://esi.tech.ccp.is/latest/characters/names/'
PARAMETER = 'character_id'
RANGES = [
    # [   90_000_000,    97_999_999],
    # [  100_000_000,   249_999_999],
    [  250_000_000,   499_999_999],
    [  500_000_000,   749_999_999],
    [  750_000_000,   999_999_999],
    [1_000_000_000, 1_249_999_999],
    [1_250_000_000, 1_499_999_999],
    [1_500_000_000, 1_749_999_999],
    [1_750_000_000, 1_999_999_999],
    [2_000_000_000, 2_099_999_999],
    [2_100_000_000, 2_111_999_999],
]

# INFO = {
#     'characters': {
#         'url': 'https://esi.tech.ccp.is/latest/characters/names/',
#         'parameter': 'character_id',
#         'ranges': [
#             [   90_000_000,    97_999_999],
#             [  100_000_000,   249_999_999],
#             [  250_000_000,   499_999_999],
#             [  500_000_000,   749_999_999],
#             [  750_000_000,   999_999_999],
#             [1_000_000_000, 1_249_999_999],
#             [1_250_000_000, 1_499_999_999],
#             [1_500_000_000, 1_749_999_999],
#             [1_750_000_000, 1_999_999_999],
#             [2_000_000_000, 2_099_999_999],
#             [2_100_000_000, 2_111_999_999],
#             [2_112_000_000, 2_119_999_999],  # Actually goes a lot further but will do for now
#         ],
#     },
#     'corporations': {
#         'url': 'https://esi.tech.ccp.is/latest/corporations/names/',
#         'parameter': 'corporation_id',
#         'ranges': [
#             [   98_000_000,    98_999_999],
#             [  100_000_000, 2_099_999_999],
#         ],
#     },
#     'alliances': {
#         'url': 'https://esi.tech.ccp.is/latest/alliances/names/',
#         'parameter': 'alliance_id',
#         'ranges': [
#             [   99_000_000,    99_999_999],
#             [  100_000_000, 2_099_999_999],
#         ],
#     },
# }


def get_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_request_bundles():
    bundle_chunks = []

    for id_type in INFO.keys():
        base_url = INFO[id_type]['url']

        for r in INFO[id_type]['ranges']:
            start = r[0]
            stop = r[1]

            chunks = get_chunks(range(start, stop), PER_REQUEST)
            
            for chunk in chunks:
                bundles.append((base_url, INFO[id_type]['parameter'], chunk))

            bundle_chunks.append

    return bundles


async def fetch(session, chunk):
    params = {
        'datasource': 'tranquility',
        f'{PARAMETER}s': ','.join(str(x) for x in chunk),
    }

    start = chunk[0]
    stop = chunk[-1]

    logging.info(f'Making request for {PARAMETER}s with chunk {start}-{stop}.')

    while True:
        try:
            async with session.get(URL, params=params) as response:
                if response.status == 200:
                    return await response.read()

        except:
            pass

        await asyncio.sleep(1)



async def handle_response(response, chunk):
    data = json.loads(response.decode('utf-8'))

    if len(data) > 0:
        start = chunk[0]
        stop = chunk[-1]

        logging.info(f'Got {len(data)} IDs in range {start}-{stop}.')

        
        range_start = start - (start % 1_000_000)

        out_file = f'test/{PARAMETER}s_{range_start:_}.txt'
        combined_data = '\n'.join(str(x[PARAMETER]) for x in data)

        with open(out_file, 'a') as f:
            f.write('\n')
            f.write(combined_data)



async def bound_fetch(sem, session, chunk):
    async with sem:
        response = await fetch(session, chunk)
        await handle_response(response, chunk)


async def run():
    tasks = []
    sem = asyncio.Semaphore(10000)

    logging.info('Creating async tasks...')
    headers = {
        'User-Agent': '<3 Regner <3',
    }

    async with ClientSession(headers=headers) as session:
        for r in RANGES:
            start = r[0]
            stop = r[1]

            chunks = get_chunks(range(start, stop), PER_REQUEST)
            
            for chunk in chunks:
                task = asyncio.ensure_future(bound_fetch(sem, session, chunk))
                tasks.append(task)

            responses = asyncio.gather(*tasks)
            await responses


loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run())
loop.run_until_complete(future)

