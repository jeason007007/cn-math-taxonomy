# -*- coding: utf-8 -*-
"""
页面冒烟测试：给每个页面注入错误捕获，用 headless Chrome 打开，
把 window.onerror / console.error 和关键元素数量写进 <title>，再 dump-dom 读回来。

用法:
    python tests/check_pages.py
"""
import os
import re
import subprocess
import sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGES = ["index.html", "paper.html", "quiz.html", "grade.html", "report.html", "teach.html"]

HEAD = """<script>
window.__err = [];
window.addEventListener('error', function (e) {
  window.__err.push('ERR: ' + (e.message || e.error));
}, true);
(function () {
  var ce = console.error;
  console.error = function () {
    window.__err.push('CONSOLE: ' + Array.prototype.join.call(arguments, ' '));
    ce.apply(console, arguments);
  };
})();
</script>"""

TAIL = """<script>
function __count() {
  return {
    item: document.querySelectorAll('.student-paper .q').length,
    fig: document.querySelectorAll('.q-fig svg, .fig svg').length,
    card: document.querySelectorAll('.t-card, .topic, .chapter').length,
    c: document.querySelectorAll('.student-paper .sec-choice .q').length,
    n: document.querySelectorAll('.student-paper .sec-numeric .q').length,
    s: document.querySelectorAll('.student-paper .sec-short .q').length
  };
}
function __report(tag) {
  var e = window.__err || [];
  var n = __count();
  document.title = 'ERR=' + e.length + ' | ' + e.slice(0, 3).join(' ;; ') +
    ' | ' + tag + ' item=' + n.item + ' fig=' + n.fig + ' card=' + n.card +
    ' c/n/s=' + n.c + '/' + n.n + '/' + n.s;
}
setTimeout(function () {
  /* 出卷页要先点一下「生成」才有内容 */
  var b = document.getElementById('btnGen');
  if (b) b.click();
  setTimeout(function () {
    /* 出卷页再切到「北师大九下」这一档，确认三档都能出卷 */
    var dn = document.querySelector('[data-diff="bn2"]');
    if (dn) {
      dn.click();
      var b2 = document.getElementById('btnGen');
      if (b2) b2.click();
      setTimeout(function () { __report('bn2'); }, 1500);
    } else {
      __report('default');
    }
  }, 1500);
}, 900);
</script>"""


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = 0
    for page in PAGES:
        src = os.path.join(root, page)
        if not os.path.exists(src):
            print("  --   %-12s 不存在" % page)
            continue
        html = open(src, encoding="utf-8").read()
        html = html.replace("</head>", HEAD + "</head>", 1)
        html = html.replace("</body>", TAIL + "</body>", 1)
        tmp = os.path.join(root, "_chk_" + page)
        open(tmp, "w", encoding="utf-8").write(html)
        try:
            out = subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=20000",
                 "--dump-dom", "file:///" + tmp.replace("\\", "/")],
                capture_output=True, text=True, timeout=90).stdout
        finally:
            os.remove(tmp)
        m = re.search(r"<title>([^<]*)</title>", out)
        info = m.group(1) if m else "(no title)"
        err = re.match(r"ERR=(\d+)", info)
        nerr = int(err.group(1)) if err else -1
        if nerr == 0:
            print("  ok   %-12s %s" % (page, info))
        else:
            bad += 1
            print("  FAIL %-12s %s" % (page, info))
    print("\n%s %d 个页面有问题" % ("✓" if bad == 0 else "✗", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
