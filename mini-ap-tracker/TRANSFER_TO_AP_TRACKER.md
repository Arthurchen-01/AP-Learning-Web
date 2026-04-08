# 将 mini-ap-tracker 放到 ap-tracker 仓库根目录

由于当前运行环境无法直连 GitHub（访问 `github.com` 返回 403），我在仓库内提供了自动同步脚本：

- `scripts/publish-mini-ap-tracker.sh`

## 一键执行

在本仓库根目录运行：

```bash
./scripts/publish-mini-ap-tracker.sh https://github.com/Arthurchen-01/ap-tracker .
```

脚本会自动：
1. 克隆 `ap-tracker` 仓库
2. 将 `mini-ap-tracker/` 的内容覆盖到目标仓库根目录
3. 提交 commit
4. 推送到目标仓库 `origin`

## 如果推送失败

通常是 GitHub 认证问题。请先配置任一方式：

- `gh auth login`
- 或配置 SSH key（`git@github.com:...`）
- 或使用 PAT Token 的 HTTPS 凭证

配置完成后重新运行脚本即可。
