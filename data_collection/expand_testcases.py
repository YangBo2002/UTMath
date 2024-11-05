import pandas as pd
import json
import subprocess
import multiprocessing
import time
import tqdm
import re
import os

from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_random_exponential, RetryError
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

from models.theb import ThebModel
from models.openai_gpt import OpenAIModel

# llm = ThebModel(model_name='gpt-3.5-turbo')
# llm = ThebModel(model_name='gpt-4o')
# llm = ThebModel(model_name='gpt-4o-mini')
# llm = OpenAIModel(model_name='gpt-4o-mini-2024-07-18')
llm = OpenAIModel(model_name='gpt-4o-2024-08-06')


N_TOTAL_PROMPT = """```
{code}
```
Here is a piece of Mathematica code that generates a sequence of numbers, where the number of generated elements is predefined. Now I want to control the length of the sequence using a variable called `N_TOTAL`. How should I modify it? Your code should have two lines: the first line should be `N_TOTAL={{original number}};` and the second line should be the original code, modified to use `N_TOTAL`.
"""
# 这是一段mathematica代码，为了生成一个数列，其中设定了生成数字的个数。我现在希望能用一个变量N_TOTAL控制生成数列的长度，请问应该如何修改？你的代码需要有两行，第一行为N_TOTAL={原来的数字};，第二行源代码修改了N_TOTAL之后的代码。


def adjust_mathematica(m_list):
    m_str = ' '.join(m_list)
    p = r'\(\*.*?\*\)'
    lines = re.split(p, m_str)
    lines = [x for x in lines if x.strip()]
    return lines


def run_command(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """
    Run a command in the shell.
    Args:
        - cmd: command to run
    """
    try:
        cp = subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}, {e}")
        raise e
    return cp

def run_wolframscript(code, timeout, retry_times=3):
    exp = None
    for _ in range(retry_times):
        try:
            cp = run_command(
                ['wolframscript', '-code', code],
                capture_output=True,
                text=True,
                timeout=timeout  # 设置超时时间
            )
        except subprocess.TimeoutExpired as e:
            raise e
        except Exception as e:
            exp = e
            continue
        return cp
    raise exp


def save_wolframscript_result(data_row, timeout, save_path):
    code = data_row['mathematica']
    aid = data_row['number']
    start_time = time.time()
    stderr = ""
    try:
        result = run_wolframscript(code, timeout)
        output = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        output =  f"Mathematica code '{code}' timed out after {timeout} seconds"
    except Exception as e:
        output = f"Raise Exception: {e}"
    
    end_time = time.time()
    run_time = end_time - start_time
    save_d = {
        'number': aid,
        'code': code,
        'run_time': run_time,
        'output': output,
        'stderr': stderr
    }
    with open(save_path, 'a') as f:
        f.write(json.dumps(save_d) + '\n')


def extract_mathematica(response):
    pattern = r'```.*?\n([\s\S]*?)\n?```'
    code_blocks = re.findall(pattern, response)
    if code_blocks:
        return code_blocks[-1]
    else:
        return None


def convert_to_sequence(output: str):
    def dfs_convert(l):
        res = []
        for x in l:
            if isinstance(x, list):
                res.extend(dfs_convert(x))
            else:
                res.append(x)
        return res

    output = output.replace('{', '[').replace('}', ']')
    return dfs_convert(eval(output))


@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
def modify_mathematica(data_row, save_path):
    code = data_row['mathematica_extracted']
    prompt = N_TOTAL_PROMPT.format(code=code)
    response = llm.call([llm.user_msg(prompt)])
    output = ''
    run_time = -1
    try:
        new_code = extract_mathematica(response)
        ori_len, new_code = new_code.split('\n')

        # check new_code
        length = int(ori_len.split('=')[-1].strip(' ;'))
        # length = len(data_row['data'].split(','))
        start_time = time.time()
        result = run_command(
            ['wolframscript', '-code', new_code.replace('N_TOTAL', str(length))],
            capture_output=True,
            text=True,
            timeout=30  # 设置超时时间
        )
        end_time = time.time()
        run_time = end_time - start_time
        logger.info(f"run time: {run_time}")
        output = result.stdout
        output = convert_to_sequence(output)
    except Exception as e:
        logger.debug(f"Exception raised in {data_row['number']} with handling response: {response}")
        logger.exception(e)
        raise e

    data_row['mathematica_expand'] = new_code
    data_row['mathematica_original_length'] = length
    data_row['mathematica_expand_output'] = ','.join(map(str, output))
    data_row['mathematica_expand_runtime'] = run_time
    with open(save_path, 'a') as f:
        f.write(json.dumps(data_row) + '\n')
    logger.info(f"Saved.")
    return data_row


