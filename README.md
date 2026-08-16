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
│       ├── data.yml             # 应用元数据（名称/描述/分类/版本/警告/端口/环境变量等）
│       ├── docker-compose.yml   # Docker Compose 模板
│       └── icon.png / icon.svg  # 应用图标（建议 256x256，PNG 或 SVG）
└── scripts/
    ├── generate_index.py # 扫描 apps/ 生成 index.json 的脚本
    ├── batch_add_apps.py # 批量生成应用定义（compose + data.yml + 图标）的核心脚本
    ├── add_categories.py # 为已有 data.yml 补写 category 分类字段（幂等）
    └── download_icons.py # 批量下载官方图标的脚本
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
category: "监控/运维"           # 应用分类（见「分类体系」，用于商店按分类筛选）
description: "..."             # 产品介绍（多行用 > 块状语法）
homepage: "https://..."        # 官方网站
source: "https://github.com/..."  # 开源社区（GitHub 仓库地址，README 按钮依赖它）
arch:                          # 支持架构
  - "amd64"
  - "arm64"

# 选填
versions:                      # 可选版本列表（下拉选择，第一个为默认版本）
  - { tag: "1",      label: "最新" }
  - { tag: "1.23.0", label: "1.23.0" }
warn: "..."                    # 安装版本警告（有值则安装时先弹出居中警告，需滚动到底并确认）
ports:                         # 容器内端口（面板据此生成外部端口映射，支持多端口分别映射）
  - { container: 3001, label: "Web 界面", protocol: "tcp" }
  - { container: 22,   label: "SSH",      protocol: "tcp" }
env:                           # 常用环境变量（面板据此预填）
  - { name: "TZ", default: "Asia/Shanghai", desc: "时区" }
```

#### 分类体系（category）

应用必须归入以下 6 个分类之一：

| 分类 | 说明 | 示例 |
| --- | --- | --- |
| `数据库/存储` | 数据库、缓存、存储服务 | MySQL、Redis、PostgreSQL、NocoDB |
| `面板/网站` | Web 应用、建站、网盘列表、导航 | WordPress、Gitea、AList、Nextcloud |
| `AI/开发` | AI 应用、开发工具、笔记本 | Open WebUI、code-server、Jupyter |
| `网络/工具` | 内网穿透、代理、网络工具 | frp、nps、RSSHub、Pixiv 工具 |
| `监控/运维` | 监控、日志、运维平台 | Uptime Kuma、Zabbix、Kibana、Watchtower |
| `开发/DevOps` | DevOps、CI/CD、基础设施 | GitLab、Consul、Dockge、runner |

#### 版本警告（warn）

若应用存在社区认可的"安全版本"或"不建议升级"的情况，请在 `warn` 字段填写说明文字，
面板会在用户点击安装时**先弹出居中的版本安全警告**，用户需滚动到弹窗底部并确认后才可继续安装。
示例（AList）：

```yaml
warn: "Alist 社区认可相对安全版本是 3.40；推荐使用新一代版本 OpenList，建议不要将其更新到更新的版本。"
versions:
  - { tag: "v3.40.0", label: "3.40（社区推荐）" }   # 第一个为默认版本
  - { tag: "latest", label: "最新" }
```

> 注意：部分镜像 tag 自带 `v` 前缀（如 `xhofe/alist:v3.40.0`），此时 `versions[].tag`
> 必须完整填写带前缀的 tag（`v3.40.0`），面板会按原样替换 `${VERSION}`。

### 3. docker-compose.yml 约定

- 镜像版本 tag 用占位符 `${VERSION}`（可选，面板会在安装时替换为用户选择的版本）：
  ```yaml
  services:
    uptime-kuma:
      image: louislam/uptime-kuma:${VERSION}
  ```
- **主服务识别**：面板只给"主服务"映射声明的端口。主服务 = 显式 `map_ports: true`
  的服务（Web 界面所在）；未指定时默认取**第一个使用 `${VERSION}` 镜像的服务**。
  其余配套服务（db / redis 等）不会映射端口，避免端口冲突。
  多服务应用的 Web 端口若在配套服务上（如 Zabbix 的 Web 由 `zabbix-web` 提供），
  需在对应服务上显式声明 `map_ports: true`：
  ```yaml
  services:
    zabbix-web:
      image: zabbix/zabbix-web-nginx-pgsql:alpine-${VERSION}
      map_ports: true    # 声明该服务为主服务，映射声明端口
  ```
- **覆盖入口 / 启动命令**：需要时可为服务声明 `entrypoint`（数组）或 `command`（字符串），
  例如命令行工具镜像以保活方式常驻、等待用户在容器终端手动执行：
  ```yaml
  services:
    pixivd:
      image: ghcr.io/bebound/pixivd:${VERSION}
      entrypoint: ["/bin/sh", "-c", "sleep infinity"]   # 覆盖 CLI 入口，保活等待手动调用
  ```
- `restart`、端口映射、`TZ` 环境变量、CPU/内存限制由面板按用户安装选项自动注入，
  模板中可给出合理的默认值。**用户可分别修改每个容器的外部端口**（多端口应用）。

### 4. 提交 PR

推送分支后提交 Pull Request 到 `main`，**合并后 CI 会自动重建索引并发布**，无需人工干预。

---

## 索引生成规范

### generate_index.py

扫描 `apps/` 下所有应用（读取各自 data.yml），生成统一的 `index.json`：

- 透传 `category`、`warn` 等新字段；
- **置底机制**：`_LAST_APPS` 集合中的应用会排到索引列表末尾（如 `alist` 有社区版本建议，不宜置顶）；
  其余应用按 id 字母序排列；
- 每个应用必须包含 `data.yml` 与 `docker-compose.yml`，缺少时跳过并告警；
- `icon.png` / `icon.svg` 缺失时仅告警，不中断生成。

### batch_add_apps.py

批量生成应用的 `docker-compose.yml` 与 `data.yml` 并下载图标，是新增大量应用的首选方式：

- `APPS` 字典定义每个应用的元数据（名称/描述/分类/版本/端口/环境变量/服务/图标候选等）；
- `CATEGORY` 字典维护 `app_id -> 分类名` 映射，`gen_data()` 会把 `category` 写入 data.yml；
- `gen_compose()` 自动生成 compose，支持 `map_ports`、`entrypoint`、`command`、
  多服务依赖（`depends_on`）等约定；
- `warn` 字段非空时写入 data.yml，供前端安装弹窗展示。

### index.json 结构

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
      "category": "监控/运维",
      "warn": "",
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

- **默认远程源**：面板未配置「索引地址」时，默认使用
  `https://wuhulab.github.io/Graw-app-store/index.json`；
- **每日拉取限制**：远程索引**最多每天拉取一次**（含手动点击「刷新」，一天内重复刷新会提示已达上限）；
- **开发版优先本地**：开发环境（存在 `app-store/` 目录）时面板**优先使用本地 `index.json`**，
  不拉取远程索引，便于离线调试；
- **首次进入免责声明**：用户首次打开应用商店会弹出《Graw 社区应用商店 免责声明》（v1.1.0），
  需滚动到弹窗底部并勾选同意后才能进入，同意状态保存在浏览器本地。

> 提示：非开发环境下若「索引地址」留空，则使用上述默认远程源。

### 本地手动生成索引

未配置 CI 时也可本地生成：

```bash
# 指定目标仓库（用于生成 gh-pages raw 链接），<owner>/<repo> 为 app-store 独立仓库地址
GRAW_STORE_REPO=<owner>/<repo> python scripts/generate_index.py
```
