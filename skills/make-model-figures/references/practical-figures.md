# 实用图型：按问题与数据选择

所有入口通过 `algorithms.figures.get_figure/get_spec/list_figures` 提供中英文名称。先保存数据，再绘制；正式输出继续使用 FigureContract 与 PDF/SVG、450 DPI RGB PNG、`.figure.json`。模拟数据用 `mode="preview", simulated=True`，不能用于真实论文结论。

| 任务 | 入口 | 结构化字段 | 需要声明 |
|---|---|---|---|
| 多对象×时期时序 | sparkline_matrix | row_labels, column_labels, series 单元格 x/y 或 None | unit；scale 默认 shared，independent 要显式标明 |
| 周期组成 | polar_stacked_bar | categories, groups, values 类别×分组 | orientation radial/angular；percent=True 才归一化；默认原量 |
| 人数/直观比例 | pictogram | categories, values | pictogram_mode array/silhouette；icon_value；阵列余量按可见面积，轮廓按高度 |
| 日活动 | calendar_heatmap | dates, values | layout horizontal/vertical；unit；重复日期上游显式聚合 |
| 保存相关/协方差 | correlation_heatmap/covariance_heatmap | matrix, labels；协方差还需 variable_units | 相关范围 [-1,1]；常量相关值未定义；协方差单位为行×列 |
| 单元格组成 | matrix_pie | row_labels, column_labels, groups, values 三维数组 | 固定半径，共享分组图例；零总量无组成 |
| 日期组成/数量 | calendar_glyphs | dates, values；glyph=pie 时还需 groups | glyph bubble/pie；面积标尺；已观测零值独立于缺失 |
| 已计算回归结果 | regression_curve | x,y,curve_x,curve_y | lower/upper 必须成对且 interval_kind 明确；外推虚线；不重新拟合 |
| 频次矩阵 | bubble_matrix | row_labels,column_labels,values 二维非负数组 | 默认面积严格比例；min_area 非零时图例说明偏移 |

`mode` 留给 formal/preview 执行模式，人物形态用 `pictogram_mode`，避免接口冲突。`correlation_matrix` 现在显示固定 [-1, 1] 色域的 Pearson 相关矩阵；原来的成对关系复合视图保留在 `pairgrid`。比较旧成果时登记这一语义修正。

`compute_matrix_statistics` 在计算层要求显式 missing="raise"/"complete_case"，保存方法、有效/原始样本数、单位和矩阵；不暗中填补或逐对删缺失。绘图使用保存矩阵，不作统计推断。日期按实际年份、星期和周定位，闰日有效，灰底表示缺失。

矩阵小图复杂时增大最终高度或减少同页单元格，不无限缩小文字。组成比较需要精确读数时优先堆叠柱或点图；极坐标长度/角度和人物高度不能冒称面积比例。使用全部相关观测，图标过多时增大 icon_value 并说明。共享尺度必须同单位。

运行 `python <skill>/scripts/practical_examples.py --output figures` 得到有来源的模拟示例和机器接口。数据、专用渲染器、配置和导出由安装算法包提供；skill 内不复制算法。成品须按真实尺寸查看 PNG、PDF/SVG 与灰度，再记录视觉审核；登记成功不代表适合论文。
# 人物轮廓与小尺寸排版

`pictogram` 使用圆头、圆肩、连续四肢的站立轮廓；纹理用于灰度区分，不能盖住人物边缘。分组图默认按 150 mm 排列，75 mm 时自动减少每行人数并增加行数；明确指定的 `columns`、高度和项目配色优先。保留全部组名和数值，长标签在所属组旁换行。

人物数组的不足一个仍按**可见多边形面积**填色，例如 67、每图标代表 10 时保留 6 个完整人物及 0.7 个填色人物。轮廓分段模式继续按高度比例，不能与面积比例混称；整人华夫模式继续拒绝对人数取整。形状精修后重新导出并检查 PNG、PDF、SVG、灰度和实际尺寸，不复用旧轮廓的审核。

