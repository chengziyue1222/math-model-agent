# /commit

## 用途
完整commit-PR-merge循环：运行质量门→创建分支→暂存→提交→推送→PR→合并

## 用法
```bash
/commit "你的提交信息"
```

## 工作流程
1. **质量门检查** - 运行代码质量检查
2. **创建分支** - 创建功能分支
3. **暂存更改** - git add更改
4. **提交更改** - git commit更改
5. **推送分支** - git push分支
6. **创建PR** - 创建Pull Request
7. **合并PR** - 合并到主分支

## 参数
- `message`: 提交信息

## 示例
```bash
/commit "feat: 添加新功能"
/commit "fix: 修复bug"
```

## 输出
自动完成整个提交流程
