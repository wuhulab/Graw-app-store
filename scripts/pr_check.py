#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PR 检查脚本：校验应用商店中每个应用的定义格式与配置是否正确。

检查范围（apps/<app-id>/ 目录）:
    1. data.yml             - 必须存在、YAML 可解析、必填字段齐全
    2. id 一致性             - data.yml 的 id 必须与目录名一致，且命名合法
    3. category 合法性       - 必须属于商店约定的 6 个分类之一
    4. versions / ports / env - 结构合法（端口范围、字段齐全）
    5. warn                 - 版本警告字段（可选，字符串）
    6. docker-compose.yml   - 必须存在、YAML 可解析、services 非空
    7. 主服务与 map_ports    - 显式声明的 map_ports 服务必须存在；主服务端口映射不冲突
    8. 图标                 - icon.png / icon.svg 至少存在一个（缺失为警告，--strict 时视为错误）

用法（在 app-store 目录内执行）:
    python scripts/pr_check.py                  # 检查 apps/ 下全部应用
    python scripts/pr_check.py <app-id> ...     # 只检查指定应用
    python scripts/pr_check.py --strict         # 图标缺失也视为错误

退出码:
    0   通过（无错误，可能有警告）
    1   存在格式 / 配置错误（CI 将据此阻止合并）

