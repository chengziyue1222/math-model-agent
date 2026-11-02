# 图表代码库中文命名规范

图表的中文名按统计含义和建模用途命名。英文字符串仍是稳定的 Python 键，中文名是同一个注册项的真实调用别名，不是只改网页标题。

```python
from algorithms.figures import get_figure, get_spec, list_figures

fig = get_figure("直方图")([1.2, 1.8, 2.1, 2.4])
assert get_spec("直方图").name == "histogram"
```

## 命名原则

- 先写图形结构，再写用途：`相关网络图`、`空间热图`、`模型混淆矩阵`。
- 同一结构按分析对象区分：`相关矩阵`、`转移矩阵`、`邻接矩阵`不合并。
- 同一对象按统计问题区分：`散点图`、`趋势散点图`、`联合密度图`分别注册。
- 方法名保留约定缩写：`ROC曲线`、`PR曲线`、`t-SNE图`、`UMAP图`、`TOPSIS权重图`。
- `name`（英文键）用于文件、代码兼容和路径；`name_zh`（中文名）用于调用、元数据、目录和论文图注草稿。

## 查询目录

```python
list_figures(chinese=True)       # 仅返回中文名
list_figures(detailed=True)      # 同时返回 name、name_zh、question_zh、required_fields
```

每次导出画廊都会生成 `output/figure-library-gallery/figure_catalog_zh.json`，其中记录 154 个注册项的中文名称、所属类别、所需字段和实现状态。中文别名解析到同一个注册项，不会制造重复图型。
