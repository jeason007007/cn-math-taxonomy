# -*- coding: utf-8 -*-
"""
题库版本暂存。

改题库（sh-questions / bn-questions / bn-sh / bn-topics / bn9b-* / figs）之后跑一次，
把当前题库源文件和打好的 bundle 一起存进 data/versions/<时间戳>/，
以后改坏了能整份退回去，不会出现「题写完了、打包失败、原稿被覆盖」。

用法:
    python build/snapshot.py                    # 存一版
    python build/snapshot.py --tag bn-v1        # 带标签，便于认
    python build/snapshot.py --list             # 看已有版本
    python build/snapshot.py --restore bn-v1    # 整份退回到某个版本

注意: --restore 会把源文件覆盖回去，bundle.js 也会一起还原。
      还原后请重新跑 python build/bundle.py 和测试，别直接部署。
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER_DIR = os.path.join(ROOT, "data", "versions")

# 一起暂存的文件：源稿 + 产物。产物也存，是为了能退回「已知能跑」的整份状态。
FILES = [
    "data/sh-questions.json",
    "data/bn-questions.json",
    "data/bn-sh.json",
    "data/bn-topics.json",
    "data/bn9b-questions.json",
    "data/bn9b-sh.json",
    "data/bn9b-topics.json",
    "data/sh-figs.json",
    "data/obj-figs.json",
    "data/bundle.js",
]

KEEP = 20   # 最多留 20 个版本，超了删最旧的


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def count_questions(path):
    if not os.path.exists(path):
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            return len(json.load(f))
    except Exception:
        return 0


def bundle_meta():
    """从 bundle.js 里把 meta 抠出来，方便一眼看出这版有多少题"""
    p = os.path.join(ROOT, "data", "bundle.js")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        raw = f.read()
    i = raw.find('"meta":')
    if i < 0:
        return {}
    j = raw.find('"topics":', i)
    if j < 0:
        return {}
    frag = raw[i:j].rstrip().rstrip(",")
    try:
        return (json.loads("{" + frag + "}") or {}).get("meta", {})
    except Exception:
        return {}


def versions():
    if not os.path.isdir(VER_DIR):
        return []
    out = []
    for name in os.listdir(VER_DIR):
        d = os.path.join(VER_DIR, name)
        if not os.path.isdir(d):
            continue
        mf = os.path.join(d, "MANIFEST.json")
        info = {}
        if os.path.exists(mf):
            try:
                with open(mf, encoding="utf-8") as f:
                    info = json.load(f)
            except Exception:
                info = {}
        out.append((name, d, info))
    out.sort(key=lambda x: x[0])
    return out


def do_list():
    vs = versions()
    if not vs:
        print("还没有暂存过版本。跑一次 python build/snapshot.py 就会生成。")
        return 0
    print("共 %d 个版本（data/versions/）：\n" % len(vs))
    for name, d, info in vs:
        m = info.get("meta", {})
        print("  %-20s %s" % (name, info.get("tag", "")))
        print("      题目 %s / 自招题 %s / 知识点 %s / 题图 %s" % (
            m.get("totalQuestions", "?"), m.get("zzAuthored", "?"),
            m.get("closureCount", "?"), m.get("figureCount", "?")))
        print("      文件 %d 个，%.1f KB" % (
            len(info.get("files", {})),
            sum(info.get("sizes", {}).values()) / 1024.0))
    return 0


def do_snapshot(tag):
    if not os.path.isdir(os.path.join(ROOT, "data")):
        print("找不到 data/ 目录，请在 g9/physics 下运行。")
        return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = stamp + ("-" + tag if tag else "")
    dest = os.path.join(VER_DIR, name)
    os.makedirs(dest, exist_ok=True)

    files, sizes, hashes = {}, {}, {}
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            continue
        flat = rel.replace("/", "__")
        shutil.copy2(src, os.path.join(dest, flat))
        files[rel] = flat
        sizes[rel] = os.path.getsize(src)
        hashes[rel] = sha(src)

    meta = bundle_meta()
    manifest = {
        "version": name,
        "tag": tag or "",
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "meta": meta,
        "files": files,
        "sizes": sizes,
        "sha256_16": hashes,
        "counts": {
            "shQuestions": count_questions(os.path.join(ROOT, "data/sh-questions.json")),
            "zzQuestions": count_questions(os.path.join(ROOT, "data/zz-questions.json")),
            "zzTopics": len((json.load(open(os.path.join(ROOT, "data/zz-topics.json"), encoding="utf-8"))
                             .get("topics", []))
                            if os.path.exists(os.path.join(ROOT, "data/zz-topics.json")) else []),
        },
    }
    with open(os.path.join(dest, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 只留最近 KEEP 个
    vs = versions()
    for old_name, old_dir, _ in vs[:-KEEP]:
        shutil.rmtree(old_dir, ignore_errors=True)
        print("清理旧版本: %s" % old_name)

    print("已暂存: data/versions/%s" % name)
    print("  题目 %s / 自招题 %s / 知识点 %s" % (
        meta.get("totalQuestions", "?"), meta.get("zzAuthored", "?"),
        meta.get("closureCount", "?")))
    for rel in files:
        print("  %-28s %8.1f KB" % (rel, sizes[rel] / 1024.0))
    return 0


def do_restore(version):
    vs = versions()
    hit = None
    for name, d, info in vs:
        if name == version or info.get("tag") == version:
            hit = (name, d, info)
    if not hit:
        print("没有找到版本 %s。可用的版本：" % version)
        for name, d, info in vs:
            print("  %s %s" % (name, info.get("tag", "")))
        return 1

    name, d, info = hit
    print("准备用 %s 覆盖当前题库。当前文件会被替换。" % name)
    for rel, flat in (info.get("files") or {}).items():
        src = os.path.join(d, flat)
        if not os.path.exists(src):
            print("  跳过（快照里没有）: %s" % rel)
            continue
        shutil.copy2(src, os.path.join(ROOT, rel))
        print("  已还原: %s" % rel)

    # 还原前先把当前状态存一版，避免退错了找不回来
    do_snapshot("before-restore-" + name)
    print("\n还原完成。请重新跑 python build/bundle.py 和 tests/test_quiz.js 确认。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="", help="版本标签，如 zz-v1")
    ap.add_argument("--list", action="store_true", help="列出已有版本")
    ap.add_argument("--restore", default="", help="退回到指定版本（名字或标签）")
    args = ap.parse_args()

    if args.list:
        return do_list()
    if args.restore:
        return do_restore(args.restore)
    return do_snapshot(args.tag)


if __name__ == "__main__":
    sys.exit(main())
