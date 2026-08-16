# -*- coding: utf-8 -*-
"""为所有现有 data.yml 补写 category 分类字段（幂等，已存在则跳过）。

用法（在 app-store 目录内执行）:
    python scripts/add_categories.py
"""
import os
import re
import sys

APP_STORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(APP_STORE_DIR, "apps")

# 复用 batch_add_apps.py 中的分类映射，保证唯一数据源
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_add_apps import CATEGORY  # noqa: E402


def main() -> int:
    patched = 0
    missing = []
    for entry in sorted(os.listdir(APPS_DIR)):
        app_dir = os.path.join(APPS_DIR, entry)
        if not os.path.isdir(app_dir) or entry.startswith("."):
            continue
        path = os.path.join(app_dir, "data.yml")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        # 已有 category 则跳过（幂等）
        if re.search(r"(?m)^category\s*:", text):
            continue
        cat = CATEGORY.get(entry, "其它")
        if cat == "其它" and entry not in CATEGORY:
            missing.append(entry)
        # 在 id: 行之后插入 category 行，保持与 gen_data 生成格式一致
        new_text = re.sub(
            r'(?m)^(id\s*:\s*"[^"]*"\s*)$',
            r'\1\n\ncategory: "' + cat + '"',
            text,
            count=1,
        )
        if new_text == text:
            print(f"[skip] {entry}: 未找到 id 行")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        patched += 1
        print(f"[patch] {entry} -> {cat}")
    print(f"\n共补写分类: {patched} 个")
    if missing:
        print("未匹配到分类（已归入其它）:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