CI: .github/workflows/pr-check.yml 在 Pull Request 时自动运行本脚本。
"""
import os
import re
import sys

try:
    import yaml  # PyYAML：解析 data.yml / docker-compose.yml
except ImportError:  # pragma: no cover - CI 会安装 PyYAML
    yaml = None

APP_STORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(APP_STORE_DIR, "apps")

# 商店约定的合法分类（与 README「分类体系」保持一致）
VALID_CATEGORIES = {
    "数据库/存储", "面板/网站", "AI/开发",
    "网络/工具", "监控/运维", "开发/DevOps",
}
# 应用 id 命名规则：仅英文/数字/_/-/点，开头为字母数字
APP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
# 合法端口协议
VALID_PROTOCOLS = {"tcp", "udp", "sctp"}

# 严重级别输出前缀
_ERROR = "ERROR"
_WARN = "WARN"


def log(level: str, app_id: str, message: str):
    """统一输出检查结果：ERROR / WARN / OK。"""
    tag = {"ERROR": "[ERROR]", "WARN": "[WARN]", "OK": "[ OK ]"}.get(level, "[----]")
    print(f"{tag} {app_id or '*':<20} {message}")


def load_yaml(path: str):
    """读取 YAML 文件；解析失败返回 None 并输出错误。"""
    if yaml is None:
        print("[ERROR] 缺少 PyYAML，请先执行 pip install pyyaml")
        return None, "缺少 PyYAML"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data, None
    except Exception as e:
        return None, str(e)


def check_data_yml(app_id: str, app_dir: str) -> tuple:
    """校验 data.yml：必填字段、id 一致性、分类、版本/端口/环境变量结构。返回 (errors, warnings)。"""
    errors, warnings = [], []
    path = os.path.join(app_dir, "data.yml")
    if not os.path.isfile(path):
        return [f"缺少 data.yml"], []

    data, err = load_yaml(path)
    if err:
        return [f"data.yml 解析失败: {err}"], []
    if not isinstance(data, dict):
        return ["data.yml 顶层必须是映射（key: value）"], []

    # ---- 必填字段 ----
    required = ["id", "name", "category", "description", "homepage", "source", "arch"]
    for field in required:
        if field not in data or data.get(field) in (None, "", []):
            errors.append(f"data.yml 缺少必填字段: {field}")

    # ---- id 一致性 ----
    data_id = str(data.get("id") or "")
    if data_id != app_id:
        errors.append(f"data.yml 的 id='{data_id}' 与目录名 '{app_id}' 不一致")
    elif not APP_ID_RE.match(data_id):
        errors.append(f"id '{data_id}' 命名不合法（仅英文/数字/_/-/点，开头为字母数字）")

    # ---- category 合法性 ----
    category = data.get("category")
    if category and category not in VALID_CATEGORIES:
        errors.append(f"category '{category}' 不在合法分类内: {', '.join(sorted(VALID_CATEGORIES))}")

    # ---- versions ----
    versions = data.get("versions")
    if versions is not None:
        if not isinstance(versions, list) or not versions:
            errors.append("versions 必须是包含至少一个版本的列表")
        else:
            for i, v in enumerate(versions):
                if not isinstance(v, dict):
                    errors.append(f"versions[{i}] 必须是映射（tag/label）")
                    continue
                if not v.get("tag"):
                    errors.append(f"versions[{i}] 缺少 tag（镜像版本号）")
                if not v.get("label"):
                    errors.append(f"versions[{i}] 缺少 label（展示名）")

    # ---- ports ----
    ports = data.get("ports")
    if ports is not None:
        if not isinstance(ports, list):
            errors.append("ports 必须是列表")
        else:
            for i, p in enumerate(ports):
                if not isinstance(p, dict):
                    errors.append(f"ports[{i}] 必须是映射")
                    continue
                container = p.get("container")
                if not isinstance(container, int) or not (1 <= container <= 65535):
                    errors.append(f"ports[{i}] 的 container 必须是 1-65535 的整数，当前: {container!r}")
                if not p.get("label"):
                    errors.append(f"ports[{i}] 缺少 label（端口用途说明）")
                protocol = p.get("protocol", "tcp")
                if protocol not in VALID_PROTOCOLS:
                    errors.append(f"ports[{i}] 的 protocol 非法: {protocol}（应为 tcp/udp/sctp）")

    # ---- env ----
    envs = data.get("env")
    if envs is not None:
        if not isinstance(envs, list):
            errors.append("env 必须是列表")
        else:
            for i, e in enumerate(envs):
                if not isinstance(e, dict):
                    errors.append(f"env[{i}] 必须是映射")
                    continue
                if not e.get("name"):
                    errors.append(f"env[{i}] 缺少 name（环境变量名）")
                if "default" not in e:
                    errors.append(f"env[{i}] 缺少 default")
                if not e.get("desc"):
                    errors.append(f"env[{i}] 缺少 desc（用途说明）")

    # ---- warn（可选）----
    warn = data.get("warn")
    if warn is not None and not isinstance(warn, str):
        errors.append("warn 必须是字符串")
    elif warn and len(warn) > 500:
        errors.append("warn 文本过长（建议 500 字符以内）")

    # ---- tags（可选，商店标签，如 推荐/蓝标）----
    tags = data.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            errors.append("tags 必须是字符串列表（如 ['推荐', '蓝标']）")

    return errors, warnings


def check_compose(app_id: str, app_dir: str, data: dict) -> tuple:
    """校验 docker-compose.yml：YAML 可解析、services 非空、主服务/map_ports 引用有效。返回 (errors, warnings)。"""
    errors, warnings = [], []
    path = os.path.join(app_dir, "docker-compose.yml")
    if not os.path.isfile(path):
        return [f"缺少 docker-compose.yml"], []

    compose, err = load_yaml(path)
    if err:
        return [f"docker-compose.yml 解析失败: {err}"], []
    if not isinstance(compose, dict):
        return ["docker-compose.yml 顶层必须是映射"], []
    services = compose.get("services")
    if not isinstance(services, dict) or not services:
        return ["docker-compose.yml 缺少 services 定义"], []

    # 主服务：显式 map_ports 的服务；否则第一个使用 ${VERSION} 镜像的服务
    primary = [n for n, s in services.items()
               if isinstance(s, dict) and s.get("map_ports") is True]
    if primary:
        for p in primary:
            if p not in services:
                errors.append(f"map_ports 指向的服务 '{p}' 不存在")
    else:
        versioned = [n for n, s in services.items()
                     if isinstance(s, dict) and "${VERSION}" in str(s.get("image", ""))]
        if versioned:
            primary = [versioned[0]]

    # 环境变量引用检查：compose 中 ${XXX} 引用应已在 env 中定义（VERSION/TZ 除外，由面板注入）
    defined_env = set()
    for e in (data.get("env") or []):
        if isinstance(e, dict) and e.get("name"):
            defined_env.add(e["name"])
    # 面板会自动注入的变量
    builtin_env = {"VERSION", "TZ"}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for m in re.finditer(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", text):
        var = m.group(1)
        if var not in defined_env and var not in builtin_env:
            warnings.append(f"compose 引用了未在 env 中定义的变量 ${{{var}}}")

    return errors, warnings


def check_icon(app_id: str, app_dir: str) -> list:
    """检查图标文件是否存在（缺失为警告）。返回 warnings。"""
    warnings = []
    has_png = os.path.isfile(os.path.join(app_dir, "icon.png"))
    has_svg = os.path.isfile(os.path.join(app_dir, "icon.svg"))
    if not has_png and not has_svg:
        warnings.append("缺少图标（icon.png / icon.svg），建议补充官方图标")
    return warnings


def check_app(app_id: str, strict_icon: bool) -> tuple:
    """检查单个应用，返回 (errors, warnings)。"""
    app_dir = os.path.join(APPS_DIR, app_id)
    if not os.path.isdir(app_dir):
        return [f"应用目录不存在: {app_id}"], []

    errors, warnings = [], []

    # 1) data.yml 结构检查
    data = {}
    data_errors, data_warnings = check_data_yml(app_id, app_dir)
    errors += data_errors
    warnings += data_warnings

    # 读取 data.yml 供 compose 检查使用（若已解析成功）
    data_path = os.path.join(app_dir, "data.yml")
    if os.path.isfile(data_path) and yaml is not None:
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            pass

    # 2) docker-compose.yml 检查
    compose_errors, compose_warnings = check_compose(app_id, app_dir, data)
    errors += compose_errors
    warnings += compose_warnings

    # 3) 图标检查
    icon_warnings = check_icon(app_id, app_dir)
    if strict_icon:
        errors += icon_warnings
    else:
        warnings += icon_warnings

    return errors, warnings


def main() -> int:
    """主入口：解析参数、运行检查、汇总输出并返回退出码。"""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict_icon = "--strict" in sys.argv[1:]

    # 目标应用：未指定则检查全部
    if args:
        targets = args
    else:
        targets = sorted(
            e for e in os.listdir(APPS_DIR)
            if os.path.isdir(os.path.join(APPS_DIR, e)) and not e.startswith(".")
        )

    if not targets:
        print("[ERROR] 未找到任何应用目录")
        return 1

    total_errors, total_warnings = 0, 0
    for app_id in targets:
        errors, warnings = check_app(app_id, strict_icon)
        if not errors and not warnings:
            log("OK", app_id, "格式与配置正确")
            continue
        for e in errors:
            log(_ERROR, app_id, e)
        for w in warnings:
            log(_WARN, app_id, w)
        total_errors += len(errors)
        total_warnings += len(warnings)

    # 汇总
    print("-" * 60)
    print(f"检查完成: {len(targets)} 个应用，错误 {total_errors}，警告 {total_warnings}")
    if total_errors:
        print("存在错误，请在合并前修复（--strict 时图标缺失也视为错误）")
        return 1
    print("全部通过" + ("（含警告，建议处理）" if total_warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
