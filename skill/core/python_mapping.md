# Python Mapping Guide

> Matlab → Python 工程化映射。基于《数学建模算法与应用》中涉及的Matlab方法。

---

## 工程目录结构

```
project/
├── data/              # 原始数据
│   ├── raw/           # 原始数据文件
│   └── cleaned/       # 清洗后数据
├── src/               # 源代码
│   ├── preprocess.py  # 数据预处理
│   ├── model.py       # 模型定义
│   ├── solver.py      # 求解器
│   └── visualize.py   # 可视化
├── model/             # 模型输出
│   ├── results.json   # 求解结果
│   └── params.json    # 模型参数
├── report/            # 报告输出
│   ├── figures/       # 图表
│   └── tables/        # 表格
└── main.py            # 主入口
```

---

## 核心库对照表

| Matlab功能 | Python替代 | 导入 |
|-----------|-----------|------|
| linprog | scipy.optimize.linprog | `from scipy.optimize import linprog` |
| fmincon | scipy.optimize.minimize | `from scipy.optimize import minimize` |
| intlinprog | pulp.LpProblem | `import pulp` |
| ode45 | scipy.integrate.solve_ivp | `from scipy.integrate import solve_ivp` |
| fitcsvm | sklearn.svm.SVC | `from sklearn.svm import SVC` |
| fitctree | sklearn.tree.DecisionTreeClassifier | `from sklearn.tree import DecisionTreeClassifier` |
| kmeans | sklearn.cluster.KMeans | `from sklearn.cluster import KMeans` |
| pca | sklearn.decomposition.PCA | `from sklearn.decomposition import PCA` |
| regress | sklearn.linear_model.LinearRegression | `from sklearn.linear_model import LinearRegression` |
| plsregress | sklearn.cross_decomposition.PLSRegression | `from sklearn.cross_decomposition import PLSRegression` |
| pdist/linkage | scipy.cluster.hierarchy | `from scipy.cluster.hierarchy import linkage, fcluster` |
| corrcoef | numpy.corrcoef | `import numpy as np` |
| eig | numpy.linalg.eig | `import numpy as np` |
| plot/mesh | matplotlib.pyplot | `import matplotlib.pyplot as plt` |
| figure/surf | matplotlib + mpl_toolkits | `from mpl_toolkits.mplot3d import Axes3D` |
| imread/imwrite | PIL.Image | `from PIL import Image` |
| fft/ifft | numpy.fft | `import numpy.fft as fft` |

---

## 常用算法Python实现

### 1. 线性规划

```python
from scipy.optimize import linprog

# min c^T x, s.t. A_ub x <= b_ub, A_eq x = b_eq
c = [-4, -3]  # 注意：linprog默认求最小值，最大化需取负
A = [[2, 1], [1, 1], [0, 1]]
b = [10, 8, 7]
bounds = [(0, None), (0, None)]

result = linprog(c, A_ub=A, b_ub=b, bounds=bounds)
print(f"最优解: x={result.x}")
print(f"最优值: {-result.fun}")  # 取负还原为最大化
```

### 2. 非线性规划

```python
from scipy.optimize import minimize

def objective(x):
    return -(4*x[0] + 3*x[1])  # 最大化

constraints = [
    {'type': 'ineq', 'fun': lambda x: 10 - 2*x[0] - x[1]},
    {'type': 'ineq', 'fun': lambda x: 8 - x[0] - x[1]},
    {'type': 'ineq', 'fun': lambda x: 7 - x[1]}
]
bounds = [(0, None), (0, None)]

result = minimize(objective, [0, 0], method='SLSQP',
                  bounds=bounds, constraints=constraints)
print(f"最优解: x={result.x}")
print(f"最优值: {-result.fun}")
```

### 3. 整数规划

```python
import pulp

prob = pulp.LpProblem("IP", pulp.LpMaximize)
x1 = pulp.LpVariable("x1", lowBound=0, cat='Integer')
x2 = pulp.LpVariable("x2", lowBound=0, cat='Integer')

prob += 4*x1 + 3*x2  # 目标函数
prob += 2*x1 + x2 <= 10  # 约束
prob += x1 + x2 <= 8
prob += x2 <= 7

prob.solve()
print(f"最优解: x1={x1.varValue}, x2={x2.varValue}")
print(f"最优值: {pulp.value(prob.objective)}")
```

### 4. 常微分方程数值解

```python
from scipy.integrate import solve_ivp
import numpy as np

def ode_system(t, y):
    """二阶ODE降阶为一阶方程组"""
    x, v = y  # y = [位置, 速度]
    dxdt = v
    dvdt = -k/m * x - c/m * v + F(t)/m  # 弹簧-阻尼系统
    return [dxdt, dvdt]

# 初始条件
y0 = [0, 0]  # [x(0), v(0)]
t_span = (0, 10)
t_eval = np.linspace(0, 10, 1000)

sol = solve_ivp(ode_system, t_span, y0, t_eval=t_eval, method='RK45')
print(f"解的形状: {sol.y.shape}")  # (2, 1000)
```

