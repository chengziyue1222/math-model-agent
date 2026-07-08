# /deploy

## 用途
将Quarto渲染为HTML并同步到docs/用于GitHub Pages部署

## 用法
```bash
/deploy Lecture1
/deploy all
```

## 功能说明
- 渲染Quarto文件为HTML
- 同步到docs/目录
- 配置GitHub Pages部署
- 自动更新索引页面

## 参数
- `filename`: 文件名或"all"部署所有文件

## 示例
```bash
/deploy Lecture01
/deploy all
/deploy index.qmd
```

## 部署流程
1. 渲染Quarto为HTML
2. 复制到docs/目录
3. 更新导航索引
4. 提交到Git仓库
