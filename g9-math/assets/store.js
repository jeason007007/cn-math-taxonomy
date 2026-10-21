/* 状态管理：localStorage 单档案，支持导出/导入 */
(function (root) {
  'use strict';

  var KEY = 'g9math.v1';
  var E = root.Engine;

  var state = null;

  function blank() {
    return {
      v: 1,
      createdAt: new Date().toISOString(),
      student: '',
      tests: [],
      topicStats: {},
      usedQids: {},
      lessons: {},
      paperOpts: {
        semesters: ['上', '下'],
        count: 20,
        ratio: { basic: 0.4, standard: 0.4, advanced: 0.2 },
        mode: 'normal'
      }
    };
  }

  function load() {
    if (state) return state;
    try {
      var raw = root.localStorage && root.localStorage.getItem(KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && parsed.v === 1) {
          state = parsed;
          return state;
        }
      }
    } catch (e) {
      console.warn('读取本地数据失败，使用空白档案', e);
    }
    state = blank();
    return state;
  }

  function save() {
    try {
      root.localStorage.setItem(KEY, JSON.stringify(state));
      return true;
    } catch (e) {
      console.error('保存失败（可能是浏览器隐私模式或空间不足）', e);
      return false;
    }
  }

  function reset() {
    state = blank();
    save();
  }

  function newId() {
    return 't' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  }

  /* 记录一张卷（出卷时创建，批改后标记 done） */
  function createTest(paper, scopeLabel) {
    load();
    var t = {
      id: newId(),
      at: new Date().toISOString(),
      scopeLabel: scopeLabel || '',
      mode: paper.mode,
      seed: paper.seed,
      items: paper.items.map(function (it) {
        return {
          qid: it.qid,
          topicId: it.topicId,
          no: it.no,
          type: it.type,
          difficulty: it.difficulty,
          points: it.points || 0,
          isProbe: !!it.isProbe
        };
      }),
      wrong: [],
      done: false
    };
    state.tests.unshift(t);
    save();
    return t;
  }

  function getTest(id) {
    load();
    for (var i = 0; i < state.tests.length; i++) {
      if (state.tests[i].id === id) return state.tests[i];
    }
    return null;
  }

  function currentTest() {
    load();
    for (var i = 0; i < state.tests.length; i++) {
      if (!state.tests[i].done) return state.tests[i];
    }
    return null;
  }

  /* 从全部已完成测试重算统计（重批、改判都不会重复累计） */
  function recomputeStats() {
    load();
    var stats = {};
    var used = {};
    /* 按时间从旧到新，保证 okStreak / lastWrongAt 正确 */
    var ordered = state.tests.slice().reverse();
    ordered.forEach(function (t) {
      if (!t.done) return;
      var wrongSet = {};
      (t.wrong || []).forEach(function (q) { wrongSet[q] = 1; });
      var at = t.gradedAt || t.at;
      t.items.forEach(function (it) {
        var st = stats[it.topicId] || {
          asked: 0, wrong: 0, okStreak: 0, lastAskedAt: null, lastOkAt: null, lastWrongAt: null
        };
        st.asked++;
        st.lastAskedAt = at;
        if (wrongSet[it.qid]) {
          st.wrong++;
          st.okStreak = 0;
          st.lastWrongAt = at;
        } else {
          st.okStreak++;
          st.lastOkAt = at;
        }
        stats[it.topicId] = st;
        used[it.qid] = 1;
      });
    });
    state.topicStats = stats;
    state.usedQids = used;
  }

  /* 提交批改结果 */
  function submitGrade(testId, wrongQids) {
    load();
    var t = getTest(testId);
    if (!t) return null;
    t.wrong = wrongQids.slice();
    t.done = true;
    t.gradedAt = new Date().toISOString();

    recomputeStats();
    save();
    return t;
  }

  /* 累计盲点：按 错误次数 / 最近状态 排序 */
  function blindSpots() {
    load();
    var out = [];
    Object.keys(state.topicStats).forEach(function (id) {
      var st = state.topicStats[id];
      var t = E.topic(id);
      if (!t) return;
      var isWeak = st.lastWrongAt && (!st.lastOkAt || st.lastWrongAt > st.lastOkAt);
      if (!isWeak) return;
      out.push({
        topicId: id,
        name: t.name,
        gradeLabel: E.gradeLabel(t.grade),
        chapterShort: E.chapterShort(t.chapter),
        isCore: t.isCore,
        wrong: st.wrong,
        asked: st.asked,
        lastWrongAt: st.lastWrongAt,
        downstream: E.downstreamCount(id)
      });
    });
    out.sort(function (a, b) {
      if (a.isCore !== b.isCore) return a.isCore ? 1 : -1; // 先修点优先
      if (b.wrong !== a.wrong) return b.wrong - a.wrong;
      return b.downstream - a.downstream;
    });
    return out;
  }

  /* 下一张卷要探测的根因候选 */
  function probeTargets() {
    load();
    var blind = blindSpots();
    var ids = [];
    blind.forEach(function (b) {
      if (!b.isCore && ids.indexOf(b.topicId) === -1) ids.push(b.topicId);
    });
    /* 不够就补初三薄弱点 */
    blind.forEach(function (b) {
      if (ids.length >= 6) return;
      if (ids.indexOf(b.topicId) === -1) ids.push(b.topicId);
    });
    return ids.slice(0, 6);
  }

  function markLessonSeen(topicId) {
    load();
    state.lessons[topicId] = new Date().toISOString();
    save();
  }

  function exportJSON() {
    load();
    return JSON.stringify(state, null, 2);
  }

  function importJSON(text) {
    var parsed = JSON.parse(text);
    if (!parsed || parsed.v !== 1 || !Array.isArray(parsed.tests)) {
      throw new Error('文件格式不对');
    }
    state = parsed;
    recomputeStats();
    save();
    return state;
  }

  function stats() {
    load();
    var done = state.tests.filter(function (t) { return t.done; });
    var totalQ = 0, totalWrong = 0;
    done.forEach(function (t) {
      totalQ += t.items.length;
      totalWrong += t.wrong.length;
    });
    return {
      testCount: done.length,
      totalQ: totalQ,
      totalWrong: totalWrong,
      accuracy: totalQ ? Math.round((totalQ - totalWrong) / totalQ * 100) : 0,
      blindCount: blindSpots().length,
      qUsed: Object.keys(state.usedQids).length,
      qTotal: E.data.meta.questionCount
    };
  }

  root.Store = {
    KEY: KEY,
    get state() { return load(); },
    load: load,
    save: save,
    reset: reset,
    createTest: createTest,
    getTest: getTest,
    currentTest: currentTest,
    submitGrade: submitGrade,
    recomputeStats: recomputeStats,
    blindSpots: blindSpots,
    probeTargets: probeTargets,
    markLessonSeen: markLessonSeen,
    exportJSON: exportJSON,
    importJSON: importJSON,
    stats: stats
  };
})(typeof window !== 'undefined' ? window : globalThis);
