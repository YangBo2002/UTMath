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