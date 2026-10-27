/* 初三数学盲点诊断 - 核心引擎
 * 依赖 window.CN_DATA（data/bundle.js）
 * 纯函数，无 DOM 依赖，可在 Node 里单测
 */
(function (root) {
  'use strict';

  var D = root.CN_DATA;
  if (!D) throw new Error('缺少 data/bundle.js');

  /* ---------- 索引 ---------- */
  var TOPIC = {};
  var QUESTION = {};
  var Q_OF = {};        // topicId -> [question]
  var PRE_OF = {};      // topicId -> [{id, strength, reason}]
  var DEP_OF = {};      // topicId -> [topicId]  谁依赖我

  D.topics.forEach(function (t) {
    TOPIC[t.id] = t;
    Q_OF[t.id] = [];
    PRE_OF[t.id] = [];
    DEP_OF[t.id] = [];
  });
  D.questions.forEach(function (q) {
    QUESTION[q.id] = q;
    if (Q_OF[q.topicId]) Q_OF[q.topicId].push(q);
  });
  D.deps.forEach(function (e) {
    if (PRE_OF[e.topicId] && TOPIC[e.prerequisiteId]) {
      PRE_OF[e.topicId].push({ id: e.prerequisiteId, strength: e.strength, reason: e.reason });
    }
    if (DEP_OF[e.prerequisiteId]) DEP_OF[e.prerequisiteId].push(e.topicId);
  });

  /* 难度排序权重 */
  /* 难度排序权重。zz 是「北师大九上压轴」档，比 advanced 再高一档，
     只有 tier==='bn' 的卷子才抽；普通卷反过来不掺 zz，避免难度失控。 */
  var DIFF_RANK = { basic: 0, standard: 1, advanced: 2, zz: 3 };
  var TYPE_SECTION = { choice: 0, numeric: 1, short: 2, self: 2 };

  /* 选择、填空在原题库里没写分值，卷面按中考惯例给 3 分 */
  var DEFAULT_POINTS = { choice: 3, numeric: 3, short: 8, self: 8 };

  /* 把解答题分值按比例缩放到「满分 − 客观题得分」，取整后余数补给小数部分最大的几道。
     按 2 分一档分配（真实卷面很少出现 9 分、11 分这种奇数分），
     既保住压轴题分值高的相对关系，整卷又刚好凑成整数满分。 */
  function rebalancePoints(items, target) {
    var shorts = items.filter(function (p) {
      return p.type === 'short' || p.type === 'self';
    });
    if (!shorts.length) return;
    var objSum = 0;
    items.forEach(function (p) {
      if (shorts.indexOf(p) === -1) objSum += p.points;
    });
    var shortTarget = target - objSum;
    var sum = shorts.reduce(function (a, p) { return a + p.points; }, 0);
    /* 每道解答题至少 4 分，凑不出来就别硬凑 */
    if (!sum || shortTarget <= shorts.length * 4) return;

    var unit = (shortTarget % 2 === 0) ? 2 : 1;   /* 一档几分 */
    var slots = shortTarget / unit;               /* 一共几档 */
    var raw = shorts.map(function (p) { return p.points / sum * slots; });
    var got = raw.map(Math.floor);
    var left = slots - got.reduce(function (a, v) { return a + v; }, 0);
    var order = raw.map(function (v, i) { return { i: i, frac: v - Math.floor(v) }; })
      .sort(function (a, b) { return b.frac - a.frac; });
    for (var k = 0; k < left; k++) got[order[k % order.length].i] += 1;
    shorts.forEach(function (p, i) { p.points = got[i] * unit; });
  }

  /* ---------- 工具 ---------- */
  function rngFactory(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gradeLabel(g) {
    if (g >= 10) return '高中';
    var cn = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
    return (cn[g] || g) + '年级';
  }

  function semesterLabel(t) {
    if (!t.semester) return '';
    return t.semester === '全' ? '' : t.semester + '册';
  }

  /* 北师大版（2026 新版）九上章节标签。
     沪科版把菱形、矩形、正方形编在八年级，北师大版九上第一章就是特殊平行四边形，
     所以压轴卷里不能写"八年级"——那不是错的教材就是错的位置，孩子照着翻不到。
     有 bnUnit 就按北师大章节说：第几章靠小节号就能看出来（1.1 就是第一章）。 */
  function bnLabel(t, tier) {
    if (!t) return '';
    var down = (tier === 'bn2');
    var unit = down ? t.bn2Unit : t.bnUnit;
    if (!unit) return '';
    var sec = (down ? t.bn2Sec : t.bnSec) || '';
    var title = (down ? t.bn2SecTitle : t.bnSecTitle) || '';
    if (title.length > 12) title = title.slice(0, 12) + '…';
    return (down ? '北师大九下' : '北师大九上') + (sec ? ' ' + sec : '') + (title ? ' ' + title : '');
  }

  /* 章节短名：从 "九上 第二十五章 一元二次方程 25.1" 提取 "第二十五章 一元二次方程" */
  function chapterShort(chapter) {
    if (!chapter) return '';
    var s = chapter.replace(/^[七八九]上\s*/, '').replace(/^[七八九]下\s*/, '');
    var parts = s.split(/\s+/);
    if (parts.length >= 2) {
      return parts[0] + ' ' + parts[1];
    }
    return s;
  }

  function coreTopics() {
    /* bnUnit 有值 = 按北师大版属于九上，bn2Unit 有值 = 属于九下。
       特殊四边形在沪科版里编在八年级，grade 是 8、isCore 是 false，
       但北师大版把它放在九上第一章；圆和反比例函数在沪科版是九上，
       北师大版却是九下。两种归位都得算进来，否则对应学期的卷子会抽不到题。 */
    return D.topics.filter(function (t) { return t.isCore || t.bnUnit || t.bn2Unit; });
  }

  /* 最可信先修链：贪心向上，优先 hard 边、优先低年级、优先教材靠前 */
  function chainTo(topicId, maxDepth) {
    maxDepth = maxDepth || 10;
    var path = [topicId];
    var cur = topicId;
    var guard = 0;
    while (guard++ < maxDepth) {
      var pres = (PRE_OF[cur] || []).slice();
      if (!pres.length) break;
      pres.sort(function (a, b) {
        var ta = TOPIC[a.id], tb = TOPIC[b.id];
        if (a.strength !== b.strength) return a.strength === 'hard' ? -1 : 1;
        if (ta.order !== tb.order) return ta.order - tb.order;
        return 0;
      });
      cur = pres[0].id;
      if (path.indexOf(cur) !== -1) break;
      path.push(cur);
    }
    return path.reverse(); // 从最早的前置到当前
  }

  /* 下游影响面：有多少个初三知识点（传递）依赖它 */
  function downstreamCount(topicId) {
    var seen = {};
    var stack = (DEP_OF[topicId] || []).slice();
    while (stack.length) {
      var cur = stack.pop();
      if (seen[cur]) continue;
      seen[cur] = 1;
      (DEP_OF[cur] || []).forEach(function (x) { stack.push(x); });
    }
    var n = 0;
    Object.keys(seen).forEach(function (id) {
      if (TOPIC[id] && TOPIC[id].isCore) n++;
    });
    return n;
  }

  /* ---------- 出卷 ---------- */
  /**
   * opts:
   *   scope      {semesters:['上','下']} 或 {chapters:['...']}
   *   count      题数
   *   ratio      {basic, standard, advanced} 占比，和为 1
   *   mode       'normal' | 'probe' | 'mixed'
   *   focus      [topicId]  盲点（加权）
   *   probe      [topicId]  根因候选（可含非初三）
   *   usedQids   {qid:1}    做过的题
   *   seed       随机种子
   */
  function generatePaper(opts) {
    var rnd = rngFactory(opts.seed || 20261021);
    var count = opts.count || 20;
    var mode = opts.mode || 'normal';
    var focus = opts.focus || [];
    var probe = opts.probe || [];
    var usedQids = opts.usedQids || {};
    /* tier='bn' 表示「北师大九上」卷：范围按北师大教材的六章走，只抽 zz 难度的题。
       普通卷（tier 为空）反过来排除 zz，两档互不污染。 */
    var tier = opts.tier || '';
    /* 北师大两档共用一套逻辑：只是章节字段和标签名不同 */
    var isBn = (tier === 'bn' || tier === 'bn2');
    var unitKey = (tier === 'bn2') ? 'bn2Unit' : 'bnUnit';
    var bnUnits = opts.bnUnits || [];

    /* 根因验证卷：只出探测点，有几个点出几道题，不拿无关题凑数 */
    if (mode === 'probe') {
      var avail = probe.filter(function (id) {
        return TOPIC[id] && Q_OF[id] && Q_OF[id].length;
      });
      count = Math.min(count, avail.length);
    }

    /* 1. 范围池 */
    var scopeTopics = coreTopics().filter(function (t) {
      if (isBn) {
        /* 按北师大版归位：只有对应学期的 bnUnit 有值，才算这学期正课内容 */
        if (!t[unitKey]) return false;
        if (bnUnits.length && bnUnits.indexOf(t[unitKey]) === -1) return false;
      }
      if (opts.scope && opts.scope.semesters && opts.scope.semesters.length) {
        if (opts.scope.semesters.indexOf(t.semester) === -1) return false;
      }
      if (opts.scope && opts.scope.chapters && opts.scope.chapters.length) {
        if (opts.scope.chapters.indexOf(t.chap) === -1) return false;
      }
      return true;
    });

    /* 2. 组装候选池 + 配额 */
    var pool = [];       // {id, weight}
    var probeQuota = 0;
    if (mode === 'probe') {
      probeQuota = count;
    } else if (mode === 'mixed') {
      probeQuota = Math.max(2, Math.round(count * 0.3));
    }

    function addPool(ids, boost) {
      ids.forEach(function (id) {
        if (!TOPIC[id]) return;
        if (!Q_OF[id] || !Q_OF[id].length) return;
        for (var i = 0; i < pool.length; i++) {
          if (pool[i].id === id) { pool[i].weight += boost; return; }
        }
        pool.push({ id: id, weight: boost });
      });
    }

    addPool(scopeTopics.map(function (t) { return t.id; }), 1);
    addPool(focus, 2);   // 盲点：基础权重 1 + 2 = 3
    addPool(probe, 2);   // 根因候选同理

    /* 3. 基础权重调整 */
    var stats = opts.topicStats || {};
    pool.forEach(function (p) {
      var st = stats[p.id];
      if (!st) {
        p.weight *= 1.5;              // 没测过，优先覆盖
      } else if (st.lastWrongAt && (!st.lastOkAt || st.lastWrongAt > st.lastOkAt)) {
        p.weight *= 1.6;              // 上次做错还没扳回来
      } else if (st.okStreak >= 2) {
        p.weight *= 0.5;              // 连着对了，降低频率
      }
    });

    /* 3b. 偏难模式：加权应用 / 推理 / 建模类知识点（山东中考风格） */
    if (opts.hardMode) {
      pool.forEach(function (p) {
        var tp = TOPIC[p.id].type;
        if (tp === 'application' || tp === 'reasoning' || tp === 'modeling') {
          p.weight *= 1.4;
        }
      });
    }

    /* 4. 难度槽位（只给客观题分配；解答题单独留名额） */
    var shortCount = Math.max(0, Math.min(opts.shortCount || 0, count));
    var objCount = Math.max(0, count - shortCount);
    var ratio = opts.ratio || { basic: 0.4, standard: 0.4, advanced: 0.2 };
    var slots = [];
    /* 北师大九上压轴档不分基础/提高，槽位一律是 zz */
    var diffKeys = isBn ? ['zz'] : ['basic', 'standard', 'advanced'];
    var diffRatio = isBn ? { zz: 1 } : ratio;
    diffKeys.forEach(function (d) {
      var n = Math.round(objCount * (diffRatio[d] || 0));
      for (var i = 0; i < n; i++) slots.push(d);
    });
    var fillDiff = isBn ? 'zz' : 'standard';
    while (slots.length < objCount) slots.push(fillDiff);
    slots = slots.slice(0, objCount);
    /* 由易到难排序，便于排卷 */
    slots.sort(function (a, b) { return DIFF_RANK[a] - DIFF_RANK[b]; });

    /* 5. 章节配额，防止一张卷压在一章 */
    var chaptersInScope = {};
    scopeTopics.forEach(function (t) { chaptersInScope[t.chap] = 1; });
    var nCh = Object.keys(chaptersInScope).length || 1;
    var capPerChapter = Math.max(2, Math.ceil(count / nCh * 1.8));

    /* 6. 选题 */
    var picked = [];        // {qid, topicId, difficulty, type}
    var chapterUsed = {};
    var topicUsed = {};
    var pickedQids = {};    // 本卷已选的题，防止同一道题出现两次

    function isObjective(q) { return q.type !== 'short' && q.type !== 'self'; }

    /* 难度档过滤：北师大九上卷只认 zz，普通卷反过来不掺 zz */
    function tierOk(q) {
      if (isBn) return q.difficulty === 'zz';
      return q.difficulty !== 'zz';
    }

    function objQsOf(id, relax) {
      return (Q_OF[id] || []).filter(function (q) {
        return isObjective(q) && (relax || tierOk(q));
      });
    }

    function shortQsOf(id, relax) {
      return (Q_OF[id] || []).filter(function (q) {
        return !isObjective(q) && (relax || tierOk(q));
      });
    }

    function poolForSlot(slotDiff) {
      return pool.filter(function (p) {
        /* 北师大九上题库只有三十几道题、覆盖十几个点，出二十几题必须复用知识点，
           靠 pickedQids 保证不重题；普通卷仍保持「一个点一题」。 */
        if (topicUsed[p.id] && !isBn) return false;
        var t = TOPIC[p.id];
        if (!isBn && t.isCore && (chapterUsed[t.chap] || 0) >= capPerChapter) return false;
        return objQsOf(p.id).some(function (q) { return !pickedQids[q.id]; });
      });
    }

    function pickWeighted(arr) {
      var total = 0;
      arr.forEach(function (p) { total += p.weight; });
      if (total <= 0) return null;
      var r = rnd() * total;
      for (var i = 0; i < arr.length; i++) {
        r -= arr[i].weight;
        if (r <= 0) return arr[i];
      }
      return arr[arr.length - 1];
    }

    /* 6a. 先挑解答题 */
    var shortPicked = 0;
    var shortPool = pool.filter(function (p) {
      return shortQsOf(p.id).some(function (q) { return !pickedQids[q.id]; });
    });
    var shortGuard = 0;
    while (shortPicked < shortCount && shortGuard++ < shortCount * 4 + 8) {
      var scands = shortPool.filter(function (p) {
        if (!isBn && topicUsed[p.id]) return false;
        return shortQsOf(p.id).some(function (q) { return !pickedQids[q.id]; });
      });
      if (!scands.length) break;
      var sChosen = pickWeighted(scands);
      if (!sChosen) break;

      var sqs = shortQsOf(sChosen.id).filter(function (q) {
        return !usedQids[q.id] && !pickedQids[q.id];
      });
      if (!sqs.length) sqs = shortQsOf(sChosen.id).filter(function (q) { return !pickedQids[q.id]; });
      if (!sqs.length) sqs = shortQsOf(sChosen.id, true).filter(function (q) { return !pickedQids[q.id]; });
      if (!sqs.length) { topicUsed[sChosen.id] = 1; continue; }
      /* 偏难模式下优先 advanced */
      sqs.sort(function (a, b) {
        return (opts.hardMode ? DIFF_RANK[b.difficulty] - DIFF_RANK[a.difficulty]
                              : DIFF_RANK[a.difficulty] - DIFF_RANK[b.difficulty]);
      });
      var sq = sqs[0];

      pickedQids[sq.id] = 1;
      picked.push({
        qid: sq.id,
        topicId: sChosen.id,
        difficulty: sq.difficulty,
        type: sq.type,
        points: sq.points || 0,
        isProbe: probe.indexOf(sChosen.id) !== -1
      });
      topicUsed[sChosen.id] = 1;
      if (TOPIC[sChosen.id].isCore) {
        chapterUsed[TOPIC[sChosen.id].chap] = (chapterUsed[TOPIC[sChosen.id].chap] || 0) + 1;
      }
      shortPicked++;
    }

    /* 先把 probeQuota 个名额留给根因候选 */
    var probePicked = 0;
    /* 卷面构成：选择题、填空题各有固定名额。
       原先按「这个知识点里还有没有选择题」逐轮去猜，最后一两格容易翻车——
       选择已经满额，却挑到一个只剩选择题的知识点，出成 11 选择 + 5 填空。
       改成先算清楚这一卷要几道选择、几道填空，再按题型名额一格一格发。 */
    var choiceWant = (opts.choiceQuota != null)
      ? Math.min(opts.choiceQuota, objCount)
      : Math.round(objCount * 0.45);

    /* 池子里现成的选择题、填空题各有多少道，决定名额能不能给满 */
    var availChoice = 0, availNum = 0;
    pool.forEach(function (p) {
      objQsOf(p.id).forEach(function (q) {
        if (pickedQids[q.id]) return;
        if (q.type === 'choice') availChoice++; else availNum++;
      });
    });
    var numTarget = Math.min(objCount - choiceWant, availNum);
    var choiceTarget = objCount - numTarget;
    if (choiceTarget > availChoice) {
      /* 选择题本身也不够，只能按实际数量收口 */
      choiceTarget = availChoice;
      numTarget = Math.min(objCount - choiceTarget, availNum);
    }
    /* 槽位是按难度从易到难排好的。选择题如果全塞在前面，就等于「选择全简单、
       填空全难」，孩子做填空题时一直在敲最难的答案。这里按比例交错发牌，
       让两种题型在难度上摊开（Bresenham 式均匀分配，正好发满 choiceTarget 个）。 */
    var typeSlots = [];
    for (var ti = 0; ti < objCount; ti++) {
      var hi = Math.floor((ti + 0.5) * choiceTarget / objCount);
      var lo = Math.floor((ti - 0.5) * choiceTarget / objCount);
      typeSlots.push(hi > lo ? 'choice' : 'numeric');
    }
    var choicePicked = 0;
    for (var s = 0; s < slots.length; s++) {
      var slotDiff = slots[s];
      var wantType = typeSlots[s];
      var cands = poolForSlot(slotDiff);

      if (probeQuota > probePicked && probe.length) {
        var onlyProbe = cands.filter(function (p) { return probe.indexOf(p.id) !== -1; });
        if (onlyProbe.length) {
          cands = onlyProbe;
        }
      }
      if (!cands.length) {
        /* 章节配额放开了再试一次 */
        cands = pool.filter(function (p) {
          if (!isBn && topicUsed[p.id]) return false;
          return objQsOf(p.id).some(function (q) { return !pickedQids[q.id]; });
        });
      }
      if (!cands.length && isBn) {
        /* 压轴题库抽干了，放开难度限制兜底（正常不会走到这里） */
        cands = pool.filter(function (p) {
          return objQsOf(p.id, true).some(function (q) { return !pickedQids[q.id]; });
        });
      }
      if (!cands.length) break;

      /* 这一格要选择题就只在还有选择题的知识点里挑，要填空就只在还有填空题的里挑。
         优先挑「同题型、同难度都还有」的知识点，难度才不会因为题型分配而跑偏；
         实在没有就退到「同题型、任意难度」，再没有才放开题型。 */
      if (wantType) {
        var exactType = cands.filter(function (p) {
          return objQsOf(p.id).some(function (q) {
            return q.type === wantType && q.difficulty === slotDiff && !pickedQids[q.id];
          });
        });
        var anyType = cands.filter(function (p) {
          return objQsOf(p.id).some(function (q) {
            return q.type === wantType && !pickedQids[q.id];
          });
        });
        if (exactType.length) cands = exactType;
        else if (anyType.length) cands = anyType;
        else wantType = '';
      }

      var chosen = pickWeighted(cands);
      if (!chosen) break;

      /* 选该知识点下最贴近目标难度、且没做过的题 */
      var qs = objQsOf(chosen.id).filter(function (q) {
        return !usedQids[q.id] && !pickedQids[q.id];
      });
      if (!qs.length) qs = objQsOf(chosen.id).filter(function (q) { return !pickedQids[q.id]; });
      if (!qs.length) qs = objQsOf(chosen.id, true).filter(function (q) { return !pickedQids[q.id]; });
      if (!qs.length) { topicUsed[chosen.id] = 1; continue; }
      if (wantType) {
        var onlyType = qs.filter(function (q) { return q.type === wantType; });
        if (onlyType.length) qs = onlyType;
      }
      qs.sort(function (a, b) {
        return Math.abs(DIFF_RANK[a.difficulty] - DIFF_RANK[slotDiff]) -
               Math.abs(DIFF_RANK[b.difficulty] - DIFF_RANK[slotDiff]);
      });
      var q = qs[0];
      if (!q) { topicUsed[chosen.id] = 1; continue; }
      if (q.type === 'choice') choicePicked++;

      pickedQids[q.id] = 1;
      picked.push({
        qid: q.id,
        topicId: chosen.id,
        difficulty: q.difficulty,
        type: q.type,
        points: q.points || 0,
        isProbe: probe.indexOf(chosen.id) !== -1
      });
      topicUsed[chosen.id] = 1;
      if (TOPIC[chosen.id].isCore) {
        chapterUsed[TOPIC[chosen.id].chap] = (chapterUsed[TOPIC[chosen.id].chap] || 0) + 1;
      }
      if (probe.indexOf(chosen.id) !== -1) probePicked++;
    }

    /* 6b. 卷面分值
       原题库里选择、填空没有分值，卷头就会空着「共 X 分」，看着像没做完。
       按中考惯例选择、填空各 3 分；解答题自带分值，整卷再缩放到 120 分，
       和青岛这套周测卷的满分对齐（10×3 + 6×3 + 72 = 120）。 */
    picked.forEach(function (p) {
      if (!p.points) p.points = DEFAULT_POINTS[p.type] || 0;
    });
    if (isBn && shortPicked === 8) rebalancePoints(picked, 120);

    /* 7. 分卷排版：选择 → 填空 → 解答 */
    picked.sort(function (a, b) {
      var sa = TYPE_SECTION[a.type] || 0, sb = TYPE_SECTION[b.type] || 0;
      if (sa !== sb) return sa - sb;
      return TOPIC[a.topicId].order - TOPIC[b.topicId].order;
    });

    var sections = [
      { key: 'choice', title: '选择题', hint: '每题只有一个正确答案', items: [] },
      { key: 'numeric', title: '填空题', hint: '把结果写在横线上', items: [] },
      { key: 'short', title: '解答题', hint: '写出必要的解题过程', items: [] }
    ];
    var secMap = { choice: 0, numeric: 1, short: 2, self: 2 };
    var no = 0;
    picked.forEach(function (p) {
      no++;
      p.no = no;
      sections[secMap[p.type] || 0].items.push(p);
    });

    return {
      seed: opts.seed || 20261021,
      mode: mode,
      tier: tier,
      bnUnits: bnUnits.slice(),
      sections: sections.filter(function (x) { return x.items.length; }),
      items: picked,
      count: picked.length,
      shortCount: shortPicked,
      probeCount: probePicked,
      requested: count
    };
  }

  /* ---------- 诊断 ---------- */
  /**
   * test: {items:[{qid,topicId}], wrong:[qid]}
   * state: {topicStats:{id:{okStreak,lastWrongAt,lastOkAt}}}
   */
  function diagnose(test, state) {
    state = state || {};
    var topicStats = state.topicStats || {};
    var wrongSet = {};
    (test.wrong || []).forEach(function (id) { wrongSet[id] = 1; });

    /* 1. 直接薄弱点 */
    var directMap = {};
    test.items.forEach(function (it) {
      if (!wrongSet[it.qid]) return;
      if (!directMap[it.topicId]) {
        directMap[it.topicId] = { topicId: it.topicId, wrongQids: [], items: [] };
      }
      directMap[it.topicId].wrongQids.push(it.qid);
      directMap[it.topicId].items.push(it);
    });
    var direct = Object.keys(directMap).map(function (id) {
      var t = TOPIC[id];
      return {
        topicId: id,
        name: t.name,
        chapter: t.chapter,
        chapterShort: chapterShort(t.chap),
        grade: t.grade,
        gradeLabel: gradeLabel(t.grade),
        domain: t.domain,
        wrongQids: directMap[id].wrongQids,
        count: directMap[id].wrongQids.length
      };
    }).sort(function (a, b) { return b.count - a.count; });

    /* 2. 根因候选：沿先修边向上 BFS */
    var rootScore = {};   // topicId -> {score, support:[], depthMin}
    var chainByTopic = {}; // 错题知识点 -> 推荐链

    direct.forEach(function (d) {
      var best = [];
      var queue = [{ id: d.topicId, depth: 0, hard: 0, path: [d.topicId] }];
      var visited = {};
      visited[d.topicId] = 0;

      while (queue.length) {
        var cur = queue.shift();
        if (cur.depth > 6) continue;
        (PRE_OF[cur.id] || []).forEach(function (e) {
          if (visited[e.id] !== undefined && visited[e.id] <= cur.depth + 1) return;
          visited[e.id] = cur.depth + 1;
          var hardCount = cur.hard + (e.strength === 'hard' ? 1 : 0);
          var depth = cur.depth + 1;
          var path = cur.path.concat([e.id]);
          queue.push({ id: e.id, depth: depth, hard: hardCount, path: path });

          var t = TOPIC[e.id];
          if (!t) return;

          /* 已被历史证明掌握 → 排除 */
          var st = topicStats[e.id];
          if (st && st.okStreak >= 1 && (!st.lastWrongAt || st.lastOkAt >= st.lastWrongAt)) return;

          var allHard = hardCount === depth;
          var base = allHard ? 1.0 : (hardCount / depth >= 0.5 ? 0.75 : 0.45);
          var depthFactor = 1 / (1 + depth * 0.75);
          var corePenalty = t.isCore ? 0.45 : 1.0;
          var score = base * depthFactor * corePenalty;

          best.push({ id: e.id, score: score, depth: depth, allHard: allHard, path: path });
        });
      }

      /* 每个错题取前 3 个根因候选 */
      best.sort(function (a, b) { return b.score - a.score; });
      var top = best.slice(0, 3);
      chainByTopic[d.topicId] = top;

      top.forEach(function (b) {
        if (!rootScore[b.id]) {
          rootScore[b.id] = { score: 0, support: [], depthMin: 99, path: b.path };
        }
        rootScore[b.id].score += b.score;
        rootScore[b.id].support.push(d.topicId);
        rootScore[b.id].depthMin = Math.min(rootScore[b.id].depthMin, b.depth);
      });
    });

    var roots = Object.keys(rootScore).map(function (id) {
      var r = rootScore[id];
      var t = TOPIC[id];
      var conf = r.score >= 0.85 && r.support.length >= 2 ? '高'
               : r.score >= 0.45 ? '中' : '低';
      return {
        topicId: id,
        name: t.name,
        chapter: t.chapter,
        chapterShort: chapterShort(t.chap),
        grade: t.grade,
        gradeLabel: gradeLabel(t.grade),
        isCore: t.isCore,
        score: Math.round(r.score * 100) / 100,
        confidence: conf,
        support: r.support,
        downstream: downstreamCount(id),
        chain: chainTo(id).concat()
      };
    }).sort(function (a, b) { return b.score - a.score; });

    /* 3. 每条错题的完整归因链（用假设路径本身，不追到最底层） */
    var chains = direct.map(function (d) {
      var tops = chainByTopic[d.topicId] || [];
      var main = tops[0];
      /* main.path 是 [错题点, 先修, ...]，反过来就是 根因 → 错题点 */
      var full = main ? main.path.slice().reverse() : [d.topicId];
      /* 去重 */
      var seen = {};
      var path = full.filter(function (id) {
        if (seen[id]) return false;
        seen[id] = 1;
        return true;
      });
      /* 太长就只留最近几环 */
      if (path.length > 6) path = path.slice(-6);
      path = path.map(function (id) {
        var t = TOPIC[id];
        return {
          id: id,
          name: t.name,
          gradeLabel: gradeLabel(t.grade),
          chapterShort: chapterShort(t.chap),
          isCore: t.isCore
        };
      });
      return {
        topicId: d.topicId,
        name: d.name,
        path: path,
        rootId: main ? main.id : null,
        confidence: main ? (main.score >= 0.6 ? '高' : main.score >= 0.35 ? '中' : '低') : '—'
      };
    });

    /* 4. 章节聚合 */
    var chAgg = {};
    test.items.forEach(function (it) {
      var t = TOPIC[it.topicId];
      if (!t) return;
      var k = t.chap;
      if (!chAgg[k]) chAgg[k] = { chapter: k, short: chapterShort(k), total: 0, wrong: 0 };
      chAgg[k].total++;
      if (wrongSet[it.qid]) chAgg[k].wrong++;
    });
    var chapters = Object.keys(chAgg).map(function (k) {
      var c = chAgg[k];
      c.rate = c.total ? Math.round((c.total - c.wrong) / c.total * 100) : 100;
      return c;
    }).sort(function (a, b) { return a.rate - b.rate; });

    /* 5. 总览 */
    var total = test.items.length;
    var wrongN = (test.wrong || []).length;
    var summary = {
      total: total,
      wrong: wrongN,
      right: total - wrongN,
      accuracy: total ? Math.round((total - wrongN) / total * 100) : 0,
      weakTopics: direct.length,
      rootCandidates: roots.length,
      probeCount: (test.items || []).filter(function (x) { return x.isProbe; }).length
    };

    return {
      summary: summary,
      direct: direct,
      roots: roots,
      chains: chains,
      chapters: chapters
    };
  }

  /* ---------- 讲解卡 ---------- */
  function buildLesson(topicId, test) {
    var t = TOPIC[topicId];
    if (!t) return null;

    var wrongItems = [];
    if (test) {
      var wrongSet = {};
      (test.wrong || []).forEach(function (id) { wrongSet[id] = 1; });
      (test.items || []).forEach(function (it) {
        if (it.topicId === topicId && wrongSet[it.qid]) {
          var q = QUESTION[it.qid];
          if (q) wrongItems.push({ no: it.no, question: q });
        }
      });
    }

    /* 同类练习：没在本次出现过的题，且不和例题重复 */
    var usedInTest = {};
    if (test) (test.items || []).forEach(function (it) { usedInTest[it.qid] = 1; });

    var diagText = (t.diagnostic_question && t.diagnostic_question.question) || '';
    function norm(s) {
      return String(s || '').replace(/[\s，。、；：（）()【】=＝,.]/g, '');
    }
    /* 数学题的"骨架"：去掉汉字只留算式，用来判断两道题是不是同一道 */
    function skeleton(s) {
      return String(s || '').replace(/[\u4e00-\u9fa5]/g, '').replace(/\s/g, '');
    }
    function tooSimilar(a, b) {
      var x = norm(a), y = norm(b);
      if (x && y) {
        var k = Math.min(12, x.length, y.length);
        if (k >= 6 && x.slice(0, k) === y.slice(0, k)) return true;
      }
      var sx = skeleton(a), sy = skeleton(b);
      if (sx.length >= 6 && sy.length >= 6) {
        if (sx.indexOf(sy) !== -1 || sy.indexOf(sx) !== -1) return true;
      }
      return false;
    }

    var practice = (Q_OF[topicId] || [])
      .filter(function (q) { return !usedInTest[q.id]; })
      .filter(function (q) { return !tooSimilar(q.prompt, diagText); })
      .slice(0, 2);

    /* 先修链：只保留最近几环，避免一路追到一年级 */
    var chainIds = chainTo(topicId);
    if (chainIds.length > 6) chainIds = chainIds.slice(-6);
    var chain = chainIds.map(function (id) {
      var x = TOPIC[id];
      return {
        id: id,
        name: x.name,
        gradeLabel: gradeLabel(x.grade),
        chapterShort: chapterShort(x.chap),
        isCore: x.isCore
      };
    });

    return {
      topicId: topicId,
      name: t.name,
      domain: t.domain,
      chapter: t.chapter,
      chapterShort: chapterShort(t.chap),
      gradeLabel: gradeLabel(t.grade),
      semesterLabel: semesterLabel(t),
      type: t.type,
      description: t.description,
      mastery: t.mastery_criteria || [],
      diagnostic: t.diagnostic_question,
      chain: chain,
      downstream: downstreamCount(topicId),
      wrongItems: wrongItems,
      practice: practice
    };
  }

  function buildLessons(topicIds, test) {
    return (topicIds || []).map(function (id) { return buildLesson(id, test); })
      .filter(Boolean);
  }

  /* ---------- 对外 ---------- */
  root.Engine = {
    data: D,
    topic: function (id) { return TOPIC[id]; },
    question: function (id) { return QUESTION[id]; },
    questionsOf: function (id) { return Q_OF[id] || []; },
    prereqsOf: function (id) { return PRE_OF[id] || []; },
    dependentsOf: function (id) { return DEP_OF[id] || []; },
    coreTopics: coreTopics,
    chapterShort: chapterShort,
    gradeLabel: gradeLabel,
    bnLabel: bnLabel,
    semesterLabel: semesterLabel,
    chainTo: chainTo,
    downstreamCount: downstreamCount,
    generatePaper: generatePaper,
    diagnose: diagnose,
    buildLesson: buildLesson,
    buildLessons: buildLessons,
    /* 北师大版（2026 新版）九上 */
    bnChapters: function () { return D.bnChapters || []; },
    bnTopics: function (unit, tier) {
      var key = (tier === 'bn2') ? 'bn2Unit' : 'bnUnit';
      return D.topics.filter(function (t) {
        return t[key] && (!unit || t[key] === unit);
      });
    },
    /* 北师大版九下 */
    bn2Chapters: function () { return D.bn2Chapters || []; }
  };
})(typeof window !== 'undefined' ? window : globalThis);
