# -*- coding: utf-8 -*-
"""
从 cn-math-taxonomy 抽取「初三数学」子图，生成可离线（file://）加载的 bundle.js

用法:
    python build/bundle.py --src ../cn-math-taxonomy-main --out data/bundle.js

产出:
    data/bundle.js  ->  window.CN_DATA = {...}
"""
import argparse
import collections
import json
import os
import sys

# 初三 = 九年级数学。初中数学 grade 字段取值 7/8/9；小学 1-6；高中 10-14
G9 = 9


def load(src, name):
    with open(os.path.join(src, "data", name), encoding="utf-8") as f:
        return json.load(f)


# "九上 第二十五章 一元二次方程 25.1" -> "九上 第二十五章 一元二次方程"
# 保留 "拓展" / "综合与实践" 这类后缀，它们不是节号
import re
_TAIL_RE = re.compile(r"\s+(?:\d+(?:\.\d+)*|拓展|综合与实践|综合应用（[^）]*）)\s*$")


def chapter_group(chapter):
    """归并到「章」一级：去掉节号、拓展、综合与实践等尾巴。"""
    if not chapter:
        return ""
    s = chapter.strip()
    while True:
        n = _TAIL_RE.sub("", s)
        if n == s:
            break
        s = n
    return s.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../cn-math-taxonomy-main")
    ap.add_argument("--out", default="data/bundle.js")
    ap.add_argument("--sh", default="data/sh-questions.json",
                    help="自编解答题（不在上游数据里）")
    ap.add_argument("--figs", default="data/sh-figs.json",
                    help="解答题题图（内联 SVG），由 build/make_figs.py 生成")
    args = ap.parse_args()

    topics = load(args.src, "topics.json")
    deps = load(args.src, "dependencies.json")
    questions = load(args.src, "questions.json")
    standards = load(args.src, "cn-curriculum-standards.json")

    # 教材顺序：topics.json 本身按 年级/学期/章 排列，直接用下标
    order = {t["id"]: i for i, t in enumerate(topics)}
    tmap = {t["id"]: t for t in topics}

    # ---- 1. 初三数学知识点 ----
    core_ids = [
        t["id"]
        for t in topics
        if t.get("grade") == G9 and t.get("subject") != "english"
    ]

    # ---- 2. 先修闭包（沿 prerequisite 边向上） ----
    pre_of = collections.defaultdict(list)
    for e in deps:
        pre_of[e["topicId"]].append(e)

    closure = set(core_ids)
    stack = list(core_ids)
    while stack:
        cur = stack.pop()
        for e in pre_of.get(cur, []):
            p = e["prerequisiteId"]
            if p in tmap and p not in closure:
                closure.add(p)
                stack.append(p)

    # ---- 3. 精简 topics ----
    out_topics = []
    for tid in closure:
        t = tmap[tid]
        stds = [s["id"] if isinstance(s, dict) else s for s in (t.get("standards") or [])]
        out_topics.append({
            "id": tid,
            "name": t.get("name", ""),
            "domain": t.get("domain", ""),
            "grade": t.get("grade"),
            "semester": t.get("semester", ""),
            "chapter": t.get("chapter", ""),
            "chap": chapter_group(t.get("chapter", "")),
            "type": t.get("type", ""),
            "description": t.get("description", ""),
            "mastery_criteria": t.get("mastery_criteria") or [],
            "diagnostic_question": t.get("diagnostic_question"),
            "standards": stds,
            "order": order.get(tid, 9999),
            "isCore": tid in set(core_ids),   # 是否初三本体
        })
    out_topics.sort(key=lambda x: x["order"])

    # ---- 4. 闭包内的先修边 ----
    out_deps = [
        {
            "topicId": e["topicId"],
            "prerequisiteId": e["prerequisiteId"],
            "strength": e.get("strength", "soft"),
            "reason": e.get("reason", ""),
        }
        for e in deps
        if e["topicId"] in closure and e["prerequisiteId"] in closure
    ]

    # ---- 5. 闭包内的题（初三题优先，先修点的题用于讲解例题） ----
    out_qs = []
    for q in questions:
        if q["topicId"] not in closure:
            continue
        item = {
            "id": q["id"],
            "topicId": q["topicId"],
            "difficulty": q.get("difficulty", "standard"),
            "type": q.get("type", "numeric"),
            "prompt": q.get("prompt", ""),
            "answer": q.get("answer", ""),
            "explanation": q.get("explanation", ""),
        }
        if q.get("choices"):
            item["choices"] = [{"key": c["key"], "text": c["text"]} for c in q["choices"]]
        out_qs.append(item)

    # ---- 5b. 合入自编解答题 ----
    figs = {}
    if args.figs and os.path.exists(args.figs):
        with open(args.figs, encoding="utf-8") as f:
            figs = json.load(f)

    self_qs = []
    if args.sh and os.path.exists(args.sh):
        with open(args.sh, encoding="utf-8") as f:
            raw = json.load(f)
        for q in raw:
            tid = q["topicId"]
            if tid not in tmap:
                print("WARN 解答题指向不存在的知识点，已跳过: %s" % q.get("id"))
                continue
            if tid not in closure:
                print("WARN 解答题的知识点不在闭包内: %s -> %s" % (q.get("id"), tid))
            item = {
                "id": q["id"],
                "topicId": tid,
                "difficulty": q.get("difficulty", "standard"),
                "type": "short",
                "prompt": q["prompt"],
                "answer": q["answer"],
                "explanation": q.get("solution", ""),
                "solution": q.get("solution", ""),
                "points": q.get("points", 8),
                "space": q.get("space", 200),
                "origin": "self",
            }
            if q["id"] in figs:
                item["fig"] = figs[q["id"]]
            out_qs.append(item)
            self_qs.append(item)

    # ---- 6. 章节目录（章一级） ----
    chapters = []
    seen = set()
    for t in out_topics:
        if not t["isCore"]:
            continue
        key = t["chap"]
        if key in seen:
            continue
        seen.add(key)
        members = [x for x in out_topics if x["isCore"] and x["chap"] == key]
        chapters.append({
            "semester": t["semester"],
            "chap": t["chap"],
            "chapter": t["chap"],
            "short": chapter_group(t["chap"]),
            "count": len(members),
        })

    # ---- 7. 统计 ----
    q_by_topic = collections.Counter(q["topicId"] for q in out_qs)
    core_qs = [q for q in out_qs if q["topicId"] in set(core_ids)]
    meta = {
        "source": "cn-math-taxonomy (CC BY-NC 4.0)",
        "generatedAt": "2026-10-21",
        "coreCount": len(core_ids),
        "closureCount": len(closure),
        "depCount": len(out_deps),
        "questionCount": len(core_qs),
        "selfAuthored": len(self_qs),
        "figureCount": sum(1 for q in out_qs if q.get("fig")),
        "shortCount": sum(1 for q in core_qs if q["type"] == "short"),
        "gradeDist": dict(sorted(collections.Counter(tmap[i].get("grade") for i in closure).items())),
        "noQuestionTopics": sorted([t["id"] for t in out_topics if t["isCore"] and q_by_topic[t["id"]] == 0]),
        "thinTopics": sorted([t["id"] for t in out_topics if t["isCore"] and 0 < q_by_topic[t["id"]] < 2]),
    }

    payload = {
        "meta": meta,
        "topics": out_topics,
        "deps": out_deps,
        "questions": out_qs,
        "chapters": chapters,
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/* 自动生成，勿手改。重新生成: python build/bundle.py */\n")
        f.write("window.CN_DATA=")
        f.write(body)
        f.write(";\n")

    size = os.path.getsize(args.out)
    print("核心知识点: %d" % meta["coreCount"])
    print("先修闭包:   %d" % meta["closureCount"])
    print("先修边:     %d" % meta["depCount"])
    print("题目:       %d" % len(out_qs))
    print("题图:       %d" % sum(1 for q in out_qs if q.get("fig")))
    print("章节:       %d" % len(chapters))
    print("年级分布:   %s" % meta["gradeDist"])
    print("无题知识点: %d %s" % (len(meta["noQuestionTopics"]), meta["noQuestionTopics"][:10]))
    print("题目<2 的:  %d %s" % (len(meta["thinTopics"]), meta["thinTopics"][:10]))
    print("输出:       %s (%.1f KB)" % (args.out, size / 1024))


if __name__ == "__main__":
    sys.exit(main())