def safe_run_task(func, *args):
    try:
        func(*args)
    except RetryError as e:
        return 


def run_expand_mathematica(path, save_path):
    # path = 'data/first_version_data_pretest.jsonl'
    # save_path = 'data/pretest_v1_expand.jsonl'
    exist_codes = set()
    if os.path.exists(save_path):
        tmp = pd.read_json(save_path, lines=True)
        exist_codes = set(tmp['mathematica_extracted'])
    d = pd.read_json(path, lines=True)
    d['mathematica_extracted'] = d['mathematica'].apply(adjust_mathematica)
    wolfram_codes = json.loads(d.explode('mathematica_extracted').reset_index(drop=True).to_json(orient='records'))
    wolfram_codes = [x for x in wolfram_codes if x['mathematica_extracted'] not in exist_codes]
    # print(wolfram_codes[0])

    # 设置每个 wolframscript 的超时时间
    # 每个任务超时时间为 5 秒
    timeout_seconds = 5
    # modify_mathematica(llm, wolfram_codes[0], save_path)

    # 创建进程池
    # with ThreadPoolExecutor(max_workers=1) as executor:
    #     futures = [executor.submit(modify_mathematica, row, save_path) for row in wolfram_codes]
        
    #     # results = []
    #     for future in tqdm.tqdm(as_completed(futures)):
    #         future.result()

    with multiprocessing.Pool(processes=12) as pool:
        results = [pool.apply_async(safe_run_task, (modify_mathematica, row, save_path)) for row in wolfram_codes]
        for r in tqdm.tqdm(results):
            r.get()


def binary_search_find_max_length(data_row, timeout, save_path):
    code = data_row['mathematica_expand']
    lb, ub = 0, 1000000
    while lb + 1 < ub:
        mid = (lb + ub) // 2
        run_code = code.replace('N_TOTAL', str(mid))
        run_ok = True
        try:
            cp = run_wolframscript(run_code, timeout)
            # number is huge
            if len(cp.stdout.split(',')[-1]) >= 30:
                run_ok = False
        except subprocess.TimeoutExpired:
            run_ok = False
        logger.info(f'{data_row["number"]} {mid} ({lb}, {ub}): {run_ok}')
        if run_ok:
            lb = mid
        else:
            ub = mid
    
    valid_length = lb
    # output = convert_to_sequence(cp.stdout)
    key = f"length_valid_in_{timeout}s"
    data_row[key] = valid_length
    # data_row['max_length_output'] = output

    with open(save_path, 'a') as f:
        f.write(json.dumps(data_row) + '\n')

def run_bs_task(path, save_path):
    # path = 'data/first_version_data_pretest.jsonl'
    # path = 'data/pretest_v1/pretest_v1_expand.jsonl'
    # save_path = 'data/pretest_v1/pretest_v1_expand_max_length_limit10_30.jsonl'
    exist_codes = set()
    if os.path.exists(save_path):
        tmp = pd.read_json(save_path, lines=True)
        if len(tmp) > 0:
            exist_codes = set(tmp['mathematica_extracted'])
    d = pd.read_json(path, lines=True)
    wolfram_codes = json.loads(d.to_json(orient='records'))
    wolfram_codes = [x for x in wolfram_codes if x['mathematica_extracted'] not in exist_codes]
    logger.info(f'Processing {len(wolfram_codes)} tasks.')
    timeout = 10
    # binary_search_find_max_length(wolfram_codes[0], timeout, save_path)

    # 创建进程池
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(binary_search_find_max_length, row, timeout, save_path) for row in wolfram_codes]
        
        # results = []
        for future in tqdm.tqdm(as_completed(futures)):
            future.result()

    # with multiprocessing.Pool(processes=10) as pool:
    #     results = [pool.apply_async(binary_search_find_max_length, (row, timeout, save_path)) for row in wolfram_codes]
    #     for r in tqdm.tqdm(results):
    #         r.get()

