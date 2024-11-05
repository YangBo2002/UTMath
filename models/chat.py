import requests
import json
import os
import re
from tenacity import retry, stop_after_attempt, wait_random_exponential
from loguru import logger

# url = "https://api.theb.ai/v1/chat/completions"
url = "https://api.baizhi.ai/v1/chat/completions"

prompt = '''Write a python program to complete the following code:
from typing import List


def separate_paren_groups(paren_string: str) -> List[str]:
    """ Input to this function is a string containing multiple groups of nested parentheses. Your goal is to
    separate those group into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within each other
    Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
'''
api_key = os.environ['API_KEY']

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
def call_llm(model_name, prompt):
  payload = json.dumps({
    "model": model_name,
    "messages": [
      {
        "role": "user",
        "content": prompt,
      }
    ],
    "stream": False
  })

  headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
  }

  response = requests.request("POST", url, headers=headers, data=payload)
  try:
    data = response.json()
  except Exception as e:
    print(response)
    raise e
  # print(response.json())

  code_content = data['choices'][0]['message']['content']
  return code_content