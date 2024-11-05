import gzip
import requests
import json
import glob
from os.path import join as pjoin
from tenacity import retry, stop_after_attempt, wait_random_exponential

url_prompt = 'https://oeis.org/search?q=id:{aid}&fmt=json'
data_path = './data/stripped.gz' # download from https://oeis.org/stripped.gz
# save_path = './data/oeis_data.jsonl'
save_dir = './data/oeis_data_all/'
split_num = 10


def get_aids(data_path):
    aids = []
    with gzip.open(data_path, 'rb') as f:
        for line in f:
            line = line.decode('utf-8')
            if line.startswith('A'):
                # print(line)
                aids.append(line.split(' ')[0])
    print(len(aids))
    return aids


def get_seq(aid):
    res = requests.post(url_prompt.format(aid=aid))
    if res.status_code == 200:
        return res.json()
    else:
        return None


def AID(seq_num):
    return 'A' + str(seq_num).zfill(6)


# @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
def download_and_save_aid_data(aid, save_dir):
    json_data = get_seq(aid)
    # assert json_data['count'] == 1
    # assert len(json_data['results']) == 1
    assert len(json_data) == 1
    aseq_data = json_data[0]
    jsonline = json.dumps(aseq_data)
    aid_p = AID(aseq_data['number'])
    assert aid_p == aid
    idx = int(aseq_data['number']) % split_num
    save_path = pjoin(save_dir, f'oeis_data_{idx:05d}_{split_num:05d}.jsonl')
    with open(save_path, 'a') as f:
        f.write(jsonline + '\n')
    print(f"Saving in {save_path}")
    return aseq_data


if __name__ == '__main__':
    # import asyncio
    # from IPython import get_ipython
    # get_ipython().run_line_magic('autoawait', 'on')
    # tasks = [asyncio.create_task(download_aid_data(x)) for x in todo_aids[:50]]
    # for t in tqdm.tqdm(tasks):
    #     await t

    aids = get_aids(data_path)
    exists_ids = set()
    for path in glob.glob(pjoin(save_dir, '*')):
        with open(path) as f:
            for line in f:
                d = json.loads(line)
                exists_ids.add(AID(d['number']))

    todo_aids = [x for x in aids if x not in exists_ids]
    print(f'len of todo_aids:', len(todo_aids))
    print(todo_aids[:10])
    # download_and_save_aid_data(todo_aids[0], save_dir)

    from multiprocessing import Pool
    pool = Pool(64)
    for aid in todo_aids:
        pool.apply_async(download_and_save_aid_data, (aid, save_dir))
    pool.close()
    pool.join()