def align_data(ori_d, new_d):
    if all([x == y for x, y in zip(ori_d, new_d)]):
        return new_d
    if all([x == y for x, y in zip(ori_d, new_d[1:])]):
        return new_d[1:]
    if all([x == y for x, y in zip(ori_d[1:], new_d)]):
        return [ori_d[0]] + new_d
    return None

    
def select_codes(path, save_path, data_path):
    # path = 'data/pretest_v1/pretest_v1_expand_max_length_limit10_30.jsonl'
    # save_path = 'data/pretest_v1/pretest_v1_expand_max_length_limit10_30_output.jsonl'
    # data_path = 'data/pretest_v1/pretest_v1_expand_max_length_limit10_30_all_output.jsonl'
    exist_codes = set()
    if os.path.exists(save_path):
        with open(save_path) as f:
            for line in f:
                d = json.loads(line)
                exist_codes.add(d['number'])
        # tmp = pd.read_json(save_path, lines=True)
        # if len(tmp) > 0:
        #     exist_codes = set(tmp['number'])
    d = pd.read_json(path, lines=True)
    data = json.loads(d.to_json(orient='records'))
    res = {}
    for data_row in data:
        if data_row['number'] in exist_codes:
            continue
        key = data_row['number']
        if key not in res:
            res[key] = data_row
        else:
            if data_row['length_valid_in_10s'] > res[key]['length_valid_in_10s']:
                res[key] = data_row
    
    for data_row in tqdm.tqdm(res.values()):
        logger.info('Processing ' + str(data_row['number']))
        valid_length = data_row['length_valid_in_10s']
        code = data_row['mathematica_expand'].replace('N_TOTAL', str(valid_length))
        logger.info('Mathematica Code: ' + code)
        st_time = time.time()
        cp = run_wolframscript(code, timeout=20)
        run_time = time.time() - st_time

        try:
            output = convert_to_sequence(cp.stdout)
        except:
            logger.info((data_row['number'], code, ori_d, output[:len(ori_d)]))
            continue
        ori_d = list(eval(data_row['data']))
        align_output = align_data(ori_d, output)
        if align_output is None:
            logger.info((data_row['number'], code, ori_d, output[:len(ori_d)]))
            continue
        # assert align_output is not None, 
        align_len = len(align_output)
        if align_output is not None and len(align_output) > len(ori_d):
            xst = int(data_row['offset'].split(',')[0])
            # 1, 2, 3, ..., 9, 10. length=10, ([9, 10], [f[9], f[10]])
            data_row['extra_data'] = (list(range(align_len-10+xst, align_len+xst)), align_output[-10:])

        data_row['max_output_runtime'] = run_time
        with open(save_path, 'a') as f:
            f.write(json.dumps(data_row) + '\n')

        save_d = {
            'number': data_row['number'],
            'mathematica': code, 
            'run_time': run_time,
            'length': align_len,
            'output': align_output
        }
        with open(data_path, 'a') as f:
            f.write(json.dumps(save_d) + '\n')


if __name__ == '__main__':
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f"logs/log_{timestamp}.log"
    # log_file_name = f"logs/debug.log"
    logger.remove()
    logger.add(
        log_file_name,
        level='DEBUG',
        format="{time} {level} {module}:{line} {message} {exception}",
        rotation='500 MB'
    )
    path = 'data/v1/first_version_data.jsonl'
    save_path = 'data/v1/first_version_data_expand.jsonl'
    # run_expand_mathematica(path, save_path)
    # run_expand_mathematica()
    path = save_path
    save_path = 'data/v1/first_version_data_max_length_limit10_30.jsonl'
    # run_bs_task(path, save_path)
    path = save_path
    save_path = 'data/v1/first_version_data_max_length_limit10_30_output.jsonl'
    data_path = 'data/v1/first_version_data_max_length_limit10_30_all_output.jsonl'
    select_codes(path, save_path, data_path)