### 5. 灰色预测 GM(1,1)

```python
import numpy as np

def gm11_predict(x0, predict_n):
    """GM(1,1)灰色预测"""
    n = len(x0)
    # 级比检验
    lam = x0[:-1] / x0[1:]
    if not (np.exp(-2/(n+1)) < lam.min() and lam.max() < np.exp(2/(n+1))):
        print("Warning: 级比检验未通过")
    # 累加生成
    x1 = np.cumsum(x0)
    # 构造数据矩阵
    B = np.column_stack([-0.5*(x1[:-1]+x1[1:]), np.ones(n-1)])
    Y = x1[1:]
    # 参数估计
    params = np.linalg.lstsq(B, Y, rcond=None)[0]
    a, b = params[0], params[1]
    # 预测
    result = np.zeros(n + predict_n)
    result[0] = x0[0]
    for k in range(1, n + predict_n):
        result[k] = (x0[0] - b/a) * np.exp(-a*k) + b/a
    # 还原
    predict = np.diff(result)
    predict = np.insert(predict, 0, x0[0])
    return predict[-predict_n:]
```

### 6. TOPSIS评价法

```python
import numpy as np

def topsis(matrix, weights, benefit_indices, cost_indices):
    """
    TOPSIS法综合评价
    matrix: 决策矩阵 (m×n, m个方案, n个指标)
    weights: 权重向量
    benefit_indices: 效益型指标索引
    cost_indices: 成本型指标索引
    """
    # 向量规范化
    norm = np.sqrt(np.sum(matrix**2, axis=0))
    B = matrix / norm
    # 加权
    C = B * weights
    # 确定正负理想解
    C_star = np.zeros(matrix.shape[1])
    C_0 = np.zeros(matrix.shape[1])
    for j in benefit_indices:
        C_star[j] = np.max(C[:, j])
        C_0[j] = np.min(C[:, j])
    for j in cost_indices:
        C_star[j] = np.min(C[:, j])
        C_0[j] = np.max(C[:, j])
    # 计算距离
    d_plus = np.sqrt(np.sum((C - C_star)**2, axis=1))
    d_minus = np.sqrt(np.sum((C - C_0)**2, axis=1))
    # 综合评价指数
    C_j = d_minus / (d_plus + d_minus)
    return C_j
```

### 7. 层次聚类

```python
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
import matplotlib.pyplot as plt
import numpy as np

def hierarchical_clustering(data, method='ward', n_clusters=3):
    """层次聚类"""
    # 计算距离矩阵和聚类
    Z = linkage(data, method=method)
    # 获取聚类结果
    labels = fcluster(Z, n_clusters, criterion='maxclust')
    # 绘制聚类图
    plt.figure(figsize=(10, 6))
    dendrogram(Z)
    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('Sample Index')
    plt.ylabel('Distance')
    plt.show()
    return labels
```

### 8. 遗传算法

```python
import numpy as np

def genetic_algorithm(objective, n_vars, bounds, pop_size=50,
                      n_generations=100, pc=0.8, pm=0.1):
    """遗传算法"""
    # 初始化种群
    pop = np.random.uniform(bounds[:, 0], bounds[:, 1], (pop_size, n_vars))
    
    for gen in range(n_generations):
        # 适应度评估
        fitness = np.array([objective(ind) for ind in pop])
        # 选择（锦标赛选择）
        selected = np.zeros_like(pop)
        for i in range(pop_size):
            idx1, idx2 = np.random.choice(pop_size, 2, replace=False)
            selected[i] = pop[idx1] if fitness[idx1] < fitness[idx2] else pop[idx2]
        # 交叉
        for i in range(0, pop_size-1, 2):
            if np.random.random() < pc:
                alpha = np.random.random()
                child1 = alpha * selected[i] + (1-alpha) * selected[i+1]
                child2 = (1-alpha) * selected[i] + alpha * selected[i+1]
                selected[i], selected[i+1] = child1, child2
        # 变异
        for i in range(pop_size):
            if np.random.random() < pm:
                j = np.random.randint(n_vars)
                selected[i, j] = np.random.uniform(bounds[j, 0], bounds[j, 1])
        pop = selected
    
    # 返回最优解
    fitness = np.array([objective(ind) for ind in pop])
    best_idx = np.argmin(fitness)
    return pop[best_idx], fitness[best_idx]
```

---

## 可视化模板

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
matplotlib.rcParams['axes.unicode_minus'] = False

def setup_academic_style():
    """设置学术图表风格"""
    plt.rcParams.update({
        'font.size': 10.5,
        'axes.labelsize': 10.5,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'figure.figsize': (8, 6),
        'axes.grid': True,
        'grid.alpha': 0.3,
    })
```
