# -*- coding: utf-8 -*-
"""
用 GitHub API 把 g9-math/ 提交到 fork 的 dev 分支。
（本机 github.com 主站不可达，git push 走不通，只能走 api.github.com）

用法: python build/push_api.py
"""
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
SKIP_DIRS = {".git", "node_modules", "shots", "__pycache__"}
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
    msg = (
        "加入 g9-math：初三数学盲点诊断工具\n\n"
        "出卷 -> 打印 -> 做卷 -> 批改 -> 找盲点 -> 讲解 -> 新卷 的闭环。\n\n"
        "- 纯静态零依赖，双击 index.html 即可用，数据内嵌避免 file:// 的 CORS 限制\n"
        "- 数据取自本仓库：82 个初三知识点、376 个先修闭包、632 条先修边\n"
        "- 自编 55 道解答题（山东中考风格），带分值、分步过程和答题框高度\n"
        "- 诊断沿先修边向上 BFS 找根因，输出根因链、置信度、下游影响面\n"
        "- 可出「根因验证卷」专门考疑似根因点，验证上一轮的推断\n"
        "- 学生卷与答案卷分开打印，解答题独立起页并留大块答题空间\n"
        "- node tests/test.js：61 项自测通过\n"
    )
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
