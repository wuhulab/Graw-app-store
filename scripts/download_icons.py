# -*- coding: utf-8 -*-
"""并发下载所有应用的官方图标。
优先使用官方仓库内的图标 URL，失败则回退官网 favicon。
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_add_apps as m

APPS_DIR = m.APPS_DIR

# 应用 -> 官方图标 URL 候选（按优先级）
ICON_URLS = {
    "mysql": ["https://www.mysql.com/common/logos/logo-mysql-170x115.png"],
    "redis": ["https://redis.io/wp-content/uploads/2024/04/Redis_Logo_Icon_Colour.svg"],
    "postgres": ["https://www.postgresql.org/media/img/about/press/elephant.png"],
    "mariadb": ["https://mariadb.org/wp-content/uploads/2022/05/MariaDB_Logo_RGB-01-1.png"],
    "nocodb": ["https://www.nocodb.com/favicon.ico"],
    "verdaccio": ["https://verdaccio.org/assets/logo/verdaccio_logo.svg"],
    "sftpgo": ["https://raw.githubusercontent.com/drakkan/sftpgo/master/docs/assets/logo.png"],
    "wordpress": ["https://s.w.org/images/wmark.png"],
    "gitea": ["https://gitea.com/assets/img/logo.png"],
    "halo": ["https://halo.run/logo.svg"],
    "outline": ["https://www.getoutline.com/favicon.svg"],
    "flarum": ["https://flarum.org/assets/img/logo.png"],
    "tailchat": ["https://raw.githubusercontent.com/msgbyte/tailchat/master/website/static/img/logo.svg"],
    "excalidraw": ["https://excalidraw.com/og-image.png"],
    "it-tools": ["https://it-tools.tech/android-chrome-512x512.png"],
    "qinglong": ["https://raw.githubusercontent.com/whyour/qinglong/develop/public/static/favicon.svg"],
    "sun-panel": ["https://raw.githubusercontent.com/hslr-s/sun-panel/master/doc/img/logo.png"],
    "open-webui": ["https://openwebui.com/favicon-32x32.png"],
    "n8n": ["https://n8n.io/favicon-32x32.png"],
    "one-api": ["https://raw.githubusercontent.com/songquanpeng/one-api/main/web/src/assets/logo.svg"],
    "astrbot": ["https://raw.githubusercontent.com/AstrBotDevs/AstrBot/main/docs/images/logo.png"],
    "llama-cpp": ["https://raw.githubusercontent.com/ggml-org/llama.cpp/master/logo.png"],
    "code-server": ["https://coder.com/logo.svg"],
    "node-red": ["https://nodered.org/about/resources/media/node-red-hexagon.svg"],
    "jupyter-notebook": ["https://jupyter.org/assets/homepage/main-logo.svg"],
    "deepseek-harness": ["https://deepseek-harness.github.io/deepseek-harness/favicon.ico"],
    "hermes-agent": ["https://hermes-agent.nousresearch.com/favicon.svg"],
    "mblog-backend": ["https://mblog.kingwrcy.cn/favicon.ico"],
    "frp": ["https://gofrp.org/img/logo.png"],
    "nps": ["https://raw.githubusercontent.com/yisier/nps/main/web/static/img/logo.png"],
    "rsshub": ["https://rsshub.app/favicon-32x32.png"],
    "opengist": ["https://opengist.io/favicon.ico"],
    "stirling-pdf": ["https://stirlingpdf.io/logo.png"],
    "gitlab": ["https://about.gitlab.com/images/press/logo/svg/gitlab-logo-gray-rgb.svg"],
    "dockge": ["https://raw.githubusercontent.com/louislam/dockge/master/images/logo.png"],
    "nezha": ["https://raw.githubusercontent.com/naiba/nezha/master/resource/static/images/logo.svg"],
    "dbx": ["https://dl.dbxio.com/assets/dbx-logo.png"],
    "bettafish": ["https://raw.githubusercontent.com/666ghj/BettaFish/main/docs/logo.png"],
    "sub2api": ["https://raw.githubusercontent.com/Wei-Shaw/sub2api/main/docs/logo.png"],
    "ddns-go": ["https://raw.githubusercontent.com/jeessy2/ddns-go/master/assets/logo.png"],
    "new-api": ["https://raw.githubusercontent.com/QuantumNous/new-api/main/web/public/logo.png"],
    "gitea-runner": ["https://gitea.com/assets/img/logo.png"],
    "forgejo-runner": ["https://forgejo.org/assets/img/logo.svg"],
    "pixivfe": ["https://raw.githubusercontent.com/asadahimeka/PixivFE/main/assets/pixivfe-logo.svg"],
    # 已有图标的 4 个旧应用无需下载
}


def fetch_icon(app_id):
    app_dir = os.path.join(APPS_DIR, app_id)
    os.makedirs(app_dir, exist_ok=True)
    # 已有图标则跳过
    if os.path.exists(os.path.join(app_dir, "icon.png")) or os.path.exists(os.path.join(app_dir, "icon.svg")):
        return app_id, "exists"
    domain = urlparse(m.APPS[app_id]["homepage"]).netloc
    candidates = list(ICON_URLS.get(app_id) or [])
    candidates.append(f"https://www.google.com/s2/favicons?domain={domain}&sz=256")
    for url in candidates:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urlopen(req, timeout=15).read()
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
            return app_id, f"OK {len(data)}B {url.split('?')[0][:60]}"
        except Exception as e:
            last = f"{type(e).__name__}"
    return app_id, f"FAIL ({last})"


def main():
    targets = [a for a in m.APPS if a not in {"nextcloud", "portainer", "uptime-kuma", "watchtower"}]
    results = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for app_id, msg in ex.map(fetch_icon, targets):
            results[app_id] = msg
    ok = [a for a, m in results.items() if m.startswith("OK") or m == "exists"]
    fail = [a for a, m in results.items() if m.startswith("FAIL")]
    for a in targets:
        print(f"{a}: {results[a]}")
    print(f"\n成功 {len(ok)}/{len(targets)}，失败 {len(fail)}")
    if fail:
        print("失败:", ", ".join(fail))


if __name__ == "__main__":
    main()
