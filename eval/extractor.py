import re


def extract_code(response, keyword):
    """keyword = "def solution" """
    pattern = re.compile(r'```python(.*?)```', re.DOTALL)

    # 搜索匹配
    matches = pattern.findall(response)

    # 输出结果
    for match in matches:
        if keyword in match:
            return match

    return ""


if __name__ == '__main__':
    text = """以下是使用Python实现的代码，根据我们推导的公式计算出给定输入变量数目n的canalizing Boolean functions数量。

```python
import math

def solution(n: int) -> int:
    if n == 0:
        return 2  # 特殊情况，n = 0 时有两个常数函数
    # 递推公式：C(n) = 2 * (2^n - 1) * 2^(2^(n-1))
    result = 2 * (2 ** n - 1) * 2 ** (2 ** (n - 1))
    return result

# 示例函数调用
print(solution(1))  # Example input
print(solution(2))  # Example input
```

### 代码解释

1. **导入math库**：
   尽管在这个实现中我们没有直接使用到`math`库的函数，但是如果考虑到大数运算，可以引入来提高效率。

2. **定义solution函数**：
   根据已推导出的公式 \( C(n) = 2 \times (2^n - 1) \times 2^{2^{n-1}} \)，我们用Python代码实现，并返回对应的结果。

3. **特殊情况处理**：
   对于 \( n = 0 \)，函数数目为常数函数，因此有2个 (0 恒定、1 恒定)。对于此特殊情况，我们直接返回2。

4. **递推公式应用**：
   我们用了公式中乘方的计算，并在代码中直接返回结果。

将示例函数调用部分用于测试以便验证计算结果是否正确。

```python
print(x) # 测试
```"""
    print(extract_code(text, keyword="def solution"))