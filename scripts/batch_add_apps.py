# -*- coding: utf-8 -*-
"""批量生成 Graw 应用商店应用（compose + data.yml + 图标）。

用法（在 app-store 目录内）:
    python scripts/batch_add_apps.py
"""
import json
import os
import time

APP_STORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(APP_STORE_DIR, "apps")

# 每个应用: id -> dict
#   svc        服务名(目录名也用它)
#   name       显示名
#   desc       中文描述
#   homepage
#   source
#   arch
#   versions   [(tag, label), ...]
#   ports      [(container, label), ...]
#   envs       [(name, default, desc), ...]
#   services   [{name, image, container, volumes:[(host_sub, container_path)], extra_env:[(k,v)], extra_ports:[(host,cont)]}]
#   icon       [候选图标 URL 列表(优先), ...]  或 {"path": "apps/<id>/icon.png", "url": "..."}
#   port_host  默认: 自动与 container 相同

APPS = {
    # ---------------- 数据库 / 存储 ----------------
    "mysql": {
        "name": "MySQL",
        "desc": "世界最流行的开源关系型数据库管理系统，广泛用于各类 Web 应用、企业系统和数据仓库。本模板使用 MySQL 8 官方镜像，数据持久化到本地 data 目录。",
        "homepage": "https://www.mysql.com/",
        "source": "https://github.com/mysql/mysql-server",
        "arch": ["amd64", "arm64"],
        "versions": [("8", "8.x"), ("5.7", "5.7")],
        "ports": [(3306, "MySQL 服务")],
        "envs": [("MYSQL_ROOT_PASSWORD", "root123", "root 密码")],
        "services": [{
            "name": "mysql",
            "image": "mysql:${VERSION}",
            "volumes": [("data", "/var/lib/mysql")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/mysql/mysql-docker@main/mysql_logo.png",
            "https://www.mysql.com/common/logos/logo-mysql-170x115.png",
        ],
    },
    "redis": {
        "name": "Redis",
        "desc": "高性能的开源内存键值数据库，支持字符串、哈希、列表、集合等数据结构，广泛用作缓存、消息队列和会话存储。本模板使用官方 Redis 7 镜像。",
        "homepage": "https://redis.io/",
        "source": "https://github.com/redis/redis",
        "arch": ["amd64", "arm64"],
        "versions": [("7", "7.x"), ("6", "6.x")],
        "ports": [(6379, "Redis 服务")],
        "envs": [("REDIS_PASSWORD", "", "访问密码（留空则不启用）")],
        "services": [{
            "name": "redis",
            "image": "redis:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/redis/redis@unstable/logo.svg",
            "https://redis.io/wp-content/uploads/2024/04/Redis_Logo_Icon_Colour.svg",
        ],
    },
    "postgres": {
        "name": "PostgreSQL",
        "desc": "功能强大的开源关系型数据库，以其可靠性和丰富的数据类型著称，支持复杂查询、事务、扩展与全文检索。本模板使用官方 PostgreSQL 16 镜像。",
        "homepage": "https://www.postgresql.org/",
        "source": "https://github.com/postgres/postgres",
        "arch": ["amd64", "arm64"],
        "versions": [("16", "16.x"), ("15", "15.x")],
        "ports": [(5432, "PostgreSQL 服务")],
        "envs": [
            ("POSTGRES_USER", "postgres", "超级用户"),
            ("POSTGRES_PASSWORD", "postgres123", "超级用户密码"),
            ("POSTGRES_DB", "postgres", "默认数据库"),
        ],
        "services": [{
            "name": "postgres",
            "image": "postgres:${VERSION}",
            "volumes": [("data", "/var/lib/postgresql/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/postgres/postgres@master/doc/src/sgml/images/logo.svg",
            "https://www.postgresql.org/media/img/about/press/elephant.png",
        ],
    },
    "mariadb": {
        "name": "MariaDB",
        "desc": "MySQL 的社区分支，完全兼容并增加更多存储引擎与性能优化，是众多 Linux 发行版的默认数据库。本模板使用官方 MariaDB 11 镜像。",
        "homepage": "https://mariadb.org/",
        "source": "https://github.com/MariaDB/server",
        "arch": ["amd64", "arm64"],
        "versions": [("11", "11.x"), ("10.11", "10.11 LTS")],
        "ports": [(3306, "MariaDB 服务")],
        "envs": [
            ("MARIADB_ROOT_PASSWORD", "root123", "root 密码"),
            ("MARIADB_DATABASE", "", "默认数据库"),
        ],
        "services": [{
            "name": "mariadb",
            "image": "mariadb:${VERSION}",
            "volumes": [("data", "/var/lib/mysql")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/MariaDB/server@main/.github/mariadb-foundation-logo.svg",
            "https://mariadb.org/wp-content/themes/mariadb/images/logo_MariaDB.png",
        ],
    },
    "nocodb": {
        "name": "NocoDB",
        "desc": "开源的 Airtable 替代品，把数据库变成可视化电子表格。支持 MySQL / PostgreSQL / SQLite，拖拽式搭建数据应用，无需编程即可管理数据。",
        "homepage": "https://nocodb.com/",
        "source": "https://github.com/nocodb/nocodb",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [("NC_DB", "", "数据库连接串（默认 SQLite）")],
        "services": [{
            "name": "nocodb",
            "image": "nocodb/nocodb:${VERSION}",
            "volumes": [("data", "/usr/app/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/nocodb/nocodb@master/packages/nc-gui/assets/img/icons/favicon.svg",
            "https://www.nocodb.com/logo.svg",
        ],
    },
    "verdaccio": {
        "name": "Verdaccio",
        "desc": "轻量级、可扩展的私有 npm 仓库代理，让你在本地或内网搭建属于自己的 Node 包源，支持代理与缓存公共 npm 包。",
        "homepage": "https://verdaccio.org/",
        "source": "https://github.com/verdaccio/verdaccio",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(4873, "npm 仓库")],
        "envs": [],
        "services": [{
            "name": "verdaccio",
            "image": "verdaccio/verdaccio:${VERSION}",
            "volumes": [("storage", "/verdaccio/storage"), ("config", "/verdaccio/conf"), ("plugins", "/verdaccio/plugins")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/verdaccio/verdaccio@master/docs/assets/logo/icon.svg",
            "https://verdaccio.org/assets/logo/verdaccio_logo.svg",
        ],
    },
    "sftpgo": {
        "name": "SFTPGo",
        "desc": "功能丰富的 SFTP / HTTP / FTP 服务器，支持本地文件系统及 S3、WebDAV、Google Drive 等存储后端，内置 Web 管理界面与虚拟用户。",
        "homepage": "https://sftpgo.com/",
        "source": "https://github.com/drakkan/sftpgo",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 管理界面"), (2022, "SFTP 服务")],
        "envs": [("SFTPGO_DEFAULT_ROOT_PATH", "/srv/sftpgo/data", "默认根目录")],
        "services": [{
            "name": "sftpgo",
            "image": "drakkan/sftpgo:${VERSION}",
            "volumes": [("data", "/srv/sftpgo/data"), ("home", "/srv/sftpgo/home")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/drakkan/sftpgo@master/docs/assets/logo.png",
            "https://raw.githubusercontent.com/drakkan/sftpgo/master/docs/assets/logo.png",
        ],
    },
    # ---------------- 面板 / 网站 ----------------
    "wordpress": {
        "name": "WordPress",
        "desc": "全球使用最广泛的开源建站与内容管理系统，插件与主题生态极其丰富，适合博客、企业站、电商等各类网站。本模板内置 MySQL 数据库。",
        "homepage": "https://wordpress.org/",
        "source": "https://github.com/WordPress/WordPress",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(80, "Web 界面")],
        "envs": [
            ("WORDPRESS_DB_HOST", "db:3306", "数据库地址"),
            ("WORDPRESS_DB_USER", "wordpress", "数据库用户"),
            ("WORDPRESS_DB_PASSWORD", "wordpress123", "数据库密码"),
            ("WORDPRESS_DB_NAME", "wordpress", "数据库名"),
        ],
        "services": [
            {
                "name": "db",
                "image": "mysql:8.0",
                "volumes": [("dbdata", "/var/lib/mysql")],
                "extra_env": [
                    ("MYSQL_DATABASE", "wordpress"),
                    ("MYSQL_USER", "wordpress"),
                    ("MYSQL_PASSWORD", "wordpress123"),
                    ("MYSQL_ROOT_PASSWORD", "root123"),
                ],
            },
            {
                "name": "wordpress",
                "image": "wordpress:${VERSION}",
                "volumes": [("wpdata", "/var/www/html")],
                "depends_on": ["db"],
            },
        ],
        "icon": [
            "https://cdn.jsdelivr.net/gh/WordPress/wporg-mu-plugins@trunk/images/wordpress.svg",
            "https://s.w.org/images/wmark.png",
        ],
    },
    "gitea": {
        "name": "Gitea",
        "desc": "轻量、快速、自托管的 Git 服务，内存占用小、安装简单，支持仓库、Issue、PR、CI、Wiki 与 Actions，是搭建私有代码托管平台的理想选择。",
        "homepage": "https://gitea.com/",
        "source": "https://github.com/go-gitea/gitea",
        "arch": ["amd64", "arm64", "arm/v7"],
        "versions": [("latest", "最新")],
        "ports": [(3000, "Web 界面"), (22, "SSH")],
        "envs": [
            ("GITEA__server__DOMAIN", "localhost", "域名 / IP"),
            ("GITEA__server__SSH_DOMAIN", "localhost", "SSH 域名"),
        ],
        "services": [{
            "name": "gitea",
            "image": "gitea/gitea:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/go-gitea/gitea@main/assets/logo.svg",
            "https://gitea.com/assets/img/logo.png",
        ],
    },
    "halo": {
        "name": "Halo",
        "desc": "现代化、简洁的 Java 博客系统，拥有丰富的主题与插件生态，基于 Spring Boot 构建，适合个人博客与内容创作。",
        "homepage": "https://halo.run/",
        "source": "https://github.com/halo-dev/halo",
        "arch": ["amd64", "arm64"],
        "versions": [("2", "2.x"), ("2.18", "2.18")],
        "ports": [(8090, "Web 界面")],
        "envs": [("HALO_PLUGIN_ENABLED", "", "需要启用的插件")],
        "services": [{
            "name": "halo",
            "image": "halohub/halo:${VERSION}",
            "volumes": [("data", "/root/.halo2")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/halo-dev/halo@main/logo.png",
            "https://halo.run/logo.svg",
        ],
    },
    "outline": {
        "name": "Outline",
        "desc": "现代团队知识库与 Wiki 平台，支持 Markdown 实时协作编辑、全文搜索与丰富集成，需配合 PostgreSQL 与 Redis 使用。",
        "homepage": "https://www.getoutline.com/",
        "source": "https://github.com/outline/outline",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3000, "Web 界面")],
        "envs": [
            ("DATABASE_URL", "postgres://outline:outline@db:5432/outline", "数据库连接"),
            ("REDIS_URL", "redis://redis:6379", "Redis 连接"),
            ("SECRET_KEY", "change-me", "密钥"),
            ("UTILS_SECRET", "change-me", "工具密钥"),
            ("URL", "http://localhost:3000", "访问地址"),
        ],
        "services": [
            {"name": "redis", "image": "redis:7", "volumes": [("redisdata", "/data")]},
            {
                "name": "db",
                "image": "postgres:16",
                "volumes": [("pgdata", "/var/lib/postgresql/data")],
                "extra_env": [
                    ("POSTGRES_USER", "outline"),
                    ("POSTGRES_PASSWORD", "outline"),
                    ("POSTGRES_DB", "outline"),
                ],
            },
            {
                "name": "outline",
                "image": "docker.getoutline.com/outlinewiki/outline:${VERSION}",
                "volumes": [("data", "/var/lib/outline/data")],
                "depends_on": ["db", "redis"],
            },
        ],
        "icon": [
            "https://cdn.jsdelivr.net/gh/outline/outline@main/logo.svg",
            "https://www.getoutline.com/favicon.svg",
        ],
    },
    "flarum": {
        "name": "Flarum",
        "desc": "优雅、简洁、易扩展的现代化开源论坛软件，界面清新、加载迅速，支持丰富的扩展生态，是搭建社区论坛的好选择。",
        "homepage": "https://flarum.org/",
        "source": "https://github.com/flarum/flarum",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "flarum",
            "image": "crazymax/flarum:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/flarum/framework@master/logo.svg",
            "https://flarum.org/assets/img/logo.png",
        ],
    },
    "tailchat": {
        "name": "Tailchat",
        "desc": "开源的下一代 IM 与协作平台，支持群组、频道、语音、插件与机器人，可完全自托管，构建属于自己的私密通信空间。",
        "homepage": "https://tailchat.msgbyte.com/",
        "source": "https://github.com/msgbyte/tailchat",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(11002, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "tailchat",
            "image": "tailchat-inc/tailchat:${VERSION}",
            "volumes": [("data", "/app/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/msgbyte/tailchat@master/website/static/img/logo.svg",
            "https://raw.githubusercontent.com/msgbyte/tailchat/master/website/static/img/logo.svg",
        ],
    },
    "excalidraw": {
        "name": "Excalidraw",
        "desc": "极简的手绘风格白板工具，支持在线协作、导出为图片与 SVG，适合绘制流程图、架构图与示意图，无需登录即可使用。",
        "homepage": "https://excalidraw.com/",
        "source": "https://github.com/excalidraw/excalidraw",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(80, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "excalidraw",
            "image": "excalidraw/excalidraw:${VERSION}",
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/excalidraw/excalidraw@master/public/excalidraw-logo.svg",
            "https://excalidraw.com/og-image.png",
        ],
    },
    "it-tools": {
        "name": "IT Tools",
        "desc": "开发者的百宝箱，集成 JSON 格式化、JWT 解析、Base64 编解码、Hash 计算、二维码生成等上百个常用工具，全部在浏览器本地运行。",
        "homepage": "https://it-tools.tech/",
        "source": "https://github.com/CorentinTh/it-tools",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(80, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "it-tools",
            "image": "corentinth/it-tools:${VERSION}",
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/CorentinTh/it-tools@main/public/logo.png",
            "https://it-tools.tech/android-chrome-512x512.png",
        ],
    },
    "qinglong": {
        "name": "青龙面板",
        "desc": "定时任务管理面板，支持 JavaScript / Python / Shell 脚本，可用于自动化签到、挂机等任务，自带依赖管理与日志查看。",
        "homepage": "https://qinglong.org.cn/",
        "source": "https://github.com/whyour/qinglong",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5700, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "qinglong",
            "image": "whyour/qinglong:${VERSION}",
            "volumes": [("data", "/ql/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/whyour/qinglong@develop/public/static/favicon.svg",
            "https://raw.githubusercontent.com/whyour/qinglong/develop/public/static/favicon.svg",
        ],
    },
    "sun-panel": {
        "name": "Sun-Panel",
        "desc": "服务器 / NAS 导航面板与浏览器首页，简洁美观、支持图标管理、内外网链接切换与内置小窗口，占用资源极低。",
        "homepage": "https://sun-panel.top/",
        "source": "https://github.com/hslr-s/sun-panel",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3002, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "sun-panel",
            "image": "hslr/sun-panel:${VERSION}",
            "volumes": [("conf", "/app/conf"), ("uploads", "/app/uploads"), ("database", "/app/database")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/hslr-s/sun-panel@master/doc/img/logo.png",
            "https://raw.githubusercontent.com/hslr-s/sun-panel/master/doc/img/logo.png",
        ],
    },
    # ---------------- AI / 开发 ----------------
    "open-webui": {
        "name": "Open WebUI",
        "desc": "可扩展、功能丰富、用户友好的自托管 AI Web 界面，支持 Ollama 与 OpenAI 兼容接口，提供多用户、RAG、模型管理与对话历史。",
        "homepage": "https://openwebui.com/",
        "source": "https://github.com/open-webui/open-webui",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [("OLLAMA_BASE_URL", "", "Ollama 地址（可选）")],
        "services": [{
            "name": "open-webui",
            "image": "ghcr.io/open-webui/open-webui:${VERSION}",
            "volumes": [("data", "/app/backend/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/open-webui/open-webui@main/static/favicon.png",
            "https://openwebui.com/favicon-32x32.png",
        ],
    },
    "n8n": {
        "name": "n8n",
        "desc": "开源的工作流自动化平台，通过可视化节点把应用、数据与 AI 连接起来，支持 400+ 集成，可自托管部署。",
        "homepage": "https://n8n.io/",
        "source": "https://github.com/n8n-io/n8n",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5678, "Web 界面")],
        "envs": [
            ("N8N_SECURE_COOKIE", "false", "是否安全 Cookie"),
            ("GENERIC_TIMEZONE", "Asia/Shanghai", "时区"),
        ],
        "services": [{
            "name": "n8n",
            "image": "n8nio/n8n:${VERSION}",
            "volumes": [("data", "/home/node/.n8n")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/n8n-io/n8n@master/assets/n8n-logo.png",
            "https://n8n.io/logo.png",
        ],
    },
    "one-api": {
        "name": "One API",
        "desc": "OpenAI 接口管理与分发系统，支持多模型统一接入、令牌管理、配额统计，可将各种模型转换为 OpenAI 格式对外提供调用。",
        "homepage": "https://github.com/songquanpeng/one-api",
        "source": "https://github.com/songquanpeng/one-api",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3000, "Web 界面")],
        "envs": [("SESSION_SECRET", "", "会话密钥（建议设置）")],
        "services": [{
            "name": "one-api",
            "image": "justsong/one-api:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/songquanpeng/one-api@main/web/src/assets/logo.svg",
            "https://raw.githubusercontent.com/songquanpeng/one-api/main/web/src/assets/logo.svg",
        ],
    },
    "astrbot": {
        "name": "AstrBot",
        "desc": "多平台 AI 聊天机器人框架，支持 QQ、微信、飞书、Telegram 等平台，可对接主流大模型，自带 WebUI 管理面板与插件生态。",
        "homepage": "https://astrbot.app/",
        "source": "https://github.com/AstrBotDevs/AstrBot",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(6185, "Web 管理界面"), (6199, "OneBot / 消息端口")],
        "envs": [],
        "services": [{
            "name": "astrbot",
            "image": "soulter/astrbot:${VERSION}",
            "volumes": [("data", "/AstrBot/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/AstrBotDevs/AstrBot@main/docs/images/logo.png",
            "https://raw.githubusercontent.com/AstrBotDevs/AstrBot/main/docs/images/logo.png",
        ],
    },
    "llama-cpp": {
        "name": "llama.cpp",
        "desc": "C/C++ 实现的 LLM 推理引擎，支持 GGUF 格式本地运行各种开源大模型，内置 OpenAI 兼容的 HTTP 服务器，可离线部署私有 AI。",
        "homepage": "https://github.com/ggml-org/llama.cpp",
        "source": "https://github.com/ggml-org/llama.cpp",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "HTTP 服务")],
        "envs": [],
        "services": [{
            "name": "llama-cpp",
            "image": "ghcr.io/ggml-org/llama.cpp:${VERSION}",
            "volumes": [("models", "/models")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/ggml-org/llama.cpp@master/logo.png",
            "https://raw.githubusercontent.com/ggml-org/llama.cpp/master/logo.png",
        ],
    },
    "code-server": {
        "name": "code-server",
        "desc": "在浏览器中运行的 VS Code，让你随时随地通过 Web 编写代码，支持扩展安装、终端与 Git 集成，适合远程开发与容器环境。",
        "homepage": "https://coder.com/",
        "source": "https://github.com/coder/code-server",
        "arch": ["amd64", "arm64", "arm/v7"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [
            ("PASSWORD", "", "访问密码（留空则自动生成）"),
            ("SUDO_PASSWORD", "", "sudo 密码（可选）"),
        ],
        "services": [{
            "name": "code-server",
            "image": "codercom/code-server:${VERSION}",
            "volumes": [("data", "/home/coder/.local/share/code-server"), ("config", "/home/coder/.config/code-server")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/coder/code-server@main/docs/logo.svg",
            "https://coder.com/logo.svg",
        ],
    },
    "node-red": {
        "name": "Node-RED",
        "desc": "基于 Node.js 的流式编程工具，通过拖拽节点把设备、API 与服务连接起来，适合物联网、自动化与数据流处理。",
        "homepage": "https://nodered.org/",
        "source": "https://github.com/node-red/node-red",
        "arch": ["amd64", "arm64", "arm/v7"],
        "versions": [("latest", "最新")],
        "ports": [(1880, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "node-red",
            "image": "nodered/node-red:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/node-red/node-red-docker@master/README.md/node-red.svg",
            "https://nodered.org/about/resources/media/node-red-hexagon.svg",
        ],
    },
    "jupyter-notebook": {
        "name": "Jupyter Notebook",
        "desc": "基于浏览器的交互式笔记本，支持 Python 代码、可视化与 Markdown 文档混合编写，是数据科学与教学科研的常用工具。",
        "homepage": "https://jupyter.org/",
        "source": "https://github.com/jupyter/notebook",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8888, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "jupyter",
            "image": "jupyter/notebook:${VERSION}",
            "volumes": [("work", "/home/jovyan/work")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/jupyter/jupyter.github.io@master/assets/main-logo.svg",
            "https://jupyter.org/assets/homepage/main-logo.svg",
        ],
    },
    "deepseek-harness": {
        "name": "DeepSeek Harness",
        "desc": "DeepSeek 官方的开源 AI Agent 框架，一切皆插件，为智能体提供文件、终端、搜索、规划等能力，自带本地 Web 界面。",
        "homepage": "https://deepseek-harness.github.io/deepseek-harness/",
        "source": "https://github.com/deepseek-ai/deepseek-harness",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3080, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "deepseek-harness",
            "image": "node:22-alpine",
            "volumes": [("data", "/root/.dsh")],
            "command": "npx -y @deepseek-ai/dsh web",
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/deepseek-ai/deepseek-harness@master/website/.vuepress/public/logo.png",
            "https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/master/website/.vuepress/public/logo.png",
        ],
    },
    "hermes-agent": {
        "name": "Hermes Agent",
        "desc": "Nous Research 开源的自我改进型 AI Agent，支持多平台消息网关（Telegram / Discord 等）、MCP 工具、技能与记忆系统，可自托管部署。",
        "homepage": "https://hermes-agent.nousresearch.com/",
        "source": "https://github.com/NousResearch/hermes-agent",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8642, "API 服务")],
        "envs": [],
        "services": [{
            "name": "hermes",
            "image": "nousresearch/hermes-agent:${VERSION}",
            "volumes": [("data", "/opt/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/docs/assets/logo.png",
            "https://hermes-agent.nousresearch.com/favicon.svg",
        ],
    },
    "mblog-backend": {
        "name": "Mblog",
        "desc": "开源的极简朋友圈 / 微博系统后端，支持图文发布、关注与广场浏览，可自托管，需配合 MySQL 数据库使用。",
        "homepage": "https://mblog.kingwrcy.cn/",
        "source": "https://github.com/kingwrcy/mblog-backend",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "服务端口")],
        "envs": [
            ("MYSQL_PASS", "", "数据库密码（必填）"),
            ("MYSQL_URL", "db:3306", "数据库地址:端口"),
            ("MYSQL_DB", "mblog", "数据库名"),
            ("MBLOG_FRONT_DOMAIN", "", "前端地址"),
        ],
        "services": [
            {
                "name": "db",
                "image": "mysql:5.7",
                "volumes": [("dbdata", "/var/lib/mysql")],
                "extra_env": [
                    ("MYSQL_DATABASE", "mblog"),
                    ("MYSQL_ROOT_PASSWORD", "root123"),
                ],
            },
            {
                "name": "mblog",
                "image": "kingwrcy/mblog-backend:${VERSION}",
                "volumes": [("data", "/app/data")],
                "depends_on": ["db"],
            },
        ],
        "icon": [
            "https://cdn.jsdelivr.net/gh/kingwrcy/mblog-backend@main/doc/logo.png",
            "https://mblog.kingwrcy.cn/favicon.ico",
        ],
    },
    # ---------------- 网络 / 代理 / 工具 ----------------
    "frp": {
        "name": "frp (frps 服务端)",
        "desc": "高性能内网穿透工具的服务端，通过反向代理将内网服务安全暴露到公网，支持 TCP / UDP / HTTP / HTTPS 协议。",
        "homepage": "https://gofrp.org/",
        "source": "https://github.com/fatedier/frp",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(7000, "frps 通信端口")],
        "envs": [],
        "services": [{
            "name": "frps",
            "image": "snowdreamtech/frps:${VERSION}",
            "volumes": [("conf", "/etc/frp")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/fatedier/frp@master/doc/logo.png",
            "https://gofrp.org/img/logo.png",
        ],
    },
    "nps": {
        "name": "nps (内网穿透)",
        "desc": "轻量、高性能的内网穿透工具服务端，自带 Web 管理界面，支持 TCP / UDP / HTTP(S) / Socks5 / P2P 隧道与流量统计。",
        "homepage": "https://github.com/yisier/nps",
        "source": "https://github.com/yisier/nps",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 管理界面"), (8024, "客户端连接端口")],
        "envs": [],
        "services": [{
            "name": "nps",
            "image": "yisier1/nps:${VERSION}",
            "volumes": [("conf", "/conf")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/yisier/nps@main/doc/logo.png",
            "https://raw.githubusercontent.com/yisier/nps/main/doc/logo.png",
        ],
    },
    "rsshub": {
        "name": "RSSHub",
        "desc": "万物皆可 RSS。生成各种内容源（网站、社交平台、博客等）的 RSS 订阅，聚合你关注的一切更新。",
        "homepage": "https://docs.rsshub.app/",
        "source": "https://github.com/DIYgod/RSSHub",
        "arch": ["amd64", "arm64", "arm/v7"],
        "versions": [("latest", "最新")],
        "ports": [(1200, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "rsshub",
            "image": "diygod/rsshub:${VERSION}",
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/DIYgod/RSSHub@master/assets/logo.png",
            "https://rsshub.app/favicon-32x32.png",
        ],
    },
    "opengist": {
        "name": "Opengist",
        "desc": "自托管的代码片段分享平台，类似 GitHub Gist，支持匿名 / 登录创建片段、语法高亮与评论，基于 Git 存储。",
        "homepage": "https://opengist.io/",
        "source": "https://github.com/thomiceli/opengist",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(6157, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "opengist",
            "image": "ghcr.io/thomiceli/opengist:${VERSION}",
            "volumes": [("data", "/opengist/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/thomiceli/opengist@main/public/img/logo.png",
            "https://opengist.io/favicon.ico",
        ],
    },
    "stirling-pdf": {
        "name": "Stirling-PDF",
        "desc": "功能强大的本地 PDF 工具箱，支持合并、拆分、压缩、转换、加密、水印、OCR 等 50+ 操作，所有处理均在本地完成，保护隐私。",
        "homepage": "https://stirlingtools.com/",
        "source": "https://github.com/Stirling-Tools/Stirling-PDF",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "stirling-pdf",
            "image": "ghcr.io/stirling-tools/stirling-pdf:${VERSION}",
            "volumes": [("data", "/usr/share/tessdata"), ("logs", "/logs"), ("custom", "/configs")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/Stirling-Tools/Stirling-PDF@main/docs/logo.png",
            "https://stirlingpdf.io/logo.png",
        ],
    },
    "gitlab": {
        "name": "GitLab",
        "desc": "完整的 DevOps 生命周期平台，集成代码仓库、CI/CD、容器镜像、Issue 与 Wiki，适合团队自托管。内存占用较大，建议 4GB 以上。",
        "homepage": "https://about.gitlab.com/",
        "source": "https://gitlab.com/gitlab-org/gitlab",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(80, "HTTP"), (443, "HTTPS"), (22, "SSH")],
        "envs": [
            ("GITLAB_OMNIBUS_CONFIG", "", "自定义配置（可选）"),
            ("GITLAB_ROOT_PASSWORD", "", "root 初始密码"),
        ],
        "services": [{
            "name": "gitlab",
            "image": "gitlab/gitlab-ce:${VERSION}",
            "volumes": [("config", "/etc/gitlab"), ("logs", "/var/log/gitlab"), ("data", "/var/opt/gitlab")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/gitlabhq/gitlabhq@master/app/assets/images/gitlab_logo.svg",
            "https://about.gitlab.com/images/press/logo/svg/gitlab-logo-gray-rgb.svg",
        ],
    },
    "dockge": {
        "name": "Dockge",
        "desc": "可视化的 Docker Compose 管理面板，以 Stack 为单位管理 compose 文件，支持编辑、启动、停止、日志与终端，界面简洁美观。",
        "homepage": "https://dockge.kuma.pet/",
        "source": "https://github.com/louislam/dockge",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5001, "Web 界面")],
        "envs": [("DOCKGE_STACKS_DIR", "/opt/stacks", "Compose 文件目录")],
        "services": [{
            "name": "dockge",
            "image": "louislam/dockge:${VERSION}",
            "volumes": [("data", "/app/data"), ("stacks", "/opt/stacks"), ("socket", "/var/run/docker.sock")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/louislam/dockge@master/images/logo.png",
            "https://dockge.kuma.pet/favicon.png",
        ],
    },
    "nezha": {
        "name": "哪吒监控",
        "desc": "自托管的一站式服务器监控与运维工具，支持多端面板、实时告警、远程命令与任务管理，帮助掌握多台服务器状态。",
        "homepage": "https://nezha.wiki/",
        "source": "https://github.com/naiba/nezha",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8008, "面板界面"), (5555, "Agent 通信端口")],
        "envs": [],
        "services": [{
            "name": "nezha",
            "image": "ghcr.io/nezhahq/nezha:${VERSION}",
            "volumes": [("data", "/dashboard/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/naiba/nezha@master/resource/static/images/logo.svg",
            "https://nezha.wiki/favicon.ico",
        ],
    },
    "dbx": {
        "name": "DBX",
        "desc": "开源数据库工作台，支持 70+ 种数据库连接与 SQL 查询、数据浏览、Schema 对比、导入导出，内置 AI 助手与 MCP Server，可 Docker 自托管。",
        "homepage": "https://dbxio.com/",
        "source": "https://github.com/t8y2/dbx",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(4224, "Web 界面")],
        "envs": [("DBX_PASSWORD", "", "Web 登录密码（建议设置）")],
        "services": [{
            "name": "dbx",
            "image": "t8y2/dbx:${VERSION}",
            "volumes": [("data", "/app/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/t8y2/dbx@main/apps/desktop/src-tauri/icons/icon.png",
            "https://dl.dbxio.com/assets/dbx-logo.png",
        ],
    },
    "bettafish": {
        "name": "BettaFish (微舆)",
        "desc": "多智能体驱动的舆情分析系统，自动采集微博、小红书、抖音等平台内容，由多个 AI Agent 协作生成结构化分析报告。",
        "homepage": "https://github.com/666ghj/BettaFish",
        "source": "https://github.com/666ghj/BettaFish",
        "arch": ["amd64"],
        "versions": [("latest", "最新")],
        "ports": [(5000, "Web 界面"), (8501, "主服务")],
        "envs": [],
        "services": [{
            "name": "bettafish",
            "image": "ghcr.io/666ghj/bettafish:${VERSION}",
            "volumes": [("data", "/app/data"), ("logs", "/app/logs")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/666ghj/BettaFish@main/docs/logo.png",
            "https://raw.githubusercontent.com/666ghj/BettaFish/main/docs/logo.png",
        ],
    },
    "sub2api": {
        "name": "Sub2API",
        "desc": "把订阅账号统一转换为 API Key 的 AI API 网关，支持账号分组、负载均衡、额度统计，需配合 PostgreSQL 与 Redis 使用。",
        "homepage": "https://github.com/Wei-Shaw/sub2api",
        "source": "https://github.com/Wei-Shaw/sub2api",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8080, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "sub2api",
            "image": "weishaw/sub2api:${VERSION}",
            "volumes": [("data", "/app/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/Wei-Shaw/sub2api@main/docs/logo.png",
            "https://raw.githubusercontent.com/Wei-Shaw/sub2api/main/docs/logo.png",
        ],
    },
    "ddns-go": {
        "name": "DDNS-GO",
        "desc": "简单易用的动态域名解析工具，自动获取公网 IPv4 / IPv6 并同步到阿里云、腾讯云、Cloudflare 等 20+ DNS 服务商，带 Web 配置界面。",
        "homepage": "https://github.com/jeessy2/ddns-go",
        "source": "https://github.com/jeessy2/ddns-go",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(9876, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "ddns-go",
            "image": "jeessy/ddns-go:${VERSION}",
            "volumes": [("config", "/root")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/jeessy2/ddns-go@master/assets/logo.png",
            "https://raw.githubusercontent.com/jeessy2/ddns-go/master/assets/logo.png",
        ],
    },
    "new-api": {
        "name": "New API",
        "desc": "新一代大模型 API 网关与 AI 资产管理平台，支持多模型统一接入、令牌管理、渠道分发、用量统计与计费，可对接 OpenAI / DeepSeek 等各类模型。",
        "homepage": "https://docs.newapi.pro/",
        "source": "https://github.com/QuantumNous/new-api",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新"), ("0.13.2", "0.13.2")],
        "ports": [(3000, "Web 界面")],
        "envs": [("SESSION_SECRET", "", "会话密钥（建议设置）")],
        "services": [{
            "name": "new-api",
            "image": "calciumion/new-api:${VERSION}",
            "volumes": [("data", "/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/QuantumNous/new-api@main/web/public/logo.png",
            "https://raw.githubusercontent.com/QuantumNous/new-api/main/web/public/logo.png",
        ],
    },
    # ---------------- CI / 其它 ----------------
    "gitea-runner": {
        "name": "Gitea Act Runner",
        "desc": "Gitea Actions 的运行器，在本地或专用机器上执行 Gitea 仓库的 CI/CD 流水线。需要先在 Gitea 注册 runner 获取 token。",
        "homepage": "https://docs.gitea.com/usage/actions/act-runner",
        "source": "https://gitea.com/gitea/runner",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [],
        "envs": [("GITEA_INSTANCE_URL", "https://gitea.com", "Gitea 实例地址"), ("GITEA_RUNNER_REGISTRATION_TOKEN", "", "Runner 注册令牌（必填）")],
        "services": [{
            "name": "gitea-runner",
            "image": "gitea/act_runner:${VERSION}",
            "volumes": [("data", "/data"), ("socket", "/var/run/docker.sock")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/go-gitea/gitea@main/assets/logo.svg",
            "https://gitea.com/assets/img/logo.png",
        ],
    },
    "forgejo-runner": {
        "name": "Forgejo Runner",
        "desc": "Forgejo Actions 的运行器，在专用机器上执行 Forgejo 仓库的 CI/CD 流水线。需要先在 Forgejo 实例注册 runner 获取令牌。",
        "homepage": "https://forgejo.org/docs/latest/admin/actions/",
        "source": "https://code.forgejo.org/forgejo/runner",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [],
        "envs": [("FORGEJO_INSTANCE_URL", "", "Forgejo 实例地址（必填）"), ("FORGEJO_RUNNER_REGISTRATION_TOKEN", "", "Runner 注册令牌（必填）")],
        "services": [{
            "name": "forgejo-runner",
            "image": "code.forgejo.org/forgejo/runner:${VERSION}",
            "volumes": [("data", "/data"), ("socket", "/var/run/docker.sock")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/codeberg/Forgejo@forgejo/assets/img/logo.png",
            "https://forgejo.org/assets/img/logo.svg",
        ],
    },
    "pixivfe": {
        "name": "PixivFE",
        "desc": "开源的 pixiv 替代前端，保护隐私、无需登录即可匿名浏览，所有请求在服务端完成，轻量现代、支持多架构镜像。",
        "homepage": "https://pixivfe-docs.pages.dev/",
        "source": "https://codeberg.org/PixivFE/PixivFE",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8282, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "pixivfe",
            "image": "registry.gitlab.com/pixivfe/pixivfe:${VERSION}",
            "volumes": [("data", "/pixivfe/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/asadahimeka/PixivFE@main/assets/pixivfe-logo.svg",
            "https://raw.githubusercontent.com/asadahimeka/PixivFE/main/assets/pixivfe-logo.svg",
        ],
    },
    # 补充：不在本脚本 APPS 内、由其它方式加入的应用也需归入对应分类
    "nextcloud": {
        "name": "Nextcloud",
        "desc": "自托管的网盘与协作平台，支持文件同步、分享、在线文档、日历、联系人等，可完全掌控自己的数据。",
        "homepage": "https://nextcloud.com/",
        "source": "https://github.com/nextcloud/server",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(80, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "nextcloud",
            "image": "nextcloud:${VERSION}",
            "volumes": [("data", "/var/www/html")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/nextcloud/server@master/core/img/logo.svg",
            "https://nextcloud.com/media/Nextcloud-logo.svg",
        ],
    },
    "portainer": {
        "name": "Portainer",
        "desc": "最流行的 Docker / Kubernetes 可视化面板，提供容器、镜像、网络、卷与栈的一站式管理，界面直观、适合新手。",
        "homepage": "https://www.portainer.io/",
        "source": "https://github.com/portainer/portainer",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(9000, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "portainer",
            "image": "portainer/portainer-ce:${VERSION}",
            "volumes": [("data", "/data"), ("socket", "/var/run/docker.sock")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/portainer/portainer@develop/app/assets/images/logo.png",
            "https://www.portainer.io/hubfs/Brand%20Assets/Portainer%20Logo.svg",
        ],
    },
    "uptime-kuma": {
        "name": "Uptime Kuma",
        "desc": "自托管的网站 / 服务可用性监控工具，支持 HTTP、TCP、Ping、DNS 等多种协议，带通知告警与状态页。",
        "homepage": "https://uptime.kuma.pet/",
        "source": "https://github.com/louislam/uptime-kuma",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3001, "Web 界面")],
        "envs": [],
        "services": [{
            "name": "uptime-kuma",
            "image": "louislam/uptime-kuma:${VERSION}",
            "volumes": [("data", "/app/data")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/louislam/uptime-kuma@master/public/icon.svg",
            "https://uptime.kuma.pet/favicon.svg",
        ],
    },
    "watchtower": {
        "name": "Watchtower",
        "desc": "自动监控运行中的容器，当基础镜像发布新版本时自动拉取并重建，让自托管应用保持最新、避免错过安全更新。",
        "homepage": "https://containrrr.dev/watchtower/",
        "source": "https://github.com/containrrr/watchtower",
        "arch": ["amd64", "arm64", "arm/v7"],
        "versions": [("latest", "最新")],
        "ports": [],
        "envs": [
            ("TZ", "Asia/Shanghai", "时区"),
            ("WATCHTOWER_CLEANUP", "true", "更新后是否删除旧镜像"),
            ("WATCHTOWER_POLL_INTERVAL", "3600", "检查间隔（秒）"),
        ],
        "services": [{
            "name": "watchtower",
            "image": "containrrr/watchtower:${VERSION}",
            "volumes": [("socket", "/var/run/docker.sock")],
        }],
        "icon": [
            "https://cdn.jsdelivr.net/gh/containrrr/watchtower@main/logo.svg",
            "https://containrrr.dev/watchtower/favicon.svg",
        ],
    },
    # ---------------- 网盘 / 列表 ----------------
    "openlist": {
        "name": "OpenList",
        "desc": "AList 社区 fork 的网盘聚合与文件列表程序，支持阿里云盘、OneDrive、百度网盘、夸克、115、WebDAV 等数十种存储，带在线预览与 WebDAV 能力。",
        "homepage": "https://www.oplist.org/",
        "source": "https://github.com/OpenListTeam/OpenList",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5244, "Web 界面")],
        "envs": [("TZ", "Asia/Shanghai", "时区"), ("UMASK", "022", "文件权限掩码")],
        "services": [{
            "name": "openlist",
            "image": "openlistteam/openlist:${VERSION}",
            "volumes": [("data", "/opt/openlist/data")],
        }],
        "icon": [
            "https://raw.githubusercontent.com/OpenListTeam/OpenList/main/frontend/public/logo.svg",
            "https://doc.oplist.org/favicon.svg",
        ],
    },
    "alist": {
        "name": "AList",
        "desc": "支持多存储的文件列表与分享程序，聚合阿里云盘、百度网盘、OneDrive、夸克等主流存储，自带 Web 界面、WebDAV 与离线下载。",
        "homepage": "https://alist.nn.ci/",
        "source": "https://github.com/AlistGo/alist",
        "arch": ["amd64", "arm64"],
        "versions": [("v3.40.0", "3.40（社区推荐）"), ("latest", "最新")],
        "warn": "Alist 社区认可相对安全版本是 3.40；推荐使用新一代版本 OpenList，建议不要将其更新到更新的版本。",
        "ports": [(5244, "Web 界面")],
        "envs": [
            ("PUID", "0", "运行用户 UID"),
            ("PGID", "0", "运行用户 GID"),
            ("UMASK", "022", "文件权限掩码"),
        ],
        "services": [{
            "name": "alist",
            "image": "xhofe/alist:${VERSION}",
            "volumes": [("data", "/opt/alist/data")],
        }],
        "icon": [
            "https://raw.githubusercontent.com/AlistGo/alist/main/logo/logo.svg",
            "https://alist.nn.ci/favicon.svg",
        ],
    },
    # ---------------- 可观测 / 监控 ----------------
    "kibana": {
        "name": "Kibana",
        "desc": "Elastic 生态的数据可视化与探索平台，配合 Elasticsearch 使用，提供图表、仪表盘、日志分析与告警，是 ELK 栈的可视化入口。",
        "homepage": "https://www.elastic.co/kibana/",
        "source": "https://github.com/elastic/kibana",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5601, "Web 界面")],
        "envs": [("ELASTICSEARCH_HOSTS", "http://localhost:9200", "Elasticsearch 地址（可填服务名，如 http://elasticsearch:9200）")],
        "services": [{
            "name": "kibana",
            "image": "docker.elastic.co/kibana/kibana:${VERSION}",
            "volumes": [("data", "/usr/share/kibana/data")],
        }],
        "icon": [
            "https://www.vectorlogo.zone/logos/elasticco_kibana/elasticco_kibana-icon.svg",
            "https://www.elastic.co/static-res/images/elk-loading.gif",
        ],
    },
    "umami": {
        "name": "Umami",
        "desc": "开源、注重隐私的网站访问统计分析工具，轻量且现代，支持多站点、事件跟踪与自定义图表，数据完全自有。本模板内置 PostgreSQL 数据库。",
        "homepage": "https://umami.is/",
        "source": "https://github.com/umami-software/umami",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(3000, "Web 界面")],
        "envs": [("HASH_SALT", "change-me", "数据加密盐值（首次部署请修改）")],
        "services": [
            {
                "name": "db",
                "image": "postgres:16-alpine",
                "volumes": [("pgdata", "/var/lib/postgresql/data")],
                "extra_env": [
                    ("POSTGRES_DB", "umami"),
                    ("POSTGRES_USER", "umami"),
                    ("POSTGRES_PASSWORD", "umami"),
                ],
            },
            {
                "name": "umami",
                "image": "ghcr.io/umami-software/umami:${VERSION}",
                "extra_env": [
                    ("DATABASE_URL", "postgresql://umami:umami@db:5432/umami"),
                    ("DATABASE_TYPE", "postgresql"),
                ],
                "depends_on": ["db"],
            },
        ],
        "icon": [
            "https://raw.githubusercontent.com/umami-software/umami/master/logo.svg",
            "https://umami.is/favicon.ico",
        ],
    },
    "zabbix": {
        "name": "Zabbix",
        "desc": "企业级开源监控解决方案，支持主机、网络、应用、数据库等监控与多渠道告警，自带可视化仪表盘。本模板内置 PostgreSQL 数据库，Web 端口 8080。",
        "homepage": "https://www.zabbix.com/",
        "source": "https://github.com/zabbix/zabbix",
        "arch": ["amd64"],
        "versions": [("7.0-latest", "7.0 LTS")],
        "ports": [(8080, "Web 界面")],
        "envs": [],
        "services": [
            {
                "name": "db",
                "image": "postgres:16-alpine",
                "volumes": [("pgdata", "/var/lib/postgresql/data")],
                "extra_env": [
                    ("POSTGRES_DB", "zabbix"),
                    ("POSTGRES_USER", "zabbix"),
                    ("POSTGRES_PASSWORD", "zabbix"),
                ],
            },
            {
                "name": "zabbix-server",
                "image": "zabbix/zabbix-server-pgsql:alpine-${VERSION}",
                "volumes": [("serverdata", "/var/lib/zabbix")],
                "extra_env": [
                    ("DB_SERVER_HOST", "db"),
                    ("POSTGRES_USER", "zabbix"),
                    ("POSTGRES_PASSWORD", "zabbix"),
                    ("ZBX_HOSTNAME", "zabbix-server"),
                ],
                "depends_on": ["db"],
            },
            {
                "name": "zabbix-web",
                "image": "zabbix/zabbix-web-nginx-pgsql:alpine-${VERSION}",
                "map_ports": True,  # Web 界面所在，主服务映射端口
                "extra_env": [
                    ("DB_SERVER_HOST", "db"),
                    ("POSTGRES_USER", "zabbix"),
                    ("POSTGRES_PASSWORD", "zabbix"),
                    ("ZBX_SERVER_HOST", "zabbix-server"),
                    ("PHP_TZ", "Asia/Shanghai"),
                ],
                "depends_on": ["db", "zabbix-server"],
            },
        ],
        "icon": [
            "https://raw.githubusercontent.com/zabbix/zabbix/master/ui/app/images/zabbix.png",
            "https://www.zabbix.com/themes/2016/images/logo.png",
        ],
    },
    # ---------------- 基础设施 / 开发 ----------------
    "consul": {
        "name": "Consul",
        "desc": "HashiCorp 的服务发现与配置中心，提供服务网格、KV 存储与健康检查，支持多数据中心。本模板以 dev 单机模式运行并开放 Web UI。",
        "homepage": "https://www.consul.io/",
        "source": "https://github.com/hashicorp/consul",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(8500, "Web UI"), (8600, "DNS 接口")],
        "envs": [],
        "services": [{
            "name": "consul",
            "image": "hashicorp/consul:${VERSION}",
            "volumes": [("data", "/consul/data")],
            "command": "agent -dev -client=0.0.0.0 -ui -bind=0.0.0.0",
        }],
        "icon": [
            "https://www.vectorlogo.zone/logos/consul/consul-icon.svg",
            "https://www.consul.io/favicon.ico",
        ],
    },
    # ---------------- frp 客户端 ----------------
    "frpc": {
        "name": "frp (frpc 客户端)",
        "desc": "高性能内网穿透工具的客户端，主动连接 frps 服务端，将本机内网服务暴露到公网。连接参数以环境变量配置，隧道规则可挂载 /etc/frp 下的 frpc.toml。",
        "homepage": "https://gofrp.org/",
        "source": "https://github.com/fatedier/frp",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [],
        "envs": [
            ("FRP_SERVER_ADDR", "", "frps 服务端地址（必填，如 1.2.3.4）"),
            ("FRP_SERVER_PORT", "7000", "frps 服务端端口"),
            ("FRP_AUTH_METHOD", "token", "认证方式（token / user 等）"),
            ("FRP_TOKEN", "", "认证 token（需与 frps 配置一致）"),
            ("FRP_SERVER_USER", "", "认证用户名（可选）"),
            ("FRP_SERVER_PASSWORD", "", "认证密码（可选）"),
        ],
        "services": [{
            "name": "frpc",
            "image": "snowdreamtech/frpc:${VERSION}",
            "volumes": [("conf", "/etc/frp")],
        }],
        "icon": [
            "https://gofrp.org/img/logo.png",
        ],
    },
    # ---------------- Pixiv 工具 ----------------
    "pppixiv": {
        "name": "pppixiv",
        "desc": "Pixiv 插画批量下载工具，自带 Web 管理界面（/dashboard），输入画师 UID 即可一键批量下载其全部插画并支持预览。需配置 Pixiv 账号密码，国内访问 Pixiv 需代理。",
        "homepage": "https://github.com/MGMCN/pppixiv",
        "source": "https://github.com/MGMCN/pppixiv",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [(5000, "Web 管理界面")],
        "envs": [
            ("username", "", "Pixiv 账号（必填）"),
            ("password", "", "Pixiv 密码（必填）"),
            ("port", "5000", "服务端口"),
        ],
        "services": [{
            "name": "pppixiv",
            "image": "godmountain/pppixiv:${VERSION}",
            "volumes": [("Illusts", "/APP/Illusts")],
        }],
        "icon": [
            "https://www.google.com/s2/favicons?domain=github.com/MGMCN/pppixiv&sz=256",
        ],
    },
    "pixivd": {
        "name": "PixivD",
        "desc": "Pixiv 命令行批量下载工具（官方 ghcr 镜像），支持按画师 ID、每日/历史排行榜批量下载插画。容器以保活方式运行，安装后在容器终端执行 pixivd 命令（如 pixivd <UID> 或 pixivd -r），下载结果保存在 illustrations 目录。",
        "homepage": "https://github.com/bebound/pixivd",
        "source": "https://github.com/bebound/pixivd",
        "arch": ["amd64", "arm64"],
        "versions": [("latest", "最新")],
        "ports": [],
        "envs": [],
        "services": [{
            "name": "pixivd",
            "image": "ghcr.io/bebound/pixivd:${VERSION}",
            "volumes": [("illustrations", "/app/illustrations"), ("config", "/.config/pixivd")],
            # 官方镜像入口为 pixivd CLI，此处覆盖为保活，安装后在容器终端手动执行下载命令
            "entrypoint": ["/bin/sh", "-c", "sleep infinity"],
        }],
        "icon": [
            "https://www.google.com/s2/favicons?domain=github.com/bebound/pixivd&sz=256",
        ],
    },
}

# 应用分类（app_id -> 分类名），写入 data.yml 供应用商店按分类筛选
CATEGORY = {
    # 数据库 / 存储
    "mysql": "数据库/存储", "redis": "数据库/存储", "postgres": "数据库/存储",
    "mariadb": "数据库/存储", "nocodb": "数据库/存储", "verdaccio": "数据库/存储",
    "sftpgo": "数据库/存储",
    # 面板 / 网站
    "wordpress": "面板/网站", "gitea": "面板/网站", "halo": "面板/网站",
    "outline": "面板/网站", "flarum": "面板/网站", "tailchat": "面板/网站",
    "excalidraw": "面板/网站", "it-tools": "面板/网站", "qinglong": "面板/网站",
    "sun-panel": "面板/网站", "nextcloud": "面板/网站",
    # AI / 开发
    "open-webui": "AI/开发", "n8n": "AI/开发", "one-api": "AI/开发",
    "astrbot": "AI/开发", "llama-cpp": "AI/开发", "code-server": "AI/开发",
    "node-red": "AI/开发", "jupyter-notebook": "AI/开发", "deepseek-harness": "AI/开发",
    "hermes-agent": "AI/开发", "mblog-backend": "AI/开发",
    # 网络 / 工具
    "frp": "网络/工具", "nps": "网络/工具", "rsshub": "网络/工具",
    "opengist": "网络/工具", "stirling-pdf": "网络/工具", "pixivfe": "网络/工具",
    "ddns-go": "网络/工具", "sub2api": "网络/工具", "frpc": "网络/工具",
    "pppixiv": "网络/工具", "pixivd": "网络/工具",
    # 监控 / 运维
    "uptime-kuma": "监控/运维", "watchtower": "监控/运维", "portainer": "监控/运维",
    "nezha": "监控/运维", "kibana": "监控/运维", "umami": "监控/运维",
    "zabbix": "监控/运维",
    # 开发 / DevOps
    "gitlab": "开发/DevOps", "dockge": "开发/DevOps", "dbx": "开发/DevOps",
    "bettafish": "开发/DevOps", "new-api": "开发/DevOps",
    "gitea-runner": "开发/DevOps", "forgejo-runner": "开发/DevOps",
    "consul": "开发/DevOps",
    # 面板 / 网站（网盘 / 列表）
    "openlist": "面板/网站", "alist": "面板/网站",
}


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def gen_compose(app_id: str, meta: dict) -> str:
    services = meta["services"]
    lines = ["# " + meta["name"], "# ${VERSION} 占位符由面板在安装时替换", 'version: "3"', "", "services:"]
    # 主服务 = 显式声明 map_ports 的服务（Web 界面所在）；否则第一个使用 ${VERSION} 镜像的服务（应用本体）。
    # 只有主服务映射声明的端口，其余配套服务（db/redis/zabbix-server 等）不映射，避免端口冲突。
    primary_idx = next(
        (i for i, s in enumerate(services) if s.get("map_ports")),
        next((i for i, s in enumerate(services) if "${VERSION}" in s["image"]), -1),
    )
    for idx, svc in enumerate(services):
        name = svc["name"]
        is_primary = idx == primary_idx
        lines.append(f"  {name}:")
        lines.append(f"    image: {svc['image']}")
        lines.append(f"    container_name: {name}")
        volumes = svc.get("volumes") or []
        if volumes:
            lines.append("    volumes:")
            for host_sub, cont in volumes:
                lines.append(f"      - ./{host_sub}:{cont}")
        # 端口：主服务暴露声明端口，其它服务仅其额外端口
        ports = []
        if is_primary:
            ports.extend((c, c) for c, _l in meta["ports"])
        ports.extend(svc.get("extra_ports") or [])
        if ports:
            lines.append("    ports:")
            for hp, cp in ports:
                lines.append(f'      - "{hp}:{cp}"')
        envs = list(svc.get("extra_env") or [])
        if is_primary:
            for env_name, default, _desc in meta["envs"]:
                envs.append((env_name, default))
        if envs:
            lines.append("    environment:")
            for k, v in envs:
                if v == "":
                    lines.append(f"      - {k}=${{{k}}}")
                else:
                    lines.append(f"      - {k}={v}")
        depends = svc.get("depends_on")
        if depends:
            lines.append("    depends_on:")
            for d in depends:
                lines.append(f"      - {d}")
        # 覆盖容器入口 / 启动命令（可选）
        entrypoint = svc.get("entrypoint")
        if entrypoint:
            if isinstance(entrypoint, list):
                import json
                lines.append("    entrypoint: " + json.dumps(entrypoint))
            else:
                lines.append(f'    entrypoint: ["{entrypoint}"]')
        command = svc.get("command")
        if command:
            if isinstance(command, list):
                import json
                lines.append("    command: " + json.dumps(command))
            else:
                lines.append(f"    command: {command}")
        lines.append("    restart: unless-stopped")
    return "\n".join(lines) + "\n"


def gen_data(app_id: str, meta: dict) -> str:
    versions = "".join(
        f"  - {{ tag: \"{t}\", label: \"{l}\" }}\n" for t, l in meta["versions"]
    )
    ports = "".join(f"  - {{ container: {c}, label: \"{l}\", protocol: \"tcp\" }}\n" for c, l in meta["ports"])
    envs = "".join(
        f"  - {{ name: \"{n}\", default: \"{d}\", desc: \"{desc}\" }}\n"
        for n, d, desc in meta["envs"]
    )
    # 安装警告（可选）：有 warn 时写入 data.yml，前端安装弹窗会展示
    warn_line = f'\nwarn: "{meta["warn"]}"\n' if meta.get("warn") else ""
    return f"""# ============================================================
# Graw 社区应用商店 - 应用元数据 data.yml
# ============================================================

name: "{meta['name']}"
id: "{app_id}"

category: "{CATEGORY.get(app_id, '其它')}"
{warn_line}description: >
  {meta['desc']}

homepage: "{meta['homepage']}"

source: "{meta['source']}"

arch:
{''.join(f'  - "{a}"\n' for a in meta['arch'])}versions:
{versions}
ports:
{ports}
env:
{envs}
"""


def main():
    from urllib.request import Request, urlopen

    import os
    skip_icons = os.environ.get("SKIP_ICONS") == "1"
    created = 0
    icons_ok = 0
    icons_fail = []
    for app_id, meta in APPS.items():
        app_dir = os.path.join(APPS_DIR, app_id)
        os.makedirs(app_dir, exist_ok=True)
        # 1) compose
        _write(os.path.join(app_dir, "docker-compose.yml"), gen_compose(app_id, meta))
        # 2) data.yml
        _write(os.path.join(app_dir, "data.yml"), gen_data(app_id, meta))
        created += 1
        if skip_icons:
            continue
        # 3) icon
        saved = False
        icon_candidates = list(meta.get("icon") or [])
        # 兜底：官网 favicon（Google 服务通常可达）
        from urllib.parse import urlparse
        domain = urlparse(meta["homepage"]).netloc
        icon_candidates.append(
            f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
        )
        for url in icon_candidates:
            try:
                req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
                data = urlopen(req, timeout=25).read()
                if len(data) < 100:
                    continue
                ext = ".png"
                if data.lstrip().startswith(b"<svg") or b"<svg" in data[:300]:
                    ext = ".svg"
                target = os.path.join(app_dir, "icon" + ext)
                if ext == ".svg":
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(data.decode("utf-8", "replace"))
                else:
                    with open(target, "wb") as f:
                        f.write(data)
                icons_ok += 1
                saved = True
                print(f"  [icon] {app_id} <- {url[:70]} ({len(data)}B)")
                break
            except Exception as e:
                print(f"  [icon] {app_id} FAIL {url[:60]}: {type(e).__name__}")
        if not saved:
            icons_fail.append(app_id)

    print(f"\n生成完成: {created} 个应用")
    print(f"图标成功: {icons_ok}，失败: {len(icons_fail)}")
    if icons_fail:
        print("图标失败列表:", ", ".join(icons_fail))


if __name__ == "__main__":
    main()
