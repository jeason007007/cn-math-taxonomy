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
    { href: 'quiz.html', label: '做题' },
    { href: 'grade.html', label: '批改' },
    { href: 'report.html', label: '盲点报告' },
    { href: 'teach.html', label: '讲解' }
  ];

  /* 手机底部标签栏：只留家长真正会用的五个入口 */
  var TABS = [
    { href: 'index.html', label: '总览', match: ['index.html'] },
    { href: 'paper.html', label: '出卷', match: ['paper.html'] },
    { href: 'quiz.html', label: '做题', match: ['quiz.html'] },
    { href: 'report.html', label: '报告', match: ['report.html', 'grade.html'] },
    { href: 'teach.html', label: '讲解', match: ['teach.html'] }
  ];

  /* 学科：靠路径判断。math/ 和 physics/ 各放一份 ui.js，两份内容保持一致，
     只有这里按当前目录自动认出是哪一科。 */
  var SUBJ = (function () {
    try {
      return /[/\\]physics[/\\]/.test(location.pathname) ? 'physics' : 'math';
    } catch (e) {
      return 'math';
    }
  })();
  var SUBJ_CN = { math: '数学', physics: '物理' };
  var SUBJ_HREF = { math: '../math/index.html', physics: '../physics/index.html' };

  function nav(current) {
    var items = NAV.map(function (n) {
      var on = n.href === current ? ' on' : '';
      return '<a class="nav-item' + on + '" href="' + n.href + '">' + n.label + '</a>';
    }).join('');
    var sw = '<span class="nav-subj">' +
      ['math', 'physics'].map(function (k) {
        return '<a class="' + (k === SUBJ ? 'on' : '') + '" href="' + SUBJ_HREF[k] + '">' +
          SUBJ_CN[k] + '</a>';
      }).join('') + '</span>';
    return '<div class="nav no-print"><div class="nav-inner">' +
      '<span class="nav-brand">初三' + SUBJ_CN[SUBJ] + ' · 盲点诊断</span>' + items + sw +
      '</div></div>';
  }

  function tabbar(current) {
    var items = TABS.map(function (t) {
      var on = (t.match || [t.href]).indexOf(current) !== -1 ? ' on' : '';
      return '<a class="' + on.trim() + '" href="' + t.href + '">' + t.label + '</a>';
    }).join('');
    var other = SUBJ === 'math' ? 'physics' : 'math';
    return '<div class="m-tabbar no-print">' + items +
      '<a class="subj" href="' + SUBJ_HREF[other] + '">' + SUBJ_CN[other] + '</a></div>';
  }

  function mountNav(current) {
    var holder = document.createElement('div');
    holder.innerHTML = nav(current) + tabbar(current);
    while (holder.firstChild) {
      document.body.insertBefore(holder.firstChild, document.body.firstChild);
    }
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

  /* 题图：内联 SVG，已经过审核的可信内容，不走 esc */
  function figHTML(q) {
    if (!q || !q.fig) return '';
    return '<div class="q-fig">' + q.fig + '</div>';
  }

  /* 试卷上的完整题目 */
  function questionHTML(q, no) {
    /* 解答题的题面用 \n 分行（小问、素材、条件各占一行），
       这里必须转成 <br>，否则整道题挤成一大段，读起来很费劲。 */
    var prompt = esc(q.prompt).replace(/\n/g, '<br>') +
      (q.type === 'choice' ? '　（　　）' : '');
    return '<div class="q" data-qid="' + esc(q.id) + '">' +
      '<span class="q-no">' + no + '.</span>' +
      '<p class="q-prompt">' + prompt + '</p>' +
      figHTML(q) +
      choicesHTML(q) +
      answerAreaHTML(q.type, q.space) +
      '</div>';
  }

  /* 复制一段文字到剪贴板，失败时退回选中提示 */
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { return true; })
        .catch(function () { return fallbackCopy(text); });
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function fallbackCopy(text) {
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (e) {
      return false;
    }
  }

  /* 手机判断：给「建议用电脑打印」这类提示用 */
  function isMobile() {
    return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
      (window.matchMedia && window.matchMedia('(max-width: 760px)').matches);
  }

  root.UI = {
    esc: esc, el: el, qs: qs, nav: nav, tabbar: tabbar, mountNav: mountNav, toast: toast,
    fmtDate: fmtDate, fmtDay: fmtDay, accuracyClass: accuracyClass,
    copyText: copyText, isMobile: isMobile, figHTML: figHTML,
    choicesHTML: choicesHTML, answerAreaHTML: answerAreaHTML, questionHTML: questionHTML
  };
})(typeof window !== 'undefined' ? window : globalThis);
