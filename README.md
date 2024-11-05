# UTMath
Data/oeis_problem.jsonl 中为UTMath benchmark中的所有题目，共有1053题，涵盖9个数学领域，每道题目拥有超过68个测试用例
Data/sample_example/gpt-4o_sample.jsonl 中是我们提前使用gpt-4o在RCoT方法上对UTMath benchmark进行推理得出的所有1053个问题的responses 示例
您可以根据该示例体验如何在UTMath上进行评测，请使用以下代码：
```python
python eval/oesi_evaluator.py  --problem_file=data/oeis_problem.jsonl --sample_file={your_sample_file_path} --with_extra_data=True

# 例如，您可以直接使用我们的responses示例：
python eval/oesi_evaluator.py  --problem_file=data/oeis_problem.jsonl --sample_file=data/sample_example/gpt-4o_sample.jsonl  --with_extra_data=True

#with_extra_data=True 代表同时测试easy and hard cases
#with_extra_data=None 代表仅测试easy cases
```
我们预先为您设置了使用opai的api来调用gpt-4o采用RCoT方法进行推理，请在环境中设置好您的api秘钥后，输入以下指令：
```python
python get_oeis_response.py
```
