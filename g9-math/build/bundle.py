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
    ap.add_argument("--src", default="../../cn-math-taxonomy-main")
    ap.add_argument("--out", default="data/bundle.js")
    ap.add_argument("--sh", default="data/sh-questions.json",
                    help="自编解答题（不在上游数据里）")
    ap.add_argument("--figs", default="data/sh-figs.json",
                    help="解答题题图（内联 SVG），由 build/make_figs.py 生成")
    ap.add_argument("--figs-obj", default="data/obj-figs.json",
                    help="客观题题图，由 build/make_figs_obj.py 生成")
    ap.add_argument("--bn", default="data/bn-topics.json",
                    help="北师大版（2026 新版）九上章节提纲与知识点映射")
    ap.add_argument("--bn-q", default="data/bn-questions.json",
                    help="北师大九上提高题（选择、填空）")
    ap.add_argument("--bn-sh", default="data/bn-sh.json",
                    help="北师大九上提高题（解答）")
    ap.add_argument("--bn2", default="data/bn9b-topics.json",
                    help="北师大版九下章节提纲与知识点映射")
    ap.add_argument("--bn2-q", default="data/bn9b-questions.json",
                    help="北师大九下提高题（选择、填空）")
    ap.add_argument("--bn2-sh", default="data/bn9b-sh.json",
                    help="北师大九下提高题（解答）")
    args = ap.parse_args()

    topics = load(args.src, "topics.json")
    deps = load(args.src, "dependencies.json")
    questions = load(args.src, "questions.json")
    standards = load(args.src, "cn-curriculum-standards.json")

    # 教材顺序：topics.json 本身按 年级/学期/章 排列，直接用下标
    order = {t["id"]: i for i, t in enumerate(topics)}
    tmap = {t["id"]: t for t in topics}

    # ---- 1. 初三数学知识点 ----
    # 数学点的 subject 字段缺省（None）；英语是 "english"；物理是 "physics"。
    # 上游 2026-10-22 加了初中物理，其中 40 个点是九年级的——只判 != "english"
    # 会把物理点和物理题一起混进数学卷，所以这里显式只取无 subject 的数学点。
    core_ids = [
        t["id"]
        for t in topics
        if t.get("grade") == G9 and not t.get("subject")
    ]

    # ---- 1b. 北师大版（新版）九上 / 九下提纲 ----
    # 现有题库按沪科版编排：特殊四边形在八下、相似/投影/概率在九下、反比例函数和圆在九上，
    # 和北师大版完全错位。这里用外部映射把知识点按北师大教材重新归位，
    # 不改编上游数据，出卷时按 bnUnit（九上）/ bn2Unit（九下）筛选即可。
    def load_bn_spec(path):
        """读一份北师大章节映射，返回 (map, units, new_ids, excluded)"""
        bmap, units, new_ids, excluded = {}, [], set(), set()
        if not path or not os.path.exists(path):
            return bmap, units, new_ids, excluded
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
        for ch in spec["chapters"]:
            secs = []
            for sec in ch["sections"]:
                secs.append({"no": sec["no"], "title": sec["title"],
                             "topics": list(sec["topics"])})
                for tid in sec["topics"]:
                    bmap[tid] = {"unit": ch["no"], "sec": sec["no"],
                                 "secTitle": sec["title"]}
            units.append({"no": ch["no"], "title": ch["title"],
                          "desc": ch.get("desc", ""), "sections": secs})
        for k, v in (spec.get("exclude") or {}).items():
            if k == "note":
                continue
            excluded |= set(v)
        new = spec.get("newTopics") or []
        new_ids = {t["id"] for t in new}
        # 新增知识点并入 tmap / order，后续统一处理
        for nt in new:
            tmap[nt["id"]] = nt
            order[nt["id"]] = nt.get("order", 9999)
        return bmap, units, new_ids, excluded

    bn_map, bn_units, bn_new_ids, bn_excluded = load_bn_spec(args.bn)
    bn2_map, bn2_units, bn2_new_ids, bn2_excluded = load_bn_spec(args.bn2)

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

    # 北师大版用到的点（八下的特殊四边形、九下的相似与投影、沪科版九上的圆等）
    # 不在九年级闭包里，但按北师大教材它们就是正课内容，必须一起纳入。
    closure |= set(bn_map) | set(bn2_map)

    # ---- 3. 精简 topics ----
    core_set = set(core_ids) | bn_new_ids | bn2_new_ids
    out_topics = []
    for tid in closure:
        t = tmap[tid]
        stds = [s["id"] if isinstance(s, dict) else s for s in (t.get("standards") or [])]
        bm = bn_map.get(tid)
        bm2 = bn2_map.get(tid)
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
            "isCore": tid in core_set,   # 是否初三本体
            # 北师大版九上归位：第几章、第几节
            "bnUnit": bm["unit"] if bm else None,
            "bnSec": bm["sec"] if bm else None,
            "bnSecTitle": bm["secTitle"] if bm else None,
            "bnNew": tid in bn_new_ids,
            # 按北师大教材不属于九上的章（反比例函数、圆、三角函数、旋转等）
            "bnOut": tid in bn_excluded,
            # 北师大版九下归位
            "bn2Unit": bm2["unit"] if bm2 else None,
            "bn2Sec": bm2["sec"] if bm2 else None,
            "bn2SecTitle": bm2["secTitle"] if bm2 else None,
            "bn2New": tid in bn2_new_ids,
            # 按北师大教材不属于九下的章（相似、二次函数、概率等）
            "bn2Out": tid in bn2_excluded,
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

    # ---- 4b. 题图（两批：自编解答题 + 客观题） ----
    figs = {}
    for fp in (args.figs, args.figs_obj):
        if fp and os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                figs.update(json.load(f))

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
        if q["id"] in figs:
            item["fig"] = figs[q["id"]]
        out_qs.append(item)

    # ---- 5b. 合入自编解答题 ----
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

    # ---- 5c. 合入北师大提高题（九上 / 九下）----
    # 这些题的难度标 zz（比 advanced 再高一档），只在对应的北师大档位里抽。
    bn_qs = []
    bn2_qs = []
    for fp, origin in ((args.bn_q, "bn"), (args.bn_sh, "bn"),
                       (args.bn2_q, "bn2"), (args.bn2_sh, "bn2")):
        if not fp or not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f)
        for q in raw:
            tid = q["topicId"]
            if tid not in tmap:
                print("WARN 北师大题库指向不存在的知识点，已跳过: %s" % q.get("id"))
                continue
            qtype = q.get("type", "numeric")
            item = {
                "id": q["id"],
                "topicId": tid,
                "difficulty": q.get("difficulty", "zz"),
                "type": qtype,
                "prompt": q["prompt"],
                "answer": q["answer"],
                "explanation": q.get("explanation") or q.get("solution", ""),
                "origin": origin,
            }
            if q.get("choices"):
                item["choices"] = [{"key": c["key"], "text": c["text"]} for c in q["choices"]]
            if q.get("table"):
                item["table"] = q["table"]
            if qtype == "short":
                item["solution"] = q.get("solution", "")
                item["points"] = q.get("points", 8)
                item["space"] = q.get("space", 200)
            fid = q.get("fig")
            if fid and fid in figs:
                item["fig"] = figs[fid]
            elif fid:
                print("WARN 题图缺失: %s -> %s" % (q["id"], fid))
            out_qs.append(item)
            (bn2_qs if origin == "bn2" else bn_qs).append(item)

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
    core_qs = [q for q in out_qs if q["topicId"] in core_set]
    bn_topic_count = sum(1 for t in out_topics if t["bnUnit"])
    bn2_topic_count = sum(1 for t in out_topics if t["bn2Unit"])
    meta = {
        "source": "cn-math-taxonomy (CC BY-NC 4.0)",
        "upstream": "xiaoyang111222/cn-math-taxonomy@d9c1ab7",
        "dataVersion": "2026-10-22",
        "generatedAt": "2026-10-27",
        "coreCount": len(core_ids),
        "closureCount": len(closure),
        "depCount": len(out_deps),
        "questionCount": len(core_qs),
        "totalQuestions": len(out_qs),
        "selfAuthored": len(self_qs),
        "figureCount": sum(1 for q in out_qs if q.get("fig")),
        "shortCount": sum(1 for q in core_qs if q["type"] == "short"),
        "gradeDist": dict(sorted(collections.Counter(tmap[i].get("grade") for i in closure).items())),
        "noQuestionTopics": sorted([t["id"] for t in out_topics if t["isCore"] and q_by_topic[t["id"]] == 0]),
        "thinTopics": sorted([t["id"] for t in out_topics if t["isCore"] and 0 < q_by_topic[t["id"]] < 2]),
        # 北师大版（2026 新版）九上
        "bnEdition": "北师大版（2026 新版）",
        "bnCount": bn_topic_count,
        "bnNewCount": len(bn_new_ids),
        "bnOutCount": sum(1 for t in out_topics if t["bnOut"]),
        "bnQuestionCount": len(bn_qs),
        # 北师大九上卷面：10 选择 + 6 填空 + 8 解答，和青大附中期中卷一致
        "bnPaperShape": {"choice": 10, "numeric": 6, "short": 8},
        # 北师大版九下（2024/2026 新版）
        "bn2Edition": "北师大版（2024/2026 新版）",
        "bn2Count": bn2_topic_count,
        "bn2NewCount": len(bn2_new_ids),
        "bn2OutCount": sum(1 for t in out_topics if t["bn2Out"]),
        "bn2QuestionCount": len(bn2_qs),
        "bn2PaperShape": {"choice": 10, "numeric": 6, "short": 8},
    }

    payload = {
        "meta": meta,
        "topics": out_topics,
        "deps": out_deps,
        "questions": out_qs,
        "chapters": chapters,
        "bnChapters": bn_units,
        "bn2Chapters": bn2_units,
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
    print("北师大九上: %d 个知识点 / %d 道提高题（新增点 %d，九上外 %d）" % (
        meta["bnCount"], meta["bnQuestionCount"], meta["bnNewCount"], meta["bnOutCount"]))
    print("北师大九下: %d 个知识点 / %d 道提高题（新增点 %d，九下外 %d）" % (
        meta["bn2Count"], meta["bn2QuestionCount"], meta["bn2NewCount"], meta["bn2OutCount"]))
    print("年级分布:   %s" % meta["gradeDist"])
    print("无题知识点: %d %s" % (len(meta["noQuestionTopics"]), meta["noQuestionTopics"][:10]))
    print("题目<2 的:  %d %s" % (len(meta["thinTopics"]), meta["thinTopics"][:10]))
    print("输出:       %s (%.1f KB)" % (args.out, size / 1024))


if __name__ == "__main__":
    sys.exit(main())
