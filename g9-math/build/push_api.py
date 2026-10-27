# -*- coding: utf-8 -*-
"""
用 GitHub API 把本目录（g9/math）提交到 fork 的 dev 分支，落到远端 g9-math/ 下。
（本机 github.com 主站不可达，git push 走不通，只能走 api.github.com）

用法:
    python build/push_api.py -m "提交说明"
    python build/push_api.py -m-file /tmp/msg.txt
"""
import argparse
import json
import os
import subprocess
import sys

REPO = "jeason007007/cn-math-taxonomy"
BRANCH = "dev"
PREFIX = "g9-math"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".push_payload.json")

# 不提交的文件
# versions/ 是本地题库快照（20 个版本 × 10 个文件 ≈ 27 MB），只作本机备份，不进仓库
SKIP_DIRS = {".git", "node_modules", "shots", "__pycache__", "versions"}
SKIP_FILES = {".push_payload.json"}


def gh(args, payload=None, method=None):
    cmd = ["gh", "api"]
    if method:
        cmd += ["-X", method]
    cmd += args
    if payload is not None:
        with open(TMP, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        cmd += ["--input", TMP]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("gh api 失败: %s\n%s" % (" ".join(cmd), r.stderr))
    return json.loads(r.stdout) if r.stdout.strip() else None


def walk():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            out.append((rel, full))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", default="", help="提交说明")
    ap.add_argument("-m-file", "--message-file", default="", help="从文件读提交说明")
    args = ap.parse_args()

    msg = args.message
    if args.message_file:
        with open(args.message_file, encoding="utf-8") as f:
            msg = f.read()
    if not msg.strip():
        raise SystemExit("必须用 -m 或 -m-file 给一条提交说明")

    files = walk()
    print("待提交文件 %d 个：" % len(files))
    for rel, full in files:
        print("  %-32s %8.1f KB" % (rel, os.path.getsize(full) / 1024))

    # 当前 dev 分支头
    ref = gh(["repos/%s/git/ref/heads/%s" % (REPO, BRANCH)])
    parent = ref["object"]["sha"]
    commit = gh(["repos/%s/git/commits/%s" % (REPO, parent)])
    base_tree = commit["tree"]["sha"]
    print("\n父提交 %s，基树 %s" % (parent[:7], base_tree[:7]))

    # 1. 上传 blob
    entries = []
    for rel, full in files:
        with open(full, encoding="utf-8") as f:
            content = f.read()
        blob = gh(["repos/%s/git/blobs" % REPO],
                  {"content": content, "encoding": "utf-8"}, method="POST")
        entries.append({
            "path": PREFIX + "/" + rel,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print("  blob %s  %s" % (blob["sha"][:7], rel))

    # 2. 建树
    tree = gh(["repos/%s/git/trees" % REPO],
              {"base_tree": base_tree, "tree": entries}, method="POST")
    print("\n新树 %s" % tree["sha"][:7])

    # 3. 建提交
    new_commit = gh(["repos/%s/git/commits" % REPO],
                    {"message": msg, "tree": tree["sha"], "parents": [parent]},
                    method="POST")
    print("新提交 %s" % new_commit["sha"][:7])

    # 4. 移动分支
    gh(["repos/%s/git/refs/heads/%s" % (REPO, BRANCH)],
       {"sha": new_commit["sha"], "force": False}, method="PATCH")
    print("\n已更新 %s -> %s" % (BRANCH, new_commit["sha"][:7]))

    if os.path.exists(TMP):
        os.remove(TMP)

    print("https://github.com/%s/tree/%s/%s" % (REPO, BRANCH, PREFIX))


if __name__ == "__main__":
    sys.exit(main())
