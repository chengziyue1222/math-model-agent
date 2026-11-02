# 图表制作能力改进交付记录

完成日期：2026-09-29。未提交、未推送。开始时工作区干净；原始数据、模型结果、算法求解逻辑和原图均保留。

## 结果

- 统一项目配置、内置回退、150 mm自定义尺寸、7–8 pt常用图字与6 pt默认下限。
- 正式导出统一为PDF、SVG、450 DPI RGB PNG和schema 3元数据；保存前后检查实际文件。
- 六类可执行模板：预测、比较、优化、灵敏度、稳健性、机制流程。
- 程序检查、文件检查和视觉检查独立记录；新导出默认 `NEEDS_VISUAL_REVIEW`。
- 11个固定案例：4张真实波浪能图、6类合成模板、1张保留全部12,000点的密集散点。
- 已查看实际PNG、11页矢量A4校样的Poppler渲染以及灰度；真实案例数值与修改前一致。
- 已备份并同步指定skill；独立临时目录中用安装后的skill生成六个完整交付包。

画廊：[gallery.html](../output/figure-upgrade/gallery.html)。完整成图、元数据、源值验证、校样和日志都在 `output/figure-upgrade/`，该目录沿用仓库原有忽略规则。

## 关键文件

| 文件 | 用途 |
|---|---|
| `code/algorithms/figure_config.py` | 唯一内置默认值、项目配置加载、来源记录、稳定对象颜色/线型/标记 |
| `config/paper_style.yaml` | 当前竞赛版面与样式覆盖值；不是通用官方规格 |
| `code/algorithms/sci_figures.py` | 兼容原接口；自定义尺寸、扩展契约、几何/字体/哈希审查、旧类样式恢复 |
| `code/algorithms/figure_export.py` | 临时目录导出、RGB转换、实际格式/尺寸验证、失败恢复、独立视觉状态 |
| `code/algorithms/figure_templates.py` | 六类注册信息和真实输入绘图；复用diagram的流程布局 |
| `code/visualize.py` | 四张真实结果图迁移到统一导出；改善热图、图例、边距和字号 |
| `code/tests/test_figure_pipeline.py` | 13项有实际数据/边界断言的新增回归测试 |
| `skills/make-model-figures/scripts/minimal_example.py` | 经过执行的最小示例和六类合成样例 |
| `skills/make-model-figures/scripts/render_*_figures.py` | 正式适配器统一配置、来源路径、待核对问题和视觉交接状态 |
| `scripts/build_figure_gallery.py` | 画廊、原图保留、真实源值核对、密集示例、灰度、矢量A4校样和渲染 |
| `scripts/verify_figure_installation.py` | 清除PYTHONPATH，在独立目录验证安装后的skill |
| `skills/make-model-figures/references/execution-and-migration.md` | 配置、字段、执行、验收、兼容与上下游交接 |
| `skills/make-model-figures/references/visual-repairs.md` | 常见视觉问题、修复方法和适用条件 |

同步更新图表skill主文档、标准、审查清单、项目视觉规则；为run-modeling-project、write-model-paper、review-model-paper补充schema 3交接说明。原skill运行时输入/输出角色不变。

## 真实案例与科学含义

### 热力图

- 原图：`figures/fig03_power_heatmap.png`。
- 新图：`output/figure-upgrade/real/fig03_power_heatmap.png`，同目录含PDF/SVG/元数据。
- 来源：`code/results.json`、`code/solve.py`、`code/visualize.py`。
- 2,500个网格值逐点重算一致，最大绝对误差0。
- 保存参数点为 `(r,d)=(4.6409,10.0)`，解析功率7433.295826 W；离散网格最大值7433.221494 W。这两个量未混淆，也未宣称全局最优。
- 原线性范围0.003911–7433.221494 W保留；改变连续色板、星标描边、上边距和图例位置。
- 增加2000/4000/6000 W等值线，采用网格间等值位置计算；热图数据未重采样、平滑或改变归一化。等值线文字增加白色描边。

### 时域三面板

- 原图：`figures/fig01_time_history.png`。
- 新图：`output/figure-upgrade/real/fig01_time_history.png`。
- 从修改前的Git版本执行原绘图函数，和新函数逐条比较全部曲线数组：完全一致。
- 同样的2,000个时刻、零初始条件、RK45积分、保存参数；图中解析稳态均值与瞬态功率分开标注。
- 最终尺寸150 × 145 mm；共享时间轴，取消前两面板重复图例，保留位移与功率各自的纵轴单位。

另外核对阻尼曲线500个响应值、参考线及灵敏度8根条形的数值，均与修改前相同。原4张PNG的SHA-256未变。证据见 `output/figure-upgrade/source_verification.json`。

