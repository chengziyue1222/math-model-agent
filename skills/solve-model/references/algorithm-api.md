# Repository Algorithm API

从仓库根目录运行，或先将 `code/` 加入 `sys.path`：

```python
import sys
sys.path.insert(0, "code")
from algorithms import ahp_weight, topsis, gm11_predict
```

## 决策与评价

- `ahp_weight(A)` → `(weights, lambda_max, CR, passed)`
- `entropy_weight(data)` → 权重
- `topsis(data, weights=None, positive_indicators=None)` → `TOPSISResult`
- `dea(...)`、`pca(...)`、`rsr(...)`、`fahp(...)`

## 预测与拟合

- `gm11_predict(x0, predict_n=5, predict_count=None)` → 字典结果
- `linear_regression(X, y)`、`ridge_regression(X, y, ...)`
- `lagrange_interp(...)`、`newton_interp(...)`、`cubic_spline_interp(...)`
- 移动平均、指数平滑、Gompertz/Logistic 曲线位于 `time_series.py`

## 优化与网络

- `linear_programming(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None, maximize=False)`
- `nonlinear_programming(objective, x0, bounds=None, ..., maximize=False)`
- `genetic_algorithm(fitness_func, n_vars, bounds, ..., vectorized=True)`
- `particle_swarm(...)`、`simulated_annealing(...)`
- `dijkstra(graph, source)`、`floyd(graph)`、`prim_mst(graph)`、`max_flow(...)`

## 仿真与其他

- `monte_carlo_integration(f, a, b, n_samples=100000, seed=None, vectorized=True)`
- `queuing_simulation(...)`、`queuing_mmsk(...)`、`random_walk(...)`
- `GameOfLife`、`ForestFire`、`SIRSModel`、`NaSchTraffic`
- `edge_detection(...)`、`image_segmentation(...)`、`feature_extraction(...)`
- `check_paper(path, figures_dir="figures", results_file=None)`

在使用前以 Python `inspect.signature` 或源代码核对参数；不要从旧 README 猜测函数名或返回值。
