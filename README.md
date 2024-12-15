## 📄 UTMath
*UTMath: Math Evaluation with **Unit Test** via Reasoning-to-Coding Thoughts*

*UTMath is a rigorous and expansive benchmark designed to evaluate the mathematical reasoning abilities of Large Language Models (LLMs), with an average of 68 test cases per problem to ensure that the model **truly solves the problem** rather than simply memorizing the answers.*
<ul>
    <li><b>⚡️Multiple Case Validation</b>: Instead of using single cases that can be memorized, our questions are sequence-based, allowing numerous cases for validating true understanding.</li>
    <li><b>🔧True Reasoning Evaluation</b>: Hard cases and runtime metrics help filter memorization and compare solution efficiency, precisely assessing reasoning abilities.</li>
</ul>

*The Reasoning-to-Coding of Thoughts (RCoT) approach complements the UTMath Benchmark by encouraging LLMs to engage in explicit reasoning prior to generating code.RCoT significantly improves the efficiency and effectiveness of the solution.*
<ul>
    <li><b>🏆Code Output Evaluation</b>: We require LLMs to output code, focusing on reasoning rather than direct answers, to better reflect their reasoning skills.</li>
    <li><b>🌐Observation of Reasoning Process</b>: By mandating code implementation, we can observe and validate the LLM's reasoning process, not just the final answer.</li>
</ul>


![overview](./pic/overview.png)

In `data/utmath_problem.jsonl`, you'll find all 1053 problems from the UTMath benchmark, covering 9 mathematical domains. Each problem includes over 68 test cases.

## 📊 Evaluating on UTMath

You can use this sample as a reference for evaluating on UTMath. Please use the following code:
```python
python utmath_eval/utmath_evaluator.py  --problem_file=data/utmath_problem.jsonl --sample_file={your_sample_file_path}
```

For example, you can directly use our response sample:
The file `data/sample_example/gpt-4o_sample.jsonl` contains responses generated using the RCoT method with GPT-4o on the UTMath benchmark. This sample includes responses to all 1053 problems.
```python
python utmath_eval/utmath_evaluator.py  --problem_file=data/utmath_problem.jsonl --sample_file=data/sample_example/gpt-4o_sample.jsonl

# --with_extra_data=True represents testing both easy and hard cases
# --with_extra_data=None represents testing only easy cases
```

## ✍️ RCoT Inference
We have preconfigured the environment to use OpenAI's API to call GPT-4o and apply the RCoT method for reasoning. After setting up your API key in the environment, you can enter the following command:
```python
python get_rcot_response.py --problem_path=data/utmath_problem.jsonl --save_path={your_save_file_path} --model_name={your_llm_name}
```
For example, after setting up the OpenAI API, you can use the following Python code to call GPT-4o and perform reasoning using the RCoT method.
```python
python get_rcot_response.py --problem_path=data/utmath_problem.jsonl --save_path=data/sample_exapmle/gpt-4o_test.jsonl --model_name=gpt-4o-2024-08-06
```


## 🥇 Leaderboard
- The best model, GPT-4o, only solves 26.93\% problem in our benchmark, demonstrate the difficulty of our benchmarks.

![Leaderboard](./pic/leaderboard.png)
Pass Rate and Average Run Time of LLMs on UTMath. We listed the performance of eight large models using PoT(Program of Thoughts) and RCoT methods across a range of metrics. The average run time is calculated based on the problems solved by the PoT or RCoT methods. The efficiency is calculated as: (Avg.Runtime(PoT) - Avg.Runtime(RcoT)) / Avg.Runtime(RcoT).

## 😎 Some interesting findings
We conducted a comprehensive study with 8 LLMs. Some of our key findings are summarized as follows:

- Modern LLMs perform poorly in Graph Theory, Group Theory, Geometry and Topology.
![performance on different problemd categories](./pic/performance_on_different_problems_categories.png)
Performance on Different Problem Categories.(%) Categories are represented by abbreviations. NT: Number Theory; T.: Theory; DM: Discrete Mathematics; CM: Combinatorial Mathematics; GT: Geometry and Topology; PSE: Polynomial and Series Expansions; SN: Special Numbers; FL: Formal Languages.

- RCoT can significantly improve the pass@k performance of LLMs. With RCoT, 7 of 8 evaluated LLMs generated more efficient solutions, with most models achieving higher scores.
![pass@k](./pic/pass_k.png)
Performance comparison of models across PoT and RCoT tasks at different pass@k levels.

- The quality of reasoning significantly impacts the accuracy and efficiency of the model's final solution.
![self-reasoning](./pic/self-reasoning.png)
Performance comparison between self-reasoning and using GPT-4o reasoning for coding across different models. The results show that models perform better when relying on GPT-4o's reasoning output.

We hope our findings contribute to a deeper understanding of current reasoning ability of LLMs and the further development of models.

## 👀 Furthermore
*Additionally, we are releasing not only the UTMath benchmark but also the UTMath-Train dataset, consisting of over 70,000 problem-solving samples. This dataset is designed to support the community in further advancing research on mathematical reasoning and improving LLM performance in this domain.*
