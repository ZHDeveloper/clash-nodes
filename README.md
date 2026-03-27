# clash-nodes

GitHub 节点聚合与订阅生成工具。它会搜索公开 GitHub 仓库中的订阅文件或 README 里的 GitHub 订阅链接，汇总后交给 [`beck-8/subs-check`](https://github.com/beck-8/subs-check) 做测活、去重和转换，然后把结果发布到仓库里的 [`output/`](/Users/king/Documents/clash-nodes/output) 目录。

## 功能

- 搜索公开仓库并提取 `yml/yaml/txt/sub` 等候选订阅文件
- 解析 README 中指向 GitHub `blob/raw` 的链接并统一转为 raw 地址
- 使用 allowlist/blocklist 控制来源
- 通过 Docker 运行 `subs-check`
- 输出 `all.yaml`、`base64.txt`
- 支持 GitHub Actions 每天自动更新

## 本地使用

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

export GH_TOKEN=你的_GitHub_Token
clash-nodes discover
clash-nodes build
# 或者一步完成
clash-nodes run
```

生成后的文件会放在 [`output/`](/Users/king/Documents/clash-nodes/output)，中间状态放在 [`data/`](/Users/king/Documents/clash-nodes/data)。

## 仓库结构

- [`src/clash_nodes/github_search`](/Users/king/Documents/clash-nodes/src/clash_nodes/github_search)
- [`src/clash_nodes/pipeline`](/Users/king/Documents/clash-nodes/src/clash_nodes/pipeline)
- [`src/clash_nodes/subs_check`](/Users/king/Documents/clash-nodes/src/clash_nodes/subs_check)
- [`config/allowlist.txt`](/Users/king/Documents/clash-nodes/config/allowlist.txt)
- [`config/blocklist.txt`](/Users/king/Documents/clash-nodes/config/blocklist.txt)
- [`.github/workflows/update-subscriptions.yml`](/Users/king/Documents/clash-nodes/.github/workflows/update-subscriptions.yml)
