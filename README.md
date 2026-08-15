# Graw 社区应用商店

Graw 社区应用商店（Graw Community App Store）是一个基于 **GitHub + Docker** 的
应用分发机制：

- **Docker 为底层**：每个应用都是一个 docker-compose.yml，面板在本机执行 `docker compose up -d` 一键部署。
- **GitHub 链接即应用**：应用元数据、图标、compose 模板全部托管在 GitHub，通过 GitHub Pages 对外发布。
- **面板拉取索引**：Graw 面板启动应用商店时请求 `index.json`，解析后渲染出应用列表，点击「安装」填写参数即可部署。

---

## 目录结构

```
app-store/
├── index.json            # 统一索引（CI 自动生成，含全部应用元数据）
├── index.html            # GitHub Pages 入口页（指向 index.json）
├── apps/                 # 应用目录，每个应用一个子目录
│   └── <app-id>/
│       ├── data.yml             # 应用元数据（名称/描述/版本/端口/环境变量等）
│       ├── docker-compose.yml   # Docker Compose 模板
│       └── icon.png             # 应用图标（建议 256x256）
└── scripts/
    └── generate_index.py # 扫描 apps/ 生成 index.json 的脚本
```

---

## 如何提交一个新应用

### 1. 创建应用目录

在 `app-store/apps/` 下新建目录，目录名即应用的唯一 `id`（仅英文/数字/`-`/`_`）：

```
apps/<app-id>/
├── data.yml
├── docker-compose.yml
└── icon.png
```

### 2. data.yml 字段说明

```yaml
# 必填
name: "Uptime Kuma"            # 应用显示名称
id: "uptime-kuma"              # 应用唯一 id（必须与目录名一致）
description: "..."             # 产品介绍（多行用 > 块状语法）
homepage: "https://..."        # 官方网站
source: "https://github.com/..."  # 开源社区（GitHub 仓库地址，README 按钮依赖它）
arch:                          # 支持架构
  - "amd64"
  - "arm64"

# 选填
versions:                      # 可选版本列表（下拉选择，第一个为默认「最新」）
  - { tag: "1",      label: "最新" }
  - { tag: "1.23.0", label: "1.23.0" }
ports:                         # 容器内端口（面板据此生成外部端口映射）
  - { container: 3001, label: "Web 界面", protocol: "tcp" }
env:                           # 常用环境变量（面板据此预填）
  - { name: "TZ", default: "Asia/Shanghai", desc: "时区" }
```

### 3. docker-compose.yml 约定

- 镜像版本 tag 用占位符 `${VERSION}`（可选，面板会在安装时替换为用户选择的版本）：
  ```yaml
  services:
    uptime-kuma:
      image: louislam/uptime-kuma:${VERSION}
  ```
- `restart`、端口映射、`TZ` 环境变量、CPU/内存限制由面板按用户安装选项自动注入，
  模板中可给出合理的默认值。

### 4. 提交 PR

推送分支后提交 Pull Request 到 `main`，**合并后 CI 会自动重建索引并发布**，无需人工干预。

---

## 发布到 GitHub 的部署流程

### 自动化（推荐）

仓库内的 GitHub Actions 工作流 `.github/workflows/app-store.yml` 自动处理：

| 触发条件 | 行为 |
| --- | --- |
| `main` 分支任意变更（含 PR 合并） | 重新扫描 `apps/`，生成 `index.json`，推送到 `gh-pages` 分支 |
| 手动触发（Actions 页面 → Run workflow） | 同上，按需重建 |

工作流步骤：

1. 检出代码；
2. 安装 PyYAML；
3. 运行 `python scripts/generate_index.py`，注入 `GITHUB_REPOSITORY`
   环境变量，生成的 `download_url` 均指向 gh-pages 分支的 raw 链接；
4. 将 `index.json` + `index.html` + `apps/` 打包，强推到 `gh-pages` 分支。

### 开启 GitHub Pages

1. 打开仓库 **Settings → Pages**；
2. Source 选择 **Deploy from a branch**；
3. Branch 选择 **`gh-pages`**，目录选择 **`/ (root)`**；
4. 保存后，索引即可通过以下地址访问：

```
https://<owner>.github.io/<repo>/index.json
```

### 在 Graw 面板中配置

1. 登录面板 → 桌面打开「应用商店」；
2. 点右上角「索引地址」；
3. 填入上面生成的 `index.json` 地址；
4. 「保存并刷新」，应用列表即从远程索引加载。

> 提示：若「索引地址」留空，面板会回退使用本机 `app-store/index.json`（开发/离线调试用）。

### 本地手动生成索引

未配置 CI 时也可本地生成：

```bash
# 指定目标仓库（用于生成 gh-pages raw 链接），<owner>/<repo> 为 app-store 独立仓库地址
GRAW_STORE_REPO=<owner>/<repo> python scripts/generate_index.py
```

---

## 索引文件结构

`index.json` 顶层：

```json
{
  "store": {
    "name": "Graw Community App Store",
    "repo": "<owner>/<repo>",
    "base_url": "https://raw.githubusercontent.com/<owner>/<repo>/gh-pages/",
    "updated_at": "2026-08-15T...",
    "app_count": 4
  },
  "apps": [
    {
      "id": "uptime-kuma",
      "name": "Uptime Kuma",
      "description": "...",
      "version": "1",
      "versions": [ { "tag": "1", "label": "最新" } ],
      "homepage": "https://uptime.kuma.pet/",
      "source": "https://github.com/louislam/uptime-kuma",
      "arch": ["amd64", "arm64", "arm/v7"],
      "ports": [ { "container": 3001, "label": "Web 界面", "protocol": "tcp" } ],
      "env": [ { "name": "TZ", "default": "Asia/Shanghai", "desc": "时区" } ],
      "icon": "https://raw.githubusercontent.com/<owner>/<repo>/gh-pages/apps/uptime-kuma/icon.png",
      "compose_url": "https://raw.githubusercontent.com/<owner>/<repo>/gh-pages/apps/uptime-kuma/docker-compose.yml",
      "data_url": "https://raw.githubusercontent.com/<owner>/<repo>/gh-pages/apps/uptime-kuma/data.yml"
    }
  ]
}
```
