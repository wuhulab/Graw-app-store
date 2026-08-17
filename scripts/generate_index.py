#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_index.py - 扫描 apps/ 下的所有应用，生成统一索引 index.json

说明:
    本脚本位于「app-store 独立仓库」内，仓库根目录即本目录的上一级
    （apps/、index.json 都以仓库根为基准，CI 工作流见 .github/workflows/app-store.yml）。

用法（本地，在 app-store 目录内执行）:
    GRAW_STORE_REPO=<owner>/<repo> python scripts/generate_index.py

用法（GitHub Actions，见 .github/workflows/app-store.yml）:
    由 CI 注入 GITHUB_REPOSITORY 环境变量后执行。

输出:
    index.json
    顶层结构:
      {
        "store": { "name", "repo", "base_url", "updated_at", "app_count" },
        "apps": [ { id, name, description, version, versions, homepage, source,
                    arch, ports, env, icon, compose_url, data_url } ]
      }

说明:
    - 每个应用目录必须包含 data.yml 与 docker-compose.yml（可指定文件名）。
    - icon.png 缺失时仅告警，不中断生成。
    - 所有 download_url 基于 gh-pages 分支的 raw 链接:
        https://raw.githubusercontent.com/<repo>/gh-pages/<path>
    - 优先使用 PyYAML 解析 data.yml；不可用时回退到内置的极简解析器
      （仅覆盖本商店约定的 data.yml 子集，建议在 CI 中安装 PyYAML）。
"""
import json
import os
import re
import sys
import datetime

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover - CI 会安装 PyYAML
    yaml = None

APP_STORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(APP_STORE_DIR, "apps")
INDEX_PATH = os.path.join(APP_STORE_DIR, "index.json")

# 需要置底的应用（排到列表末尾）：如 alist 有社区版本建议，不宜置顶
_LAST_APPS = {"alist"}


def _entry_sort_key(name: str):
    """排序 key：需要置底的应用排最后，其余按名称字母序。"""
    return (name in _LAST_APPS, name)


# ------------------------------------------------------------
# 内置极简 YAML 子集解析器（PyYAML 不可用时兜底）
# 仅支持: 顶层/嵌套映射、带引号或不带引号的标量、> 块状描述、"- item" 列表、
#         "- { k: v, ... }" 内联映射列表项。
# ------------------------------------------------------------
def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_inline_map(s: str) -> dict:
    """解析 "{ tag: 1, label: 最新 }" 形式的行内映射。"""
    result = {}
    s = s.strip()
    if s.startswith("{"):
        s = s[1:]
    if s.endswith("}"):
        s = s[:-1]
    for part in s.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        key, _, val = part.partition(":")
        result[key.strip()] = _parse_scalar(val)
    return result


def _parse_scalar(s: str):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return _parse_inline_map(s)
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x) for x in inner.split(",")]
    s = _strip_quotes(s)
    if s in ("null", "Null", "NULL", "~", ""):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    # 数值
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _min_yaml(text: str) -> dict:
    """极简 YAML 解析，返回嵌套 dict。"""
    lines = text.splitlines()
    root = {}
    # (缩进, 父容器, key 或 None(列表项)) 栈
    stack = []  # type: list[tuple[int, dict, str]]
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw.strip()
        # 列表项 "- xxx"
        if content.startswith("- "):
            item = content[2:].strip()
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if not stack:
                raise ValueError(f"无法解析的列表项: {raw}")
            parent = stack[-1][1]
            key = stack[-1][2]
            lst = parent.setdefault(key, [])
            if item.startswith("{") or ":" in item:
                lst.append(_parse_inline_map(item))
            else:
                lst.append(_parse_scalar(item))
            i += 1
            continue
        # 普通键值
        if ":" not in content:
            raise ValueError(f"无法解析的行: {raw}")
        key, _, val = content.partition(":")
        key = key.strip()
        val = val.strip()
        # 弹栈到当前缩进层级
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            container = root
        else:
            container = stack[-1][1].setdefault(stack[-1][2], {})
            # 若父级目标是列表，则容器为列表的最后一个元素
            if isinstance(container, list):
                if not container:
                    container = {}
                else:
                    container = container[-1]
            if not isinstance(container, dict):
                raise ValueError(f"无法解析: {raw}")
        if val in (">", "|"):
            # 块状文本
            block = []
            j = i + 1
            while j < n:
                nxt = lines[j]
                if not nxt.strip():
                    block.append("")
                    j += 1
                    continue
                nindent = len(nxt) - len(nxt.lstrip(" "))
                if nindent <= indent:
                    break
                block.append(nxt.strip())
                j += 1
            container[key] = "\n".join(block).strip()
            i = j
        elif val == "":
            container[key] = {}
            stack.append((indent, container, key))
            i += 1
        else:
            container[key] = _parse_scalar(val)
            i += 1
    return root


def load_yml(path: str) -> dict:
    """读取 YAML 文件，优先 PyYAML，失败时回退内置解析器。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if yaml is not None:
        try:
            data = yaml.safe_load(text) or {}
            return data if isinstance(data, dict) else {"_raw": data}
        except Exception:
            pass
    return _min_yaml(text)


