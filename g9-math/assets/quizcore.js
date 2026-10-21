/* 线上做题的判分工具
 * 只处理客观题：选择题比对选项字母，填空题比对数值。
 *
 * 设计取向：宁可漏判「错」，也不要把「对」判成「错」。
 * 诊断工具最怕制造假盲点——孩子明明会，却因为写法不同被记一笔，
 * 后面就会浪费时间去补一个根本不存在的洞。所以数值按「多重集」比较，
 * 顺序、写法、全角半角都不计较。
 */
(function (root) {
  'use strict';

  /* 全角转半角 + 统一各种分隔符 */
  function norm(s) {
    return String(s == null ? '' : s)
      .replace(/[\uFF01-\uFF5E]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
      })
      .replace(/[，、;；]/g, ',')
      .replace(/[（]/g, '(').replace(/[）]/g, ')')
      .replace(/[－—–]/g, '-')
      .replace(/\s+/g, '')
      .toLowerCase();
  }

  /* 解析单个数值：整数、小数、分数、带正负号的分数 */
  function parseVal(s) {
    if (!s) return null;
    var t = s.replace(/^[a-z]\s*=/, '');          // 去掉 x= / m= 这类前缀
    t = t.replace(/^\+/, '');
    var frac = /^(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)$/.exec(t);
    if (frac) {
      var den = parseFloat(frac[2]);
      if (den === 0) return null;
      return parseFloat(frac[1]) / den;
    }
    if (/^-?\d+(?:\.\d+)?$/.test(t)) return parseFloat(t);
    return null;
  }

  function splitVals(s) {
    var t = norm(s);
    var parts = t.split(',');
    if (parts.length === 1) parts = t.split(/[\s]+/);
    return parts.filter(function (x) { return x !== ''; });
  }

  function sameVal(a, b) {
    var x = parseVal(a), y = parseVal(b);
    if (x === null || y === null) return a === b;
    /* 容差只用来吸收浮点误差（1/2 与 0.5），不放宽到「近似值算对」 */
    return Math.abs(x - y) < 1e-9;
  }

  /* 多重集比较：答案里的每个值都要在作答里找到唯一对应 */
  function checkNumeric(input, answer) {
    var u = splitVals(input);
    var a = splitVals(answer);
    if (!u.length) return false;
    if (u.length !== a.length) return false;
    var used = u.map(function () { return false; });
    for (var i = 0; i < a.length; i++) {
      var hit = -1;
      for (var j = 0; j < u.length; j++) {
        if (!used[j] && sameVal(u[j], a[i])) { hit = j; break; }
      }
      if (hit === -1) return false;
      used[hit] = true;
    }
    return true;
  }

  function checkChoice(picked, answer) {
    if (!picked) return false;
    return norm(picked) === norm(answer);
  }

  /* 客观题判分；解答题（short / self）线上不判，返回 null */
  function isObjective(q) {
    return q && (q.type === 'choice' || q.type === 'numeric');
  }

  function check(q, picked) {
    if (!isObjective(q)) return null;
    if (q.type === 'choice') return checkChoice(picked, q.answer);
    return checkNumeric(picked, q.answer);
  }

  /* 给家长看的正确答案 */
  function answerText(q) {
    if (!q) return '';
    if (q.type === 'choice') {
      var c = (q.choices || []).filter(function (x) { return x.key === q.answer; })[0];
      return q.answer + (c ? '. ' + c.text : '');
    }
    return String(q.answer);
  }

  root.QuizCore = {
    norm: norm,
    parseVal: parseVal,
    splitVals: splitVals,
    checkNumeric: checkNumeric,
    checkChoice: checkChoice,
    isObjective: isObjective,
    check: check,
    answerText: answerText
  };
})(typeof window !== 'undefined' ? window : globalThis);