## 已运行验证

在项目根目录执行：

```powershell
python -m pytest code/tests/test_figure_pipeline.py code/tests/test_sci_figures.py code/tests/test_visualize.py code/tests/test_paper_figure_theme.py code/tests/test_paper_style_config.py code/tests/test_skill_adapters.py code/tests/test_skill_runtime.py -q
```

最终结果：**56 passed in 7.55s**。日志：`output/figure-upgrade/tests.log`。

```powershell
python scripts/build_figure_gallery.py
python scripts/verify_figure_installation.py
python scripts/validate_skills.py
python scripts/validate_adapter_boundaries.py
python C:/Users/Blake/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/Blake/.codex/skills/make-model-figures
python C:/Users/Blake/.codex/skills/make-model-figures/scripts/_runtime/skill_contracts.py --skill make-model-figures --profile competition
python -m ruff check code/algorithms/figure_config.py code/algorithms/figure_export.py code/algorithms/figure_templates.py code/algorithms/sci_figures.py code/visualize.py code/tests/test_figure_pipeline.py scripts/build_figure_gallery.py scripts/verify_figure_installation.py skills/make-model-figures/scripts --output-format concise
git diff --check
```

结果：11个交付包生成并检查；独立安装六个交付包通过；8项skill结构校验通过；适配器边界PASS；skill有效；安装后的契约角色正确；Ruff与diff检查通过。

回归覆盖尺寸/优先级、样式隔离、外部tight、RGB/DPI/像素、缺字、长标签、axes与figure图例、刻度/色条越界、色条面板区分、名称样式稳定、源缺失/哈希变化、实际排序和残差、缺区间时不编造、旧接口及失败导出恢复。

## 安装与最小用法

安装目标：`C:/Users/Blake/.codex/skills/make-model-figures`。

备份：`C:/Users/Blake/.codex/skill-backups/make-model-figures-20260929-233522`。

差异比较未发现独立skill定制；原有运行时由仓库安装工具维护。只同步这一项skill，没有覆盖其他已安装skills。

系统旧算法包包含无关模块差异，予以保留。本次wheel安装在独立环境：`C:/Users/Blake/.codex/runtimes/math-model-figures`；依赖复用当前系统环境，算法模块来自新wheel。不是完全隔离的依赖锁定环境。

构建/安装命令：

```powershell
python -m build --wheel --outdir output/figure-upgrade/dist
python -m venv --system-site-packages C:/Users/Blake/.codex/runtimes/math-model-figures
C:/Users/Blake/.codex/runtimes/math-model-figures/Scripts/python.exe -m pip install --no-deps --force-reinstall output/figure-upgrade/dist/math_model_agent-7.3.0-py3-none-any.whl
python scripts/install_skills.py make-model-figures --force
```

现在可从任意目录运行：

```powershell
python C:/Users/Blake/.codex/skills/make-model-figures/scripts/minimal_example.py --output figure-demo
```

加 `--suite` 运行六类。脚本自动发现独立环境，不存作者绝对路径；其他机器安装wheel或设置 `MATH_MODEL_FIGURES_PYTHON`。独立临时目录测试未使用仓库配置，元数据正确记录builtin来源。

## 兼容与尚未执行项

- 89/183 mm预设和旧公共接口保留；正式项目尺寸使用 `publication_size(None, None, config=cfg)` 或显式 `width_mm`。
- `save_figure` 和旧专业图类保留探索用途、原画布和统计假设；正式六类使用新模板。旧模拟ROC/预测类不能代替真实数据绘图。
- schema 3保留 `audit` 等旧字段；旧schema没有视觉字段时按NOT_CHECKED处理。不能用 `audit.passed` 推断整体通过。
- 严格导出现在会拒绝不存在的源路径或缺字；旧调用方需要修正来源和字体。
- 几何重叠/轴内图例属于提示。实际检查未发现关键数据遮挡；共享时间轴省略重复标签等设计已写入视觉记录。
- **未执行**：实物打印、另一台机器上的SVG字体显示、全仓库无关算法测试；本次不承诺所有旧专业图型均已完成正式版面改造。
- 两个其他问题适配器已迁移并通过相关边界/接口测试，未使用其完整业务输入重跑；本次真实成图验收使用现有波浪能结果。
- Poppler输出Symbol/ArialUnicode默认显示字体配置提示；文件中的实际字体嵌入检查通过，已查看的PNG与PDF渲染未见缺字。保留此环境提示，不当作未运行的检查通过。
- 程序、源值与视觉检查均不能独立证明模型假设或统计结论正确；合成案例不进入真实研究结论。
