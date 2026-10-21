/* 共用 UI 工具 */
(function (root) {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* 脚本出错时直接显示出来，避免页面静默空白 */
  if (typeof document !== 'undefined') {
    root.addEventListener('error', function (e) {
      var d = document.createElement('div');
      d.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#B91C1C;color:#fff;' +
        'padding:10px 16px;z-index:99999;font-size:13px;font-family:monospace';
      d.textContent = '脚本错误：' + (e.message || e.error) +
        (e.filename ? ' @ ' + e.filename.split('/').pop() + ':' + e.lineno : '');
      document.body.appendChild(d);
    });
  }

  function el(id) { return document.getElementById(id); }

  function qs(name, def) {
    var m = new RegExp('[?&]' + name + '=([^&]*)').exec(location.search);
    return m ? decodeURIComponent(m[1]) : (def === undefined ? null : def);
  }

  function fmtDate(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    var p = function (n) { return n < 10 ? '0' + n : n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
           ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function fmtDay(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    var p = function (n) { return n < 10 ? '0' + n : n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }

  var NAV = [
    { href: 'index.html', label: '总览' },
    { href: 'paper.html', label: '出卷' },
    { href: 'grade.html', label: '批改' },
    { href: 'report.html', label: '盲点报告' },
    { href: 'teach.html', label: '讲解' }
  ];

  function nav(current) {
    var items = NAV.map(function (n) {
      var on = n.href === current ? ' on' : '';
      return '<a class="nav-item' + on + '" href="' + n.href + '">' + n.label + '</a>';
    }).join('');
    return '<div class="nav no-print"><div class="nav-inner">' +
      '<span class="nav-brand">初三数学 · 盲点诊断</span>' + items +
      '</div></div>';
  }

  function mountNav(current) {
    var holder = document.createElement('div');
    holder.innerHTML = nav(current);
    document.body.insertBefore(holder.firstChild, document.body.firstChild);
  }

  function toast(msg, ms) {
    var d = document.createElement('div');
    d.textContent = msg;
    d.style.cssText = 'position:fixed;left:50%;bottom:34px;transform:translateX(-50%);' +
      'background:#1F2328;color:#fff;padding:10px 20px;border-radius:8px;font-size:14px;' +
      'z-index:9999;opacity:0;transition:opacity .18s;box-shadow:0 6px 24px rgba(0,0,0,.18)';
    document.body.appendChild(d);
    requestAnimationFrame(function () { d.style.opacity = '1'; });
    setTimeout(function () {
      d.style.opacity = '0';
      setTimeout(function () { d.remove(); }, 220);
    }, ms || 1800);
  }

  function accuracyClass(p) {
    if (p >= 85) return 'good';
    if (p >= 60) return 'warn';
    return 'bad';
  }

  /* 题目渲染 */
  function choicesHTML(q) {
    if (!q.choices || !q.choices.length) return '';
    /* 选项文字长就竖排，避免挤成两行 */
    var longOpt = q.choices.some(function (c) { return String(c.text).length > 12; });
    var inner = q.choices.map(function (c) {
      return '<span class="c">' + esc(c.key) + '. ' + esc(c.text) + '</span>';
    }).join('');
    return '<div class="q-choices' + (longOpt ? ' vertical' : '') + '">' + inner + '</div>';
  }

  function answerAreaHTML(type, space) {
    if (type === 'short' || type === 'self') {
      var h = space || 200;
      return '<div class="q-box" style="height:' + h + 'pt"></div>';
    }
    if (type === 'choice') return '';
    return '<div class="q-line"></div>';
  }

  /* 试卷上的完整题目 */
  function questionHTML(q, no) {
    var prompt = esc(q.prompt) + (q.type === 'choice' ? '　（　　）' : '');
    return '<div class="q" data-qid="' + esc(q.id) + '">' +
      '<span class="q-no">' + no + '.</span>' +
      '<p class="q-prompt">' + prompt + '</p>' +
      choicesHTML(q) +
      answerAreaHTML(q.type, q.space) +
      '</div>';
  }

  root.UI = {
    esc: esc, el: el, qs: qs, nav: nav, mountNav: mountNav, toast: toast,
    fmtDate: fmtDate, fmtDay: fmtDay, accuracyClass: accuracyClass,
    choicesHTML: choicesHTML, answerAreaHTML: answerAreaHTML, questionHTML: questionHTML
  };
})(typeof window !== 'undefined' ? window : globalThis);
