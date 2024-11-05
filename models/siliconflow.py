import requests
import json
import sys
import os
import re
from tenacity import retry, stop_after_attempt, wait_random_exponential
from loguru import logger

from models import common


class SiliconFlowModel(common.Model):
    def __init__(
        self,
        model_name: str
    ):
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model_name: str = model_name
        self.key = self.check_api_key()
        self.headers =  {
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json'
        }
        logger.info(f'Setting model {self.model_name}...')
        self.model_info = self.get_model_info()
        if self.model_name not in self.model_info:
            raise ValueError(f"No model named {self.model_name} in Theb. Please see https://docs.theb.ai/models.")

        self.cost_per_input = -1
        self.cost_per_output = -1

    def get_model_info(self):
        url = "https://api.siliconflow.cn/v1/models"
        response = requests.request("GET", url, headers=self.headers)
        res_d = response.json()['data']
        model_info = {x['id']: x for x in res_d}
        return model_info

    def check_api_key(self) -> str:
        key = os.getenv("SILICONFLOW_API_KEY")
        if not key:
            print("Please set the SILICONFLOW_API_KEY env var")
            sys.exit(1)
        return key

    def setup(self) -> None:
        pass


    @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
    def call(self, messages: list[dict], **kwargs):
        payload = json.dumps({
            "model": self.model_name,
            "messages": messages,
            "steam": False,
            "temperature": kwargs.get('temperature', common.MODEL_TEMP),
            "top_p": kwargs.get('top_p', common.MODEL_TOPP)
        })
        response = requests.request("POST", self.url, headers=self.headers, data=payload)
        if response.status_code != 200:
            raise TimeoutError(response.text)
        else:
            data = response.json()
            if "error" in data:
                raise Exception(data)

        content = data['choices'][0]['message']['content']

        usage_stats = data['usage']
        input_tokens = int(usage_stats['prompt_tokens'])
        output_tokens = int(usage_stats['completion_tokens'])
        # cost = self.calc_cost(input_tokens, output_tokens)
        # common.thread_cost.process_cost += cost
        common.thread_cost.process_input_tokens += input_tokens
        common.thread_cost.process_output_tokens += output_tokens

        return content,input_tokens,output_tokens


if __name__ == '__main__':
    llm = SiliconFlowModel(model_name='Qwen/Qwen2.5-Math-72B-Instruct')
    msgs = [{'role': 'user', 'content': 'who are you?'}]
    response, inputs_tokens, outputs_tokens = llm.call(msgs)
    print(response)
    msgs.append({'role': 'assistant', 'content': response})
    msgs.append({'role': 'user', 'content': 'How dare you?'})
    print(llm.call(msgs))
    print(llm.get_overall_exec_stats()) # 获取当前花了多少钱
