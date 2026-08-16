# -*- coding: utf-8 -*-
"""为缺失/错误图标的应用，通过 GitHub API 精确找出合适的 logo 文件并下载。"""
import json
import os
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_add_apps as m

APPS_DIR = m.APPS_DIR
UA = {"User-Agent": "Mozilla/5.0"}

# 需要重新获取的应用 -> GitHub (owner, repo, 分支)
TARGETS = {
    "mysql": ("mysql", "mysql-docker", "main"),
    "qinglong": ("whyour", "qinglong", "develop"),
    "deepseek-harness": ("deepseek-ai", "deepseek-harness", "master"),
    "mblog-backend": ("kingwrcy", "mblog-backend", "main"),
    "gitlab": ("gitlabhq", "gitlabhq", "master"),
    "redis": ("redis", "redis", "unstable"),
    "bettafish": ("666ghj", "BettaFish", "main"),
    "sun-panel": ("hslr-s", "sun-panel", "master"),
    "halo": ("halo-dev", "halo", "main"),
    "nps": ("yisier", "nps", "master"),
    "one-api": ("songquanpeng", "one-api", "main"),
    "dbx": ("t8y2", "dbx", "main"),
}


def _get(url, t=25):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=t) as r:
        return r.read()


def list_tree(owner, repo, branch):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    try:
        data = json.loads(_get(url, 30).decode("utf-8"))
    except Exception:
        return []
    out = []
    for it in data.get("tree", []):
        p = it.get("path", "")
        low = p.lower()
        if low.endswith((".png", ".svg", ".jpg", ".jpeg", ".webp", ".ico")):
            # 只要单个 logo/icon 文件，且路径简短、非截图
            if any(k in low for k in ("logo", "icon", "favicon", "brand", "avatar", "mark")):
                if not any(bad in low for bad in ("screenshot", "banner", "hero", "social", "og-", "apple", "android", "blog", "icon-192", "icon-512", "mask-icon", "mstile", "favicon-16", "favicon-32", "docs")):
                    out.append(p)
    return out


def pick_path(app_id, paths):
    """挑最合适的图标路径。"""
    if not paths:
        return None
    # 关键词优先级
    keys = ("logo", "icon", "favicon", "brand", "mark", "avatar")
    scored = []
    for p in paths:
        low = p.lower()
        score = 0
        if "logo" in low:
            score += 10
        if low.endswith(".svg"):
            score += 5
        if "favicon" in low:
            score += 3
        if len(p) < 80:
            score += 2
        scored.append((score, len(p), p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]


def fetch(app_id):
    owner, repo, branch = TARGETS[app_id]
    app_dir = os.path.join(APPS_DIR, app_id)
    os.makedirs(app_dir, exist_ok=True)
    # 清掉旧的
    for fn in os.listdir(app_dir):
        if fn.startswith("icon"):
            os.remove(os.path.join(app_dir, fn))
    try:
        paths = list_tree(owner, repo, branch)
    except Exception as e:
        return app_id, f"TREE-ERR {type(e).__name__}"
    if not paths:
        return app_id, "NO-LOGO-PATH"
    chosen = pick_path(app_id, paths)
    for br in (branch, "main", "master", "develop"):
        url = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{br}/{chosen}"
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
            return app_id, f"OK {len(data)}B {ext} <- {chosen[:60]}"
        except Exception:
            continue
    return app_id, f"DL-FAIL ({chosen[:60]})"


def main():
    for app_id in TARGETS:
        print(fetch(app_id))


if __name__ == "__main__":
    main()
