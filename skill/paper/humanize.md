# /humanize

## 用途
只读检测AI写作痕迹（10个检测维度），只报告不修改

## 用法
```bash
/humanize file.tex --severity high
```

## 检测维度
1. **模板化过渡句** - 机械化的过渡表达
2. **AI陈词滥调** - AI常用的套话
3. **破折号滥用** - 过度使用破折号
4. **句式单一** - 缺乏句式变化
5. **词汇重复** - 词汇使用过于重复
6. **逻辑跳跃** - 逻辑连接不自然
7. **情感平淡** - 缺乏情感色彩
8. **细节不足** - 缺乏具体细节
9. **个人观点缺失** - 缺乏作者观点
10. **文化适应性** - 不符合学术写作规范

## 参数
- `filename`: 文件名
- `--severity`: 检测严格程度（high/medium/low）

## 示例
```bash
/humanize paper.tex --severity high
/humanize manuscript.tex --severity medium
```

## 输出
生成AI写作痕迹检测报告，标注问题段落和建议
