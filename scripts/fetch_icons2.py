# -*- coding: utf-8 -*-
"""为缺失图标的应用，通过 GitHub API 查找仓库内真实 logo 文件并从 jsDelivr 下载；
非 GitHub 仓库回退官网 favicon。"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_add_apps as m

APPS_DIR = m.APPS_DIR

UA = {"User-Agent": "Mozilla/5.0"}


def _get(url, timeout=25, binary=False):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data


def _github_repo(source):
    u = urlparse(source)
    if u.netloc not in ("github.com", "www.github.com"):
        return None
    parts = [p for p in u.path.split("/") if p]
    return (parts[0], parts[1]) if len(parts) >= 2 else None


def _find_logo_paths(owner, repo):
    """通过 GitHub API 获取文件树，返回候选 logo/icon 路径。"""
    for branch in ("main", "master", "develop", "dev"):
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            data = json.loads(_get(url).decode("utf-8"))
            tree = data.get("tree", [])
            if not tree:
                continue
            hits = []
            for item in tree:
                p = item.get("path", "")
                low = p.lower()
                # 只保留 logo / icon / favicon 相关图片文件
                if not any(x in low for x in ("logo", "icon", "favicon", "brand", "banner")):
                    continue
                if not low.endswith((".png", ".svg", ".jpg", ".jpeg", ".ico", ".webp")):
                    continue
                # 排除过大的截图 / 文档示例
                if any(x in low for x in ("screenshot", "example", "demo", "test", "docs/", "/images/blog")):
                    continue
                if len(p) < 120:
                    hits.append(p)
            if hits:
                return hits
        except Exception:
            continue
    return []


def fetch(app_id):
    meta = m.APPS[app_id]
    app_dir = os.path.join(APPS_DIR, app_id)
    os.makedirs(app_dir, exist_ok=True)
    if os.path.exists(os.path.join(app_dir, "icon.png")) or os.path.exists(os.path.join(app_dir, "icon.svg")):
        return app_id, "exists"

    repo = _github_repo(meta["source"])
    candidates = []

    # 1) GitHub 仓库内 logo 路径
    if repo:
        owner, repo_name = repo
        paths = _find_logo_paths(owner, repo_name)
        # 优先级：icon / logo 单文件优先，避免挑到文档图
        ordered = sorted(paths, key=lambda p: (0 if "icon" in p.lower() else 1, len(p)))
        for p in ordered[:6]:
            candidates.append(f"https://cdn.jsdelivr.net/gh/{owner}/{repo_name}@main/{p}")
            candidates.append(f"https://cdn.jsdelivr.net/gh/{owner}/{repo_name}@master/{p}")

    # 2) 官网 favicon
    domain = urlparse(meta["homepage"]).netloc
    candidates.append(f"https://{domain}/favicon.ico")
    candidates.append(f"https://{domain}/favicon.png")
    candidates.append(f"https://www.google.com/s2/favicons?domain={domain}&sz=256")

    for url in candidates:
        try:
            data = _get(url)
            if len(data) < 100:
                continue
            ext = ".svg" if (data.lstrip().startswith(b"<svg") or b"<svg" in data[:300]) else ".png"
            target = os.path.join(app_dir, "icon" + ext)
            if ext == ".svg":
                with open(target, "w", encoding="utf-8") as f:
                    f.write(data.decode("utf-8", "replace"))
            else:
                with open(target, "wb") as f:
                    f.write(data)
            return app_id, f"OK {len(data)}B <- {url.split('?')[0][:70]}"
        except Exception:
            continue
    return app_id, "FAIL"


def main():
    missing = [a for a in m.APPS
               if not os.path.exists(os.path.join(APPS_DIR, a, "icon.png"))
               and not os.path.exists(os.path.join(APPS_DIR, a, "icon.svg"))]
    print(f"待下载: {len(missing)}")
    results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for app_id, msg in ex.map(fetch, missing):
            results[app_id] = msg
    for a in missing:
        print(f"{a}: {results[a]}")
    ok = [a for a in missing if results[a].startswith("OK")]
    fail = [a for a in missing if results[a].startswith("FAIL")]
    print(f"\n成功 {len(ok)}/{len(missing)}，失败 {len(fail)}")
    if fail:
        print("失败:", ", ".join(fail))


if __name__ == "__main__":
    main()
