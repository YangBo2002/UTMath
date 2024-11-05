import json
import os
import tqdm
from data_collection.aseq_data_download import download_and_save_aid_data, AID
# from models.chat import call_llm

a_seq_path = './data/oeis_data.jsonl'
cate_path = './data/categorys.jsonl'


class ASeqFactory:
    def __init__(self, data_path) -> None:
        self.data_path = data_path
        self.a_dict = {}
        with open(data_path) as f:
            for line in f:
                d = json.loads(line)
                self.a_dict[AID(d['number'])] = d

    def get_or_download_a_seq(self, aid: str):
        if aid not in self.a_dict:
            self.a_dict[aid] = download_and_save_aid_data(aid, self.data_path)
        return self.a_dict[aid]
        

def get_categories(path):
    categorys = {}
    with open(path) as f:
        for line in f:
            categorys.update(json.loads(line))
    return categorys


def category_cluster():
    seq_db = ASeqFactory(a_seq_path)
    categories = get_categories(cate_path)
    prompt = '''There are some categories of sequences. Each category has a berif description and an example sequence. You need Help me cluster these categories into less than 10 different domains.
    
    Categories:
    '''
    for i, (cate_name, seqs) in tqdm.tqdm(enumerate(categories.items())):
        if len(seqs) == 0:
            continue
        seq_data = seq_db.get_or_download_a_seq(seqs[0])
        cate_name = cate_name.strip(',  sequences related to')
        prompt +=  f"{i+1}. {cate_name}\nExample: {seq_data['name']}\n\n"
    
    print(prompt)
    print(len(prompt))
    # # response = call_llm(prompt)
    # with open('./data/cate_cluster_1.md', 'w') as f:
    #     f.write(response)
    # print(response)
    # return response


if __name__ == '__main__':
    category_cluster()