def _resolve_repo() -> str:
    """确定仓库 owner/name（用于生成 gh-pages raw 链接）。"""
    repo = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GRAW_STORE_REPO")
    if repo:
        return repo.strip("/")
    # 本地回退：尝试从 git remote 推导
    try:
        import subprocess
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        m = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?$", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    # 兜底占位：请替换为 app-store 独立仓库的实际地址（如 <owner>/<repo>）。
    # CI 中会由 GITHUB_REPOSITORY 注入覆盖，此处仅影响本地无环境变量时的演示输出。
    return "<owner>/<repo>"


def _file_url(repo: str, rel: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/gh-pages/{rel.lstrip('/')}"


def collect_apps(repo: str):
    """扫描 apps/ 目录，返回 (apps 列表, warnings 列表)。"""
    apps = []
    warnings = []
    if not os.path.isdir(APPS_DIR):
        warnings.append(f"apps 目录不存在: {APPS_DIR}")
        return apps, warnings

    for entry in sorted(os.listdir(APPS_DIR), key=_entry_sort_key):
        app_dir = os.path.join(APPS_DIR, entry)
        if not os.path.isdir(app_dir) or entry.startswith("."):
            continue
        # data.yml 必须存在
        data_path = os.path.join(app_dir, "data.yml")
        if not os.path.isfile(data_path):
            warnings.append(f"[{entry}] 缺少 data.yml，已跳过")
            continue
        try:
            meta = load_yml(data_path)
        except Exception as e:
            warnings.append(f"[{entry}] data.yml 解析失败: {e}")
            continue

        app_id = str(meta.get("id") or entry)
        name = str(meta.get("name") or entry)
        if not meta.get("name") or not meta.get("description"):
            warnings.append(f"[{entry}] data.yml 缺少 name 或 description")

        compose_file = str(meta.get("compose") or "docker-compose.yml")
        compose_path = os.path.join(app_dir, compose_file)
        if not os.path.isfile(compose_path):
            warnings.append(f"[{entry}] 缺少 {compose_file}，已跳过")
            continue

        icon_rel = f"apps/{app_id}/icon.png"
        icon_found = os.path.isfile(os.path.join(app_dir, "icon.png"))
        if not icon_found:
            icon_rel = f"apps/{app_id}/icon.svg"
            icon_found = os.path.isfile(os.path.join(app_dir, "icon.svg"))
        if not icon_found:
            warnings.append(f"[{entry}] 缺少 icon.png / icon.svg")

        versions = meta.get("versions") or []
        if not versions:
            versions = [{"tag": "latest", "label": "最新"}]
        default_version = versions[0].get("tag", "latest") if isinstance(versions[0], dict) else str(versions[0])

        apps.append({
            "id": app_id,
            "name": name,
            "description": str(meta.get("description") or "").strip(),
            "category": str(meta.get("category") or ""),
            "warn": str(meta.get("warn") or ""),
            "tags": meta.get("tags") or [],
            "version": str(default_version),
            "versions": versions,
            "homepage": str(meta.get("homepage") or ""),
            "source": str(meta.get("source") or ""),
            "arch": meta.get("arch") or [],
            "ports": meta.get("ports") or [],
            "env": meta.get("env") or [],
            "icon": _file_url(repo, icon_rel),
            "compose_url": _file_url(repo, f"apps/{app_id}/{compose_file}"),
            "data_url": _file_url(repo, f"apps/{app_id}/data.yml"),
        })
    return apps, warnings


def main() -> int:
    repo = _resolve_repo()
    apps, warnings = collect_apps(repo)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    index = {
        "store": {
            "name": "Graw Community App Store",
            "repo": repo,
            "base_url": f"https://raw.githubusercontent.com/{repo}/gh-pages/",
            "updated_at": now,
            "app_count": len(apps),
        },
        "apps": apps,
    }

    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"[app-store] 仓库: {repo}")
    print(f"[app-store] 应用数量: {len(apps)}")
    for a in apps:
        print(f"  - {a['id']} ({a['name']}) v{a['version']}")
    for w in warnings:
        print(f"[warn] {w}")
    print(f"[app-store] 已写入: {INDEX_PATH}")
    return 0 if apps else 1


if __name__ == "__main__":
    sys.exit(main())
