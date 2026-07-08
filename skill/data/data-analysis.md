# /data-analysis

## 用途
端到端R数据分析管道：探索→清洗→回归→发表级图表

## 用法
```bash
/data-analysis dataset.csv
```

## 分析流程
1. **数据探索** - 数据结构和分布
2. **数据清洗** - 缺失值和异常值处理
3. **回归分析** - 统计建模
4. **图表生成** - 发表级质量图表

## 输出内容
1. **编号脚本** - 可复现的R脚本
2. **分析报告** - 详细分析报告
3. **图表文件** - 高质量图表
4. **统计结果** - 统计检验结果

## 参数
- `filename`: 数据文件名

## 示例
```bash
/data-analysis survey_data.csv
/data-analysis experimental_data.csv
```

## 输出
生成完整的分析脚本和报告，保存到scripts/R/目录
