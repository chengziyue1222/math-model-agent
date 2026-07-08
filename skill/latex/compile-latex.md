# /compile-latex

## 用途
用XeLaTeX 3遍编译Beamer幻灯片 + bibtex引用解析

## 用法
```bash
/compile-latex Lecture01  # 不含 .tex 后缀
```

## 功能说明
- 自动检测并编译.tex文件
- 支持Beamer幻灯片格式
- 处理bibtex引用解析
- 3遍编译确保交叉引用正确

## 参数
- `filename`: LaTeX文件名（不含.tex后缀）

## 示例
```bash
/compile-latex Lecture01
/compile-latex Chapter03
```
