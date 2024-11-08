import json
import sys
import os
import time
from utils.construct_aseq_prompt import make_aseq_prompt
from models.openai_gpt import OpenAIModel
from data_collection.category_cluster import ASeqFactory

problem_path = r'data/oeis_problem.jsonl'
save_path = r'data/sample_example/gpt-4o_test.jsonl'

seq_db = ASeqFactory(problem_path)

def RCoT(sequence, model_name):
    prompt_reasoning = make_aseq_prompt(sequence, turn=1)
    prompt_coding = make_aseq_prompt(sequence, turn=2)

    first_llm = OpenAIModel(model_name)
    second_llm = OpenAIModel(model_name)
    
    msgs = [{'role': 'user', 'content': prompt_reasoning}]
    content, _, _ = first_llm.call(msgs)
    msgs.append({'role': 'assistant', 'content': content})
    msgs.append({'role': 'user', 'content': prompt_coding})
    content, _, _ = second_llm.call(msgs)
    msgs.append({'role': 'assistant', 'content': content})
    
    return msgs



cnt = 0
task_id_done = set()
with open(save_path, 'r', encoding='utf-8') as file:
    for line in file:
        item = json.loads(line)
        task_id_done.add(item['task_id'])
cnt_done = len(task_id_done)
task_id_done_discard = set()

with open(problem_path, 'r', encoding='utf-8') as file:
    flag = 1
    if cnt_done == 0:
        flag = 0
    else:
        cnt+=cnt_done
    for line in file:
        item = json.loads(line)
        if flag == 1:
            if item['task_id'] in task_id_done:
                task_id_done.discard(item['task_id'])
                task_id_done_discard.add(item['task_id'])
                if len(task_id_done) == 0:
                    flag = 0
                    print(f'已加载{save_path}已完成数据')
                    print(f'已加载{cnt_done}条数据')
                continue
            elif item['task_id'] in task_id_done_discard:
                continue
        print(item['task_id'])
        model_name = 'gpt-4o-2024-08-06'
        try:
            msgs, input_tokens_first, output_tokens_first, input_tokens_second, output_tokens_second = RCoT(seq_db, item, model_name)
        except:
            continue
        temp_dictionary = {}
        temp_dictionary['task_id'] = item['task_id']
        temp_dictionary['model'] = model_name
        temp_dictionary['input_tokens_first'] = input_tokens_first
        temp_dictionary['output_tokens_first'] = output_tokens_first
        temp_dictionary['input_tokens_second'] = input_tokens_second
        temp_dictionary['output_tokens_second'] = output_tokens_second
        temp_dictionary['messages'] = msgs
        print(temp_dictionary)
        with open(save_path, 'a',encoding='utf-8') as save_file:
            save_line = json.dumps(temp_dictionary, ensure_ascii=False)
            save_file.write(save_line + '\n')
        cnt+=1
        if cnt%10 == 0:
            print(cnt)
