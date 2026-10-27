# -*- coding: utf-8 -*-
"""
为自编解答题生成题图（内联 SVG，不依赖任何图片文件，打印/离线都能用）

用法:
    python build/make_figs.py            # 生成 data/sh-figs.json
    python build/make_figs.py --preview  # 另存 figs-preview.html 供肉眼检查

坐标一律用屏幕坐标（y 向下）。画图只用手写线条，不用字体图标，
避免在没装字体的机器上变成方块。
"""
import argparse
import json
import math
import os
import sys

INK = "#2b2b2b"
GRAY = "#8b8b8b"
FONT = "system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"


def P(deg, r, cx, cy):
    """极坐标 -> 屏幕坐标。deg 按数学习惯（逆时针为正，0 度朝右）"""
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy - r * math.sin(a))


def L(x1, y1, x2, y2, dash=None, w=None, color=None):
    s = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"' % (x1, y1, x2, y2)
    if dash:
        s += ' stroke-dasharray="%s"' % dash
    if w:
        s += ' stroke-width="%s"' % w
    if color:
        s += ' stroke="%s"' % color
    return s + "/>"


def PL(pts, close=False, dash=None, w=None, color=None, fill=None):
    tag = "polygon" if close else "polyline"
    s = '<%s points="%s"' % (tag, " ".join("%.1f,%.1f" % p for p in pts))
    if dash:
        s += ' stroke-dasharray="%s"' % dash
    if w:
        s += ' stroke-width="%s"' % w
    if color:
        s += ' stroke="%s"' % color
    if fill:
        s += ' fill="%s"' % fill
    return s + "/>"


def CI(cx, cy, r, dash=None):
    s = '<circle cx="%.1f" cy="%.1f" r="%.1f"' % (cx, cy, r)
    if dash:
        s += ' stroke-dasharray="%s"' % dash
    return s + "/>"


def DOT(x, y, r=2.4):
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="none"/>' % (x, y, r, INK)


def T(x, y, s, anchor="middle", size=13, color=INK, bold=False):
    return ('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%d" fill="%s" '
            'stroke="none" font-family="%s"%s>%s</text>'
            % (x, y, anchor, size, color, FONT,
               ' font-weight="600"' if bold else "", s))


def ARC(cx, cy, r, d1, d2):
    x1, y1 = P(d1, r, cx, cy)
    x2, y2 = P(d2, r, cx, cy)
    large = 1 if abs(d2 - d1) > 180 else 0
    sweep = 0 if d2 > d1 else 1
    return ('<path d="M%.1f,%.1f A%.1f,%.1f 0 %d %d %.1f,%.1f" fill="none"/>'
            % (x1, y1, r, r, large, sweep, x2, y2))


def RA(x, y, ux, uy, s=10):
    """直角标记：顶点 (x,y)，两条边方向单位向量 (ux,uy)/(vx,vy)"""
    vx, vy = -uy, ux
    p1 = (x + ux * s, y + uy * s)
    p2 = (x + ux * s + vx * s, y + uy * s + vy * s)
    p3 = (x + vx * s, y + vy * s)
    return PL([p1, p2, p3])


def SVG(w, h, parts, label="题图"):
    return ('<svg class="fig" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
            'role="img" aria-label="%s">'
            '<g fill="none" stroke="%s" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round">%s</g></svg>' % (w, h, label, INK, "".join(parts)))


# ======================= 各题题图 =======================

def f_fence_wall():
    """sh_228_2 靠墙围矩形菜地"""
    p = []
    # 墙
    p.append(L(40, 40, 300, 40, w=7, color=GRAY))
    for x in range(48, 300, 16):
        p.append(L(x, 40, x - 9, 28, color=GRAY, w=1.2))
    # 篱笆（三边）
    p.append(PL([(90, 40), (90, 150), (250, 150), (250, 40)], w=2.2))
    p.append(T(78, 100, "x", anchor="end"))
    p.append(T(262, 100, "x", anchor="start"))
    p.append(T(170, 172, "40 − 2x"))
    p.append(T(170, 22, "墙（长 25 m）", size=12, color=GRAY))
    p.append(DOT(90, 40, 2) + DOT(250, 40, 2))
    return SVG(340, 190, p, "靠墙围矩形菜地")


def f_arch_bridge():
    """sh_236_2 抛物线拱桥"""
    p = []
    cx, top = 170, 60
    sc = 26.0  # 每米像素
    half = 4 * sc
    pts = []
    for i in range(-20, 21):
        xm = i * 0.2
        ym = xm * xm / 4.0
        pts.append((cx + xm * sc, top + ym * sc))
    p.append(PL(pts, w=2.2))
    # 水面
    p.append(L(50, top + half, 292, top + half, w=1.6))
    for x in range(58, 292, 20):
        p.append(L(x, top + half + 6, x + 9, top + half + 6, color="#7aa7d6", w=1.3))
    # 轴
    p.append(L(cx, top - 26, cx, top + half + 16, dash="5 4", color=GRAY))
    p.append(L(50, top + half, 292, top + half, dash="5 4", color=GRAY))
    p.append(T(cx + 12, top - 12, "O"))
    p.append(T(cx, top + half + 26, "8 m", size=12, color=GRAY))
    p.append(T(cx + 10, top + half / 2, "4 m", anchor="start", size=12, color=GRAY))
    p.append(DOT(cx, top))
    return SVG(340, 200, p, "抛物线形拱桥")


def f_parabola_basic():
    """sh_232_1 y=x²-2x-3"""
    p = []
    sx = lambda x: 170 + 36 * x
    sy = lambda y: 112 - 17 * y
    p.append(L(58, sy(0), 302, sy(0), w=1.3))
    p.append(L(sx(0), 26, sx(0), 208, w=1.3))
    p.append(T(300, sy(0) - 8, "x", anchor="end", size=12))
    p.append(T(sx(0) + 10, 34, "y", size=12))
    pts = []
    x = -1.75
    while x <= 3.8:
        pts.append((sx(x), sy(x * x - 2 * x - 3)))
        x += 0.1
    p.append(PL(pts, w=2.2))
    for (x, y, lab, dx, dy) in [(-1, 0, "A", -14, 16), (3, 0, "B", 12, 16),
                                (0, -3, "C", -13, 4), (1, -4, "D", 4, 17)]:
        p.append(DOT(sx(x), sy(y)))
        p.append(T(sx(x) + dx, sy(y) + dy, lab))
    return SVG(340, 226, p, "二次函数图象")


def f_parabola_tri():
    """sh_232_2 抛物线与 △PBC"""
    p = []
    sx = lambda x: 128 + 36 * x
    sy = lambda y: 118 - 15 * y
    p.append(L(44, sy(0), 306, sy(0), w=1.3))
    p.append(L(sx(0), 24, sx(0), 196, w=1.3))
    p.append(T(304, sy(0) - 8, "x", anchor="end", size=12))
    p.append(T(sx(0) + 10, 32, "y", size=12))
    pts = []
    x = -1.8
    while x <= 4.0:
        pts.append((sx(x), sy(x * x - 2 * x - 3)))
        x += 0.1
    p.append(PL(pts, w=2.2))
    # 三角形 P B C（P 取 (4,5)）
    p.append(PL([(sx(4), sy(5)), (sx(3), sy(0)), (sx(0), sy(-3))], close=True,
                w=1.8, color="#c0392b", fill="rgba(192,57,43,.06)"))
    for (x, y, lab, dx, dy) in [(-1, 0, "A", -14, 16), (3, 0, "B", 10, 16),
                                (0, -3, "C", -13, 4), (4, 5, "P", 4, -8)]:
        p.append(DOT(sx(x), sy(y)))
        p.append(T(sx(x) + dx, sy(y) + dy, lab))
    return SVG(340, 214, p, "抛物线与三角形")


def f_inverse_k():
    """sh_239_1 反比例 k 的几何意义（k<0，二四象限）"""
    p = []
    sx = lambda x: 170 + 40 * x
    sy = lambda y: 104 - 20 * y
    p.append(L(46, sy(0), 300, sy(0), w=1.3))
    p.append(L(sx(0), 22, sx(0), 196, w=1.3))
    p.append(T(298, sy(0) - 8, "x", anchor="end", size=12))
    p.append(T(sx(0) + 10, 30, "y", size=12))
    for sgn in (1, -1):
        pts = []
        t = 0.55
        while t <= 5.0:
            pts.append((sx(sgn * t), sy(-6 / (sgn * t))))
            t += 0.12
        p.append(PL(pts, w=2.2))
    # P(-2,3), A(-2,0), O
    p.append(PL([(sx(0), sy(0)), (sx(-2), sy(3)), (sx(-2), sy(0))], close=True,
                color="#c0392b", w=1.7, fill="rgba(192,57,43,.08)"))
    p.append(RA(sx(-2), sy(0), 1, 0, 9))
    for (x, y, lab, dx, dy) in [(0, 0, "O", 11, 15), (-2, 3, "P", -14, 4), (-2, 0, "A", -13, 15)]:
        p.append(DOT(sx(x), sy(y)))
        p.append(T(sx(x) + dx, sy(y) + dy, lab))
    return SVG(340, 210, p, "反比例函数中 k 的几何意义")


def f_rotation():
    """sh_245_1 绕点 A 顺时针旋转 50°"""
    p = []
    ax, ay = 122, 200
    B = P(110, 128, ax, ay)
    C = P(80, 98, ax, ay)
    B2 = P(60, 128, ax, ay)
    C2 = P(30, 98, ax, ay)
    p.append(PL([(ax, ay), B, C], close=True, w=2.0))
    p.append(PL([(ax, ay), B2, C2], close=True, w=2.0, color="#1f6fb2"))
    p.append(ARC(ax, ay, 38, 80, 110))
    p.append(ARC(ax, ay, 62, 60, 110))
    p.append(T(*P(95, 52, ax, ay), "30°", size=11))
    p.append(T(*P(70, 76, ax, ay), "50°", size=11, color="#1f6fb2"))
    for pt, lab, dx, dy in [(B, "B", -6, -10), (C, "C", -4, -11), (B2, "B′", 4, -12),
                            (C2, "C′", 10, 8), ((ax, ay), "A", -16, 17)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 224, p, "三角形旋转")


def f_square_rotate():
    """sh_247_1 正方形中 EF=BE+DF"""
    p = []
    A, B, C, D = (96, 44), (256, 44), (256, 204), (96, 204)
    E = (256, 128)
    F = (176, 204)
    p.append(PL([A, B, C, D], close=True, w=2.0))
    p.append(L(*A, *E, w=1.8, color="#1f6fb2"))
    p.append(L(*A, *F, w=1.8, color="#1f6fb2"))
    p.append(L(*E, *F, w=2.0, color="#c0392b"))
    p.append(ARC(A[0], A[1], 46, -44, -20))
    p.append(T(A[0] + 56, A[1] + 34, "45°", size=11))
    for pt, lab, dx, dy in [(A, "A", -13, -6), (B, "B", 12, -6), (C, "C", 12, 14),
                            (D, "D", -13, 14), (E, "E", 12, 5), (F, "F", -4, 18)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "正方形中的旋转")


def f_chord():
    """sh_251_1 垂径定理"""
    p = []
    cx, cy, r = 170, 104, 100
    ay = cy + 60
    A = (cx - 80, ay)
    B = (cx + 80, ay)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2.0))
    p.append(L(cx, cy, cx, ay, w=1.6, color="#1f6fb2"))
    p.append(L(cx, cy, *A, w=1.4, dash="5 4", color=GRAY))
    p.append(RA(cx, ay, 0, -1, 10))
    for pt, lab, dx, dy in [((cx, cy), "O", 12, -2), (A, "A", -12, 5),
                            (B, "B", 12, 5), ((cx, ay), "M", 6, 17)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 224, p, "垂径定理")


def f_inscribed_angle():
    """sh_253_1 圆周角"""
    p = []
    cx, cy, r = 170, 118, 88
    A = P(220, r, cx, cy)
    B = P(320, r, cx, cy)
    C = P(90, r, cx, cy)
    p.append(CI(cx, cy, r))
    p.append(L(*C, *A, w=1.8))
    p.append(L(*C, *B, w=1.8))
    p.append(L(cx, cy, *A, w=1.2, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *B, w=1.2, dash="4 4", color=GRAY))
    p.append(L(*A, *B, w=1.2, dash="4 4", color=GRAY))
    # 圆心角 ∠AOB
    p.append(ARC(cx, cy, 34, 220, 320))
    p.append(T(*P(270, 40, cx, cy), "100°", size=10))
    # 圆周角 ∠ACB
    p.append(ARC(C[0], C[1], 30, 245, 295))
    p.append(T(C[0], C[1] + 50, "?", size=12, color="#c0392b"))
    for pt, lab, dx, dy in [((cx, cy), "O", 12, 4), (A, "A", -13, 6),
                            (B, "B", 13, 6), (C, "C", 0, -11)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 226, p, "圆周角定理")


def f_cyclic_quad():
    """sh_255_1 圆内接四边形"""
    p = []
    cx, cy, r = 170, 112, 84
    A = P(95, r, cx, cy)
    B = P(340, r, cx, cy)
    C = P(250, r, cx, cy)
    D = P(170, r, cx, cy)
    p.append(CI(cx, cy, r))
    p.append(PL([A, B, C, D], close=True, w=2.0))
    for pt, lab, dx, dy in [(A, "A", -4, -10), (B, "B", 13, 6),
                            (C, "C", 6, 17), (D, "D", -14, 6)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(DOT(cx, cy, 2.0))
    p.append(T(cx + 11, cy + 14, "O"))
    return SVG(340, 226, p, "圆内接四边形")


def f_sector():
    """sh_257_1 扇形面积"""
    p = []
    cx, cy, r = 170, 190, 118
    p.append(ARC(cx, cy, r, 30, 150))
    p.append(L(cx, cy, *P(30, r, cx, cy)))
    p.append(L(cx, cy, *P(150, r, cx, cy)))
    p.append(ARC(cx, cy, 30, 30, 150))
    p.append(T(*P(90, 46, cx, cy), "120°", size=11))
    p.append(T(*P(60, r / 2, cx, cy), "6", size=12))
    p.append(DOT(cx, cy))
    p.append(T(cx - 11, cy + 16, "O"))
    return SVG(340, 214, p, "扇形")


def f_cone():
    """sh_258_1 圆锥"""
    p = []
    cx, apex, by = 170, 44, 172
    rx, ry = 84, 20
    p.append(L(cx, apex, cx - rx, by, w=1.8))
    p.append(L(cx, apex, cx + rx, by, w=1.8))
    p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d"/>' % (cx, by, rx, ry))
    p.append('<path d="M%d,%d A%d,%d 0 0 0 %d,%d" fill="none"/>'
             % (cx + rx, by, rx, ry, cx - rx, by))
    p.append(L(cx, apex, cx, by, dash="5 4", color=GRAY))
    p.append(T(cx + 46, (apex + by) / 2, "5", size=12, color="#1f6fb2"))
    p.append(T(cx, by + 34, "3", size=12, color="#1f6fb2"))
    p.append(T(cx, apex - 12, "母线 l=5，底面半径 r=3", size=11, color=GRAY))
    p.append(DOT(cx, apex))
    return SVG(340, 210, p, "圆锥")


def f_tangent_len():
    """sh_263_1 切线长定理"""
    p = []
    cx, cy, r = 170, 116, 56
    d = 112
    A = P(-30, r, cx, cy)
    B = P(-150, r, cx, cy)
    Pp = (cx, cy + d)
    p.append(CI(cx, cy, r))
    p.append(L(*Pp, *A, w=1.8))
    p.append(L(*Pp, *B, w=1.8))
    p.append(L(cx, cy, *A, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *B, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *Pp, w=1.2, dash="4 4", color=GRAY))
    p.append(RA(A[0], A[1], (Pp[0] - A[0]) / 120.0, (Pp[1] - A[1]) / 120.0, 9))
    p.append(ARC(*Pp, 34, 70, 110))
    p.append(T(*P(90, 30, Pp[0], Pp[1]), "60°", size=10))
    p.append(T(cx + 12, cy - 8, "O", size=11))
    for pt, lab, dx, dy in [(A, "A", -12, -4), (B, "B", 12, -4), (Pp, "P", 0, 18)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(DOT(cx, cy))
    return SVG(340, 248, p, "切线长定理")


def f_tangent_prop():
    """sh_262_1 切线的性质"""
    p = []
    cx, cy, r = 128, 124, 74
    A = (cx, cy - r)
    Pp = (A[0] + 128, A[1])
    p.append(CI(cx, cy, r))
    p.append(L(46, A[1], 300, A[1], w=1.8))
    p.append(L(cx, cy, *A, w=1.5, color="#1f6fb2"))
    p.append(L(cx, cy, *Pp, w=1.5))
    p.append(RA(A[0], A[1], 1, 0, 10))
    p.append(ARC(*Pp, 42, 180, 210))
    p.append(T(*P(196, 56, Pp[0], Pp[1]), "30°", size=10))
    p.append(T(A[0] - 13, A[1] - 8, "A"))
    p.append(T(Pp[0] + 10, Pp[1] - 8, "P"))
    p.append(T(cx + 4, cy + 17, "O"))
    p.append(DOT(*A) + DOT(*Pp) + DOT(cx, cy))
    return SVG(340, 210, p, "切线的性质")


def f_incircle():
    """sh_264_1 直角三角形内切圆"""
    p = []
    C = (86, 206)
    A = (206, 206)
    B = (86, 46)
    ri = 40
    O = (C[0] + ri, C[1] - ri)
    p.append(PL([C, A, B], close=True, w=2.0))
    p.append(CI(O[0], O[1], ri))
    p.append(RA(C[0], C[1], 1, 0, 11))
    p.append(T((C[0] + A[0]) / 2, C[1] + 19, "3"))
    p.append(T(C[0] - 15, (C[1] + B[1]) / 2, "4"))
    p.append(T((A[0] + B[0]) / 2 + 20, (A[1] + B[1]) / 2 - 4, "5", anchor="start"))
    p.append(DOT(*O, 2.0))
    p.append(T(O[0] + 12, O[1] - 2, "O"))
    return SVG(340, 234, p, "三角形内切圆")


def f_circumcircle():
    """sh_265_1 直角三角形外接圆"""
    p = []
    C = (86, 206)
    A = (206, 206)
    B = (86, 46)
    O = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
    r = math.hypot(A[0] - O[0], A[1] - O[1])
    p.append(CI(O[0], O[1], r))
    p.append(PL([C, A, B], close=True, w=2.0))
    p.append(RA(C[0], C[1], 1, 0, 11))
    p.append(T((C[0] + A[0]) / 2, C[1] + 19, "6"))
    p.append(T(C[0] - 15, (C[1] + B[1]) / 2, "8"))
    p.append(T((A[0] + B[0]) / 2 + 18, (A[1] + B[1]) / 2 - 2, "10", anchor="start"))
    p.append(DOT(*O, 2.0))
    p.append(T(O[0] + 13, O[1] + 4, "O"))
    return SVG(340, 234, p, "三角形外接圆")


def f_similar():
    """sh_271_1 相似三角形的判定"""
    p = []
    A = (74, 208)
    B = (286, 208)
    C = (152, 62)
    D = (196, 208)
    p.append(PL([A, B, C], close=True, w=2.0))
    p.append(L(*C, *D, w=1.8, color="#1f6fb2"))
    p.append(ARC(*C, 34, 250, 288))
    p.append(T(*P(266, 46, C[0], C[1]), "1", size=11, color="#c0392b"))
    p.append(ARC(*B, 34, 152, 178))
    p.append(T(*P(164, 46, B[0], B[1]), "2", size=11, color="#c0392b"))
    for pt, lab, dx, dy in [(A, "A", -14, 6), (B, "B", 13, 6),
                            (C, "C", 0, -10), (D, "D", 0, 19)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 234, p, "相似三角形")


def f_elevation():
    """sh_279_1 仰角"""
    p = []
    g = 200
    hpx = 138.0
    bx = 292
    p.append(L(34, g, 320, g, w=1.6))
    p.append(L(bx, g, bx, g - hpx, w=2.2))
    p.append(L(50, g, bx, g - hpx, w=1.5))
    p.append(L(212, g, bx, g - hpx, w=1.5))
    p.append(L(50, g, 212, g, w=2.4, color="#8b8b8b"))
    p.append(ARC(50, g, 40, 0, 31))
    p.append(T(*P(15, 48, 50, g), "30°", size=10))
    p.append(ARC(212, g, 34, 0, 60))
    p.append(T(*P(30, 42, 212, g), "60°", size=10))
    p.append(T(131, g + 18, "20 m", size=11, color=GRAY))
    p.append(T(bx + 12, g - hpx / 2, "楼", size=11, anchor="start", color=GRAY))
    for pt, lab, dx, dy in [((50, g), "A", -13, 15), ((212, g), "B", 0, 17)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(DOT(bx, g - hpx))
    p.append(T(bx + 12, g - hpx - 6, "C", anchor="start"))
    p.append(RA(bx, g, -1, 0, 10))
    return SVG(340, 224, p, "仰角问题")


def f_slope():
    """sh_280_1 坡度"""
    p = []
    x0, y0 = 62, 178
    x1, y1 = 258, 178
    x2, y2 = 258, 80
    p.append(PL([(x0, y0), (x1, y1), (x2, y2)], close=True, w=2.0))
    p.append(RA(x1, y1, -1, 0, 10))
    p.append(T(196, y0 - 10, "水平 2", size=11, color=GRAY))
    p.append(T(x1 + 12, (y1 + y2) / 2 + 4, "铅直 1", size=11, anchor="start", color=GRAY))
    p.append(T((x0 + x2) / 2 - 30, (y0 + y2) / 2 + 4, "20 m", size=11))
    p.append(ARC(x0, y0, 44, 0, 26))
    p.append(T(*P(13, 60, x0, y0), "α", size=11))
    p.append(T(170, 204, "坡比 i = 铅直 ∶ 水平 = 1 ∶ 2", size=11, color=GRAY))
    p.append(DOT(x0, y0) + DOT(x2, y2))
    return SVG(340, 214, p, "坡度问题")


def f_spinner():
    """sh_289_1 转盘"""
    p = []
    cx, cy, r = 170, 132, 84
    p.append(CI(cx, cy, r))
    for d in (30, 150, 270):
        p.append(L(cx, cy, *P(d, r, cx, cy)))
    for d, lab in [(90, "1"), (210, "2"), (330, "3")]:
        p.append(T(*P(d, r * 0.56, cx, cy), lab, size=17, bold=True))
    p.append(DOT(cx, cy, 3))
    # 指针画在圆外，指向转盘
    p.append(L(cx, cy - r - 40, cx, cy - r - 8, w=2.2, color="#c0392b"))
    p.append(PL([(cx - 7, cy - r - 16), (cx, cy - r - 4), (cx + 7, cy - r - 16)],
                close=True, color="#c0392b", fill="#c0392b"))
    return SVG(340, 240, p, "转盘")


# ---------- 北师大九上提高题的图 ----------

def f_bn003():
    """bn003 平行四边形 ABCD，E 为 BC 中点，AE 交 BD 于 F"""
    p = []
    A, B, C, D = (60, 180), (260, 180), (360, 60), (160, 60)
    E, F = (310, 120), (227, 140)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(A[0], A[1], E[0], E[1], color=GRAY))
    p.append(L(B[0], B[1], D[0], D[1], color=GRAY))
    p.append(DOT(*E) + DOT(*F))
    p.append(T(44, 186, "A", size=14))
    p.append(T(266, 186, "B", size=14))
    p.append(T(372, 56, "C", size=14))
    p.append(T(150, 56, "D", size=14))
    p.append(T(320, 138, "E", size=14))
    p.append(T(210, 154, "F", size=14))
    return SVG(420, 212, p, "平行四边形 ABCD，E 为 BC 中点，AE 交 BD 于 F")


def f_bn023():
    """bn023 平行四边形 ABCD，CF 延长交 BA 延长线于 G"""
    p = []
    # 数学坐标 B(0,0) C(4,0) A(1,2) D(5,2) 映射到屏幕
    def M(x, y):
        return (80 + 62 * x, 300 - 40 * y)
    B, C, A, D = M(0, 0), M(4, 0), M(1, 2), M(5, 2)
    F, E, G = M(11 / 3.0, 2), M(3.75, 1.5), M(3, 6)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(B[0], B[1], D[0], D[1], color=GRAY))
    p.append(L(G[0], G[1], C[0], C[1], color=GRAY))
    # G 在 BA 的延长线上，所以 G-A-B 三点共线，这条线要画出来
    p.append(L(G[0], G[1], B[0], B[1], color=GRAY, dash="6 3"))
    p.append(DOT(*F) + DOT(*E))
    p.append(T(A[0] - 14, A[1] + 4, "A", size=14))
    p.append(T(B[0] - 14, B[1] + 16, "B", size=14))
    p.append(T(C[0] + 14, C[1] + 16, "C", size=14))
    p.append(T(D[0] + 14, D[1] + 4, "D", size=14))
    p.append(T(G[0] - 4, G[1] - 10, "G", size=14))
    p.append(T(F[0] + 2, F[1] - 10, "F", size=14))
    p.append(T(E[0] + 14, E[1] + 16, "E", size=14))
    return SVG(430, 330, p, "平行四边形 ABCD，CF 延长交 BA 延长线于 G")


def f_bn024():
    """bn024 新定义 k 倍四边形，两幅对照图"""
    p = []
    # ---- 图 1：平行四边形，E 为 OB 中点 ----
    def M1(x, y):
        return (46 + 42 * x, 190 - 42 * y)
    A, B, C, D = M1(0, 0), M1(4, 0), M1(5, 2), M1(1, 2)
    O, E = M1(2.5, 1), M1(2.25, 0.5)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(A[0], A[1], C[0], C[1], color=GRAY))
    p.append(L(B[0], B[1], D[0], D[1], color=GRAY))
    p.append(L(A[0], A[1], E[0], E[1], color=GRAY))
    p.append(L(E[0], E[1], C[0], C[1], color=GRAY))
    p.append(DOT(*O) + DOT(*E))
    p.append(T(A[0] - 12, A[1] + 14, "A", size=13))
    p.append(T(B[0] - 12, B[1] + 14, "B", size=13))
    p.append(T(C[0] + 12, C[1] - 2, "C", size=13))
    p.append(T(D[0] + 12, D[1] - 2, "D", size=13))
    p.append(T(O[0] + 10, O[1] - 6, "O", size=13))
    p.append(T(E[0] - 12, E[1] + 16, "E", size=13))
    p.append(T(140, 222, "图 1", size=12, color=GRAY))

    # ---- 图 2：k 倍四边形（AC 被 BD 平分，OD > OB）----
    def M2(x, y):
        return (300 + 42 * x, 190 - 42 * y)
    A2, C2 = M2(0, 0), M2(4, 0)
    O2 = M2(2, 0)
    B2, D2 = M2(2, -1), M2(2, 2)
    p.append(PL([A2, B2, C2, D2], close=True, w=2))
    p.append(L(A2[0], A2[1], C2[0], C2[1], color=GRAY))
    p.append(L(B2[0], B2[1], D2[0], D2[1], color=GRAY))
    p.append(DOT(*O2))
    p.append(T(A2[0] - 14, A2[1] + 4, "A", size=13))
    p.append(T(C2[0] + 14, C2[1] + 4, "C", size=13))
    p.append(T(B2[0] - 14, B2[1] + 4, "B", size=13))
    p.append(T(D2[0] + 14, D2[1] + 4, "D", size=13))
    p.append(T(O2[0] + 16, O2[1] - 6, "O", size=13))
    p.append(T(400, 222, "图 2", size=12, color=GRAY))
    return SVG(500, 240, p, "k 倍四边形示意")


def f_bn027():
    """bn027 直角梯形背景上的动点，AQPE 为平行四边形"""
    p = []
    def M(x, y):
        return (56 + 14 * x, 262 - 14 * y)
    A, B, C, D = M(0, 0), M(16, 0), M(16, 6), M(8, 6)
    P, Q = M(6.4, 4.8), M(4, 0)
    E = M(2.4, 4.8)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(RA(C[0], C[1], 0, 1, 9))
    # 平行四边形 AQPE
    p.append(PL([A, Q, P, E], close=True, dash="5 3", color=GRAY))
    p.append(L(P[0], P[1], Q[0], Q[1], color=GRAY))
    p.append(DOT(*P) + DOT(*Q) + DOT(*E))
    p.append(T(A[0] - 14, A[1] + 16, "A", size=14))
    p.append(T(B[0] + 6, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 16, C[1] - 4, "C", size=14))
    p.append(T(D[0] + 2, D[1] - 12, "D", size=14))
    p.append(T(P[0] - 4, P[1] - 10, "P", size=14))
    p.append(T(Q[0] - 4, Q[1] + 20, "Q", size=14))
    p.append(T(E[0] - 14, E[1] + 4, "E", size=14))
    return SVG(330, 300, p, "四边形 ABCD 与动点 P、Q，AQPE 为平行四边形")


def f_bn028():
    """bn028 正方形中 AE 与 BF 交于 G"""
    p = []
    def M(x, y):
        return (66 + 50 * x, 246 - 50 * y)
    A, B, C, D = M(0, 0), M(4, 0), M(4, 4), M(0, 4)
    E, F = M(4, 1), M(3, 4)
    G = M(64 / 17.0, 16 / 17.0)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(A[0], A[1], E[0], E[1], color=GRAY))
    p.append(L(B[0], B[1], F[0], F[1], color=GRAY))
    p.append(RA(G[0], G[1], 0.235, 0.972, 8))
    p.append(DOT(*E) + DOT(*F) + DOT(*G))
    p.append(T(A[0] - 14, A[1] + 16, "A", size=14))
    p.append(T(B[0] + 6, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 16, C[1] - 2, "C", size=14))
    p.append(T(D[0] - 14, D[1] - 2, "D", size=14))
    p.append(T(E[0] + 15, E[1] + 18, "E", size=14))
    p.append(T(F[0] + 2, F[1] - 12, "F", size=14))
    p.append(T(G[0] - 8, G[1] + 22, "G", size=14))
    return SVG(340, 290, p, "正方形 ABCD 中 AE 与 BF 交于点 G")


def f_bn032():
    """bn032 矩形折叠，EF 为折痕（AC 的垂直平分线）"""
    p = []
    def M(x, y):
        return (60 + 30 * x, 306 - 30 * y)
    A, B, C, D = M(0, 0), M(6, 0), M(6, 8), M(0, 8)
    E, F = M(0, 6.25), M(6, 1.75)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(A[0], A[1], C[0], C[1], dash="5 3", color=GRAY))
    p.append(L(E[0], E[1], F[0], F[1], w=2.2))
    p.append(RA(A[0], A[1], 1, 0, 8))
    p.append(DOT(*E) + DOT(*F))
    p.append(T(A[0] - 14, A[1] + 16, "A", size=14))
    p.append(T(B[0] + 6, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 16, C[1] - 2, "C", size=14))
    p.append(T(D[0] - 14, D[1] - 2, "D", size=14))
    p.append(T(E[0] - 16, E[1] + 4, "E", size=14))
    p.append(T(F[0] + 16, F[1] + 4, "F", size=14))
    return SVG(320, 340, p, "矩形 ABCD 沿 EF 折叠使 C 与 A 重合")


def f_bn033():
    """bn033 正方形中 ∠EAF = 45°"""
    p = []
    def M(x, y):
        return (70 + 30 * x, 266 - 30 * y)
    A, B, C, D = M(0, 0), M(6, 0), M(6, 6), M(0, 6)
    E, F = M(6, 2), M(3, 6)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(A[0], A[1], E[0], E[1], color=GRAY))
    p.append(L(A[0], A[1], F[0], F[1], color=GRAY))
    p.append(L(E[0], E[1], F[0], F[1], w=2))
    p.append(DOT(*E) + DOT(*F))
    p.append(T(A[0] - 14, A[1] + 16, "A", size=14))
    p.append(T(B[0] + 6, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 16, C[1] - 2, "C", size=14))
    p.append(T(D[0] - 14, D[1] - 2, "D", size=14))
    p.append(T(E[0] + 16, E[1] + 6, "E", size=14))
    p.append(T(F[0] + 2, F[1] - 12, "F", size=14))
    p.append(T(A[0] + 46, A[1] - 22, "45°", size=12, color=GRAY))
    return SVG(340, 310, p, "正方形 ABCD 中 E 在 BC、F 在 CD，∠EAF = 45°")


# ============ 北师大九下压轴题（圆 / 反比例函数 / 解直角三角形） ============

def f_bn9_001():
    """9b001 半径 5 的圆，弦 AB = 8，点 C 在优弧上"""
    p = []
    cx, cy, r = 170, 130, 90          # 90px = 5 单位
    A, B = (cx - 72, cy + 54), (cx + 72, cy + 54)   # 半弦 4、弦心距 3
    C = (180, 45)
    p.append(CI(cx, cy, r, w=None) if False else CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(L(cx, cy, *A, color=GRAY) + L(cx, cy, *B, color=GRAY))
    p.append(L(cx, cy, cx, cy + 54, dash="4 3", color=GRAY))
    p.append(L(*A, *C, color=GRAY) + L(*B, *C, color=GRAY))
    p.append(RA(cx, cy + 54, 0, -1, 8))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C))
    p.append(T(cx - 14, cy + 5, "O", size=14))
    p.append(T(A[0] - 12, A[1] + 18, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 2, C[1] - 10, "C", size=14))
    return SVG(340, 250, p, "⊙O 中弦 AB = 8，点 C 在圆上")


def f_bn9_004():
    """9b004 堤坝梯形横断面"""
    p = []
    A, B, C, D = (40, 200), (139, 134), (183, 134), (315, 200)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(B[0], B[1], B[0], 200, dash="4 3", color=GRAY))
    p.append(L(C[0], C[1], C[0], 200, dash="4 3", color=GRAY))
    p.append(RA(B[0], 200, 1, 0, 8) + RA(C[0], 200, -1, 0, 8))
    p.append(T(B[0] - 26, 166, "6 m", size=12, color=GRAY))
    p.append(T((B[0] + C[0]) / 2, 126, "4 m", size=12))
    p.append(T(A[0] - 14, A[1] + 18, "A", size=14))
    p.append(T(B[0] - 6, B[1] - 10, "B", size=14))
    p.append(T(C[0] + 8, C[1] - 10, "C", size=14))
    p.append(T(D[0] + 14, D[1] + 18, "D", size=14))
    p.append(T((A[0] + B[0]) / 2 - 10, 150, "i = 1 : 1.5", size=11, color=GRAY))
    p.append(T((C[0] + D[0]) / 2 + 10, 150, "i = 1 : 2", size=11, color=GRAY))
    return SVG(360, 230, p, "梯形堤坝横断面，坝顶 4 m，坝高 6 m")


def f_bn9_007():
    """9b007 直径 AB 与垂直于它的弦 CD"""
    p = []
    cx, cy, r = 160, 125, 80
    A, B = (cx - 80, cy), (cx + 80, cy)
    E = (cx - 48, cy)                  # AE = 2 单位（32px）
    C, D = (E[0], cy - 64), (E[0], cy + 64)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(L(*C, *D, w=2))
    p.append(L(cx, cy, *C, color=GRAY) + L(cx, cy, *D, color=GRAY))
    p.append(RA(E[0], E[1], 1, 0, 8))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*E))
    p.append(T(cx - 6, cy - 10, "O", size=14))
    p.append(T(A[0] - 12, A[1] + 6, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 6, "B", size=14))
    p.append(T(C[0] - 14, C[1] - 2, "C", size=14))
    p.append(T(D[0] - 14, D[1] + 12, "D", size=14))
    p.append(T(E[0] - 12, E[1] + 16, "E", size=14))
    return SVG(340, 250, p, "AB 是直径，弦 CD ⊥ AB 于 E")


def f_bn9_009():
    """9b009 圆外一点引两条切线"""
    p = []
    cx, cy, r = 150, 150, 80
    P_ = (283, 150)
    A, B = (198, 86), (198, 214)
    p.append(CI(cx, cy, r))
    p.append(L(*P_, *A, w=2) + L(*P_, *B, w=2))
    p.append(L(cx, cy, *A, color=GRAY) + L(cx, cy, *B, color=GRAY))
    p.append(L(cx, cy, *P_, dash="5 3", color=GRAY))
    p.append(RA(A[0], A[1], 0.6, -0.8, 9) + RA(B[0], B[1], 0.6, 0.8, 9))
    p.append(DOT(cx, cy) + DOT(*P_) + DOT(*A) + DOT(*B))
    p.append(T(cx - 16, cy + 6, "O", size=14))
    p.append(T(P_[0] + 10, P_[1] + 6, "P", size=14))
    p.append(T(A[0] + 10, A[1] - 8, "A", size=14))
    p.append(T(B[0] + 10, B[1] + 14, "B", size=14))
    return SVG(340, 270, p, "PA、PB 切 ⊙O 于 A、B")


def f_bn9_011():
    """9b011 第二象限内双曲线上的点 A，AB ⊥ x 轴"""
    p = []
    ox, oy, sc = 160, 180, 26
    p.append(L(30, oy, 300, oy, w=1.6) + L(ox, 40, ox, 300, w=1.6))
    p.append(T(306, oy + 4, "x", size=12, anchor="start"))
    p.append(T(ox - 6, 36, "y", size=12, anchor="end"))
    p.append(T(ox - 12, oy + 16, "O", size=13))
    # 第二象限分支（k = −10）
    pts = [(ox - sc * x, oy - sc * (10.0 / x)) for x in [1.1 + 0.15 * i for i in range(28)]]
    pts = [(x, y) for x, y in pts if y > 26]
    p.append(PL(pts, w=2))
    A = (ox - 2 * sc, oy - 5 * sc)
    B = (A[0], oy)
    p.append(L(*A, *B, w=2) + L(ox, oy, *A, w=2))
    p.append(RA(B[0], B[1], 1, 0, 8))
    p.append(DOT(*A) + DOT(*B))
    p.append(T(A[0] - 14, A[1] - 4, "A", size=14))
    p.append(T(B[0] - 4, B[1] + 18, "B", size=14))
    return SVG(340, 320, p, "双曲线 y = k/x 上一点 A，AB ⊥ x 轴于 B")


def f_bn9_019():
    """9b019 仰角测楼高"""
    p = []
    A, B, C, D = (56, 210), (140, 210), (250, 210), (250, 56)
    p.append(L(30, 210, 300, 210, w=1.6))
    p.append(L(*C, *D, w=2.4))
    p.append(L(*A, *D, dash="5 3", color=GRAY) + L(*B, *D, dash="5 3", color=GRAY))
    p.append(RA(C[0], C[1], -1, 0, 9))
    p.append(DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D))
    p.append(T(A[0] - 8, A[1] + 18, "A", size=14))
    p.append(T(B[0], B[1] + 18, "B", size=14))
    p.append(T(C[0] - 2, C[1] + 18, "C", size=14))
    p.append(T(D[0] + 16, D[1] + 4, "D", size=14))
    p.append(T(A[0] + 26, A[1] - 8, "30°", size=11, color=GRAY))
    p.append(T(B[0] + 26, B[1] - 8, "45°", size=11, color=GRAY))
    p.append(T((A[0] + B[0]) / 2, 232, "20 m", size=12, color=GRAY))
    return SVG(340, 250, p, "在 A、B 两处测楼顶 D 的仰角")


def f_bn9_020():
    """9b020 一次函数与反比例函数交于 A、B"""
    p = []
    ox, oy, sc = 130, 130, 22
    p.append(L(26, oy, 320, oy, w=1.6) + L(ox, 24, ox, 300, w=1.6))
    p.append(T(326, oy + 4, "x", size=12, anchor="start"))
    p.append(T(ox - 6, 22, "y", size=12, anchor="end"))
    p.append(T(ox - 12, oy + 16, "O", size=13))
    # y = −6/x
    pts = [(ox - sc * x, oy - sc * (6.0 / x)) for x in [0.55 + 0.12 * i for i in range(40)]]
    pts = [(x, y) for x, y in pts if 22 < y < 306]
    p.append(PL(pts, w=2))
    pts2 = [(ox + sc * x, oy + sc * (6.0 / x)) for x in [0.55 + 0.12 * i for i in range(40)]]
    pts2 = [(x, y) for x, y in pts2 if 22 < y < 306]
    p.append(PL(pts2, w=2))
    A = (ox - 2 * sc, oy - 3 * sc)
    B = (ox + 6 * sc, oy + 1 * sc)
    # 直线 y = −x/2 + 2
    x1, x2 = -4.6, 9.5
    p.append(L(ox + sc * x1, oy - sc * (-x1 / 2 + 2),
               ox + sc * x2, oy - sc * (-x2 / 2 + 2), w=2))
    p.append(DOT(*A) + DOT(*B))
    p.append(T(A[0] - 12, A[1] - 8, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 12, "B", size=14))
    return SVG(340, 320, p, "直线与双曲线交于 A、B 两点")


def f_bn9_021():
    """9b021 AC 平分 ∠DAB，DC 为切线"""
    p = []
    cx, cy, r = 160, 130, 75
    A, B = (cx - r, cy), (cx + r, cy)
    C = (139, 58)
    D = (70, 78)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(L(*A, *C, w=2))
    p.append(L(*C, *D, w=2.2))
    p.append(L(cx, cy, *C, dash="4 3", color=GRAY))
    p.append(L(*A, *D, color=GRAY))
    p.append(RA(C[0], C[1], 0.28, 0.96, 9) + RA(D[0], D[1], -0.28, -0.96, 9))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D))
    p.append(T(cx - 4, cy + 20, "O", size=14))
    p.append(T(A[0] - 12, A[1] + 18, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 6, "B", size=14))
    p.append(T(C[0] + 14, C[1] - 2, "C", size=14))
    p.append(T(D[0] - 14, D[1] - 8, "D", size=14))
    return SVG(330, 250, p, "AC 平分 ∠DAB，DC 切 ⊙O 于 C")


def f_bn9_022():
    """9b022 等腰三角形内接半圆，DE ⊥ AC"""
    p = []
    A, B, C = (180, 60), (60, 220), (300, 220)
    O_ = (120, 140)
    D = (180, 220)
    E = (257, 162)
    p.append(PL([A, B, C], close=True, w=2))
    p.append(CI(*O_, 100))
    p.append(L(*A, *D, color=GRAY))
    p.append(L(*D, *E, w=2.2))
    p.append(L(*O_, *D, dash="4 3", color=GRAY))
    p.append(RA(D[0], D[1], 0.8, -0.6, 9))
    p.append(RA(E[0], E[1], -0.6, -0.8, 9))
    p.append(DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*E) + DOT(*O_))
    p.append(T(A[0], A[1] - 10, "A", size=14))
    p.append(T(B[0] - 14, B[1] + 6, "B", size=14))
    p.append(T(C[0] + 14, C[1] + 6, "C", size=14))
    p.append(T(D[0] + 4, D[1] + 20, "D", size=14))
    p.append(T(E[0] + 16, E[1] + 2, "E", size=14))
    p.append(T(O_[0] - 14, O_[1] - 6, "O", size=14))
    return SVG(350, 260, p, "以 AB 为直径的 ⊙O 交 BC 于 D，DE ⊥ AC")


def f_bn9_023():
    """9b023 半径 10，弦 10√3，圆心角 120°"""
    p = []
    cx, cy, r = 170, 140, 95
    A, B = (87.7, 187.5), (252.3, 187.5)
    H = (170, 187.5)
    p.append(CI(cx, cy, r))
    # 弓形（劣弧与弦之间）浅色填充，比画一段重复的弧线清楚
    seg = [P(210 + 1.0 * i, r, cx, cy) for i in range(121)]
    p.append(PL([A] + seg + [B], close=True, fill="#f0efec", color="none", w=0))
    p.append(L(*A, *B, w=2.2))
    p.append(L(cx, cy, *A, color=GRAY) + L(cx, cy, *B, color=GRAY))
    p.append(L(cx, cy, *H, dash="4 3", color=GRAY))
    p.append(RA(H[0], H[1], 0, -1, 8))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*H))
    p.append(T(cx - 6, cy - 12, "O", size=14))
    p.append(T(A[0] - 12, A[1] + 6, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 6, "B", size=14))
    p.append(T(H[0] + 14, H[1] + 6, "H", size=14))
    p.append(T(cx, cy + 34, "120°", size=11, color=GRAY))
    return SVG(340, 230, p, "⊙O 中弦 AB 所对的圆心角为 120°")


def f_bn9_024():
    """9b024 三级台阶与坡板"""
    p = []
    # 台阶轮廓：三级踏面 + 三级踢面
    pts = [(50, 250), (110, 250), (110, 220), (170, 220), (170, 190), (230, 190), (230, 160)]
    p.append(PL(pts, w=2))
    # 坡板：从第一级前沿铺到第三级后沿
    p.append(L(110, 250, 230, 160, w=2.6))
    # 尺寸标注
    p.append(L(110, 268, 230, 268, color=GRAY))
    p.append(T(170, 284, "水平 90 cm", size=11, color=GRAY))
    p.append(L(248, 250, 248, 160, color=GRAY))
    p.append(T(258, 208, "45", size=11, color=GRAY, anchor="start"))
    p.append(T(266, 222, "cm", size=11, color=GRAY, anchor="start"))
    p.append(T(96, 214, "15", size=10, color=GRAY, anchor="end"))
    p.append(T(156, 184, "15", size=10, color=GRAY, anchor="end"))
    p.append(DOT(110, 250) + DOT(230, 160))
    return SVG(320, 300, p, "三级台阶与铺在上面的坡板")


def f_bn9_025():
    """9b025 v = 480/t 图象"""
    p = []
    ox, oy = 60, 240
    p.append(L(ox, oy, 310, oy, w=1.6) + L(ox, 40, ox, oy, w=1.6))
    p.append(T(316, oy + 4, "t/h", size=12, anchor="start"))
    p.append(T(ox - 8, 36, "v", size=12, anchor="end"))
    p.append(T(ox - 10, oy + 16, "O", size=13))
    pts = [(ox + 2.2 * t, oy - 0.9 * (480.0 / t)) for t in [2.6 + 0.2 * i for i in range(60)]]
    pts = [(x, y) for x, y in pts if 48 < y < oy]
    p.append(PL(pts, w=2))
    # 辅助虚线：t = 6 时 v = 80
    p.append(L(ox + 2.2 * 6, oy, ox + 2.2 * 6, oy - 0.9 * 80, dash="4 3", color=GRAY))
    p.append(L(ox, oy - 0.9 * 80, ox + 2.2 * 6, oy - 0.9 * 80, dash="4 3", color=GRAY))
    p.append(DOT(ox + 2.2 * 6, oy - 0.9 * 80))
    p.append(T(ox + 2.2 * 6, oy + 16, "6", size=12, color=GRAY))
    p.append(T(ox - 16, oy - 0.9 * 80 + 4, "80", size=12, color=GRAY))
    return SVG(340, 270, p, "v 关于 t 的反比例函数图象")


def f_bn9_026():
    """9b026 圆内接四边形 ABCD，PD 为切线"""
    p = []
    cx, cy, r = 150, 110, 60
    A, B = (90, 110), (210, 110)
    D = (120, 58)
    C = (180, 58)
    P_ = (30, 110)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(*P_, *D, w=2.2))
    p.append(L(cx, cy, *D, dash="4 3", color=GRAY))
    p.append(RA(D[0], D[1], 0.5, 0.87, 8))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*P_))
    p.append(T(cx - 4, cy + 18, "O", size=13))
    p.append(T(A[0] - 12, A[1] + 16, "A", size=13))
    p.append(T(B[0] + 12, B[1] + 16, "B", size=13))
    p.append(T(C[0] + 12, C[1] - 6, "C", size=13))
    p.append(T(D[0] - 12, D[1] - 6, "D", size=13))
    p.append(T(P_[0] - 12, P_[1] + 6, "P", size=13))
    return SVG(300, 200, p, "四边形 ABCD 内接于 ⊙O，PD 切 ⊙O 于 D")


def f_bn9_027():
    """9b027 圆锥与它的侧面展开图"""
    p = []
    # 左：圆锥
    apex = (90, 50)
    left, right = (40, 170), (140, 170)
    p.append(L(*apex, *left, w=2) + L(*apex, *right, w=2))
    p.append('<ellipse cx="90" cy="170" rx="50" ry="13"/>')
    p.append(L(90, 170, 140, 170, dash="4 3", color=GRAY))
    p.append(T(90, 40, "9", size=12))
    p.append(T(112, 178, "3", size=12, color=GRAY))
    # 右：展开扇形（用采样点画，避免 SVG 弧线方向标志出错）
    cx, cy, R = 250, 200, 90
    arc = [P(60 + 1.0 * i, R, cx, cy) for i in range(121)]
    p.append(PL([(cx, cy)] + arc, close=True, w=2))
    p.append(L(cx, cy, cx + R * 0.5, cy - R * 0.866, dash="4 3", color=GRAY))
    p.append(T(cx + 34, cy - 16, "120°", size=11, color=GRAY))
    p.append(T(cx + 24, cy - 62, "9", size=12))
    p.append(T(cx - 46, cy - 30, "9", size=12))
    return SVG(370, 230, p, "圆锥及其侧面展开图（圆心角 120°）")


def f_bn9_028():
    """9b028 直径 AB，弦 AC，∠ACB 的平分线交圆于 D"""
    p = []
    cx, cy, r = 170, 110, 90
    A, B = (80, 110), (260, 110)
    C = (144.8, 23.6)
    D = (170, 200)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(L(*A, *C, w=2) + L(*B, *C, w=2))
    p.append(L(*C, *D, w=2.2))
    p.append(L(*A, *D, color=GRAY) + L(*B, *D, color=GRAY))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D))
    p.append(T(cx - 4, cy + 20, "O", size=14))
    p.append(T(A[0] - 12, A[1] + 18, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 18, "B", size=14))
    p.append(T(C[0] - 4, C[1] - 10, "C", size=14))
    p.append(T(D[0] + 4, D[1] + 18, "D", size=14))
    return SVG(340, 230, p, "AB 是直径，CD 平分 ∠ACB")


def f_bn9_029():
    """9b029 方向角与暗礁判断"""
    p = []
    A, B = (56, 210), (216, 210)
    C = (296, 72)
    H = (296, 210)
    p.append(L(30, 210, 320, 210, w=1.6))
    p.append(L(316, 210, 308, 206, color=GRAY) + L(316, 210, 308, 214, color=GRAY))
    p.append(L(*A, *C, w=2) + L(*B, *C, w=2))
    p.append(L(*C, *H, dash="4 3", color=GRAY))
    p.append(RA(H[0], H[1], -1, 0, 8))
    # 指北线
    p.append(L(A[0], A[1], A[0], A[1] - 90, dash="3 3", color=GRAY))
    p.append(L(A[0], A[1] - 96, A[0], A[1] - 84, color=GRAY))
    p.append(T(A[0], A[1] - 104, "北", size=11, color=GRAY))
    p.append(DOT(*A) + DOT(*B) + DOT(*C))
    p.append(T(A[0] - 14, A[1] + 18, "A", size=14))
    p.append(T(B[0], B[1] + 18, "B", size=14))
    p.append(T(C[0] + 4, C[1] - 12, "C", size=14))
    p.append(T(150, 232, "40 海里", size=11, color=GRAY))
    p.append(T(A[0] + 12, A[1] - 44, "60°", size=11, color=GRAY))
    p.append(T(B[0] + 4, B[1] - 34, "30°", size=11, color=GRAY))
    return SVG(350, 260, p, "渔船由 A 向正东航行到 B，测灯塔 C 的方向")


def f_bn9_030():
    """9b030 直径 AB，BD 为切线，CE ⊥ AB"""
    p = []
    A, B = (50, 220), (275, 220)
    C, D = (194, 112), (275, 51)
    E = (194, 220)
    cx = (A[0] + B[0]) / 2.0
    p.append(CI(cx, 220, (B[0] - A[0]) / 2.0))
    p.append(L(*A, *B, w=2))
    p.append(L(*A, *D, w=2))
    p.append(L(*B, *D, w=2.2))
    p.append(L(*C, *E, w=2))
    p.append(RA(B[0], B[1], -1, 0, 9))
    p.append(RA(E[0], E[1], 0, -1, 8))
    p.append(DOT(cx, 220) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*E))
    p.append(T(cx - 12, 246, "O", size=13, anchor="end"))
    p.append(T(A[0] - 12, A[1] + 6, "A", size=14))
    p.append(T(B[0] + 10, B[1] + 6, "B", size=14))
    p.append(T(C[0] - 16, C[1] - 4, "C", size=14))
    p.append(T(D[0] + 14, D[1] + 4, "D", size=14))
    p.append(T(E[0] - 12, E[1] + 18, "E", size=14))
    return SVG(340, 270, p, "AB 是直径，BD 为切线，CE ⊥ AB")


def f_bn9_031():
    """9b031 矩形内动点 P 满足 AP = 4（隐圆）"""
    p = []
    A, B, C, D = (60, 210), (240, 210), (240, 50), (60, 50)   # 6×8 按 30px/单位 → 180×160
    p.append(PL([A, B, C, D], close=True, w=2))
    # 以 A 为圆心、4（120px）为半径的圆弧（矩形内部分）
    arc = [P(0 + 1.0 * i, 120, A[0], A[1]) for i in range(91)]
    p.append(PL(arc, color=GRAY, dash="5 3"))
    P_ = (A[0] + 120 * 0.6, A[1] - 120 * 0.8)   # 弧上一点
    p.append(L(*A, *C, dash="4 3", color=GRAY))
    p.append(DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*P_))
    p.append(T(A[0] - 14, A[1] + 18, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 18, "B", size=14))
    p.append(T(C[0] + 12, C[1] - 4, "C", size=14))
    p.append(T(D[0] - 12, D[1] - 4, "D", size=14))
    p.append(T(P_[0] - 14, P_[1] - 8, "P", size=14))
    return SVG(300, 250, p, "矩形 ABCD 内动点 P 满足 AP = 4")


def f_bn9_032():
    """9b032 以 AB 为直径的圆，C、P 在圆上"""
    p = []
    A, B = (70, 220), (270, 220)
    cx, cy, r = 170, 220, 100
    C = (170 - 100 * 0.6, 220 - 100 * 0.8)     # 圆上一点，∠ACB = 90°
    P_ = (170 + 100 * 0.6, 220 - 100 * 0.8)
    p.append(CI(cx, cy, r))
    p.append(L(*A, *B, w=2))
    p.append(L(*A, *C, w=2) + L(*B, *C, w=2))
    p.append(L(*A, *P_, color=GRAY) + L(*B, *P_, color=GRAY))
    p.append(L(*C, *P_, dash="4 3", color=GRAY))
    p.append(DOT(cx, cy) + DOT(*A) + DOT(*B) + DOT(*C) + DOT(*P_))
    p.append(T(cx - 2, cy + 20, "M", size=13))
    p.append(T(A[0] - 14, A[1] + 6, "A", size=14))
    p.append(T(B[0] + 12, B[1] + 6, "B", size=14))
    p.append(T(C[0] - 14, C[1] - 6, "C", size=14))
    p.append(T(P_[0] + 14, P_[1] - 6, "P", size=14))
    return SVG(340, 260, p, "以 AB 为直径的圆，C、P 都在圆上")


def f_bn9_033():
    """9b033 双曲线上的点 A，矩形 OBAC，D 为 AC 中点"""
    p = []
    ox, oy, sc = 80, 240, 42
    p.append(L(40, oy, 300, oy, w=1.6) + L(ox, 40, ox, oy, w=1.6))
    p.append(T(306, oy + 4, "x", size=12, anchor="start"))
    p.append(T(ox - 8, 36, "y", size=12, anchor="end"))
    p.append(T(ox - 10, oy + 16, "O", size=13))
    pts = [(ox + sc * x, oy - sc * (6.0 / x)) for x in [0.7 + 0.12 * i for i in range(34)]]
    pts = [(x, y) for x, y in pts if 34 < y < oy]
    p.append(PL(pts, w=2))
    A = (ox + 2 * sc, oy - 3 * sc)
    B, C = (A[0], oy), (ox, A[1])
    D = ((A[0] + C[0]) / 2.0, A[1])
    p.append(PL([(ox, oy), B, A, C], close=True, color=GRAY))
    p.append(L(ox, oy, *B, w=2) + L(ox, oy, *D, w=2))
    p.append(L(*D, *B, w=2))
    p.append(RA(ox, oy, 1, 0, 8))
    p.append(DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D))
    p.append(T(A[0] + 12, A[1] - 8, "A", size=13))
    p.append(T(B[0] + 4, B[1] + 18, "B", size=13))
    p.append(T(C[0] - 12, C[1] - 4, "C", size=13))
    p.append(T(D[0] - 6, D[1] - 10, "D", size=13))
    return SVG(320, 280, p, "双曲线上一点 A 与矩形 OBAC，D 为 AC 中点")


# ---- 补图：题干写了「如图」但原来没图的四道九上题 ----

def f_bn013():
    """bn013 正方形四角剪去全等等腰直角三角形，剩下正八边形"""
    p = []
    x0, y0, s = 60, 30, 160
    x1, y1 = x0 + s, y0 + s
    d = s * (1 - 1 / math.sqrt(2))      # 每个角沿两边各剪掉的长度
    # 原正方形用浅灰虚线保留，让人看出「剪掉」的是四个角
    p.append(PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dash="4 4", color=GRAY))
    oct_pts = [
        (x0 + d, y0), (x1 - d, y0), (x1, y0 + d), (x1, y1 - d),
        (x1 - d, y1), (x0 + d, y1), (x0, y1 - d), (x0, y0 + d),
    ]
    p.append(PL(oct_pts, close=True, w=2))
    p.append(T(x0 - 14, y0 - 6, "A", size=13))
    p.append(T(x1 + 14, y0 - 6, "B", size=13))
    p.append(T(x1 + 14, y1 + 16, "C", size=13))
    p.append(T(x0 - 14, y1 + 16, "D", size=13))
    return SVG(280, 220, p, "正方形四角剪去全等三角形后剩下的正八边形")


def f_bn026():
    """bn026 平行四边形 ABCD，E、F 在 BD 的延长线上且 DE = BF"""
    p = []
    A, B = (50, 60), (190, 60)
    D, C = (100, 170), (240, 170)
    O = ((A[0] + C[0]) / 2.0, (A[1] + C[1]) / 2.0)
    E = (D[0] + 0.38 * (D[0] - B[0]), D[1] + 0.38 * (D[1] - B[1]))
    F = (B[0] + 0.38 * (B[0] - D[0]), B[1] + 0.38 * (B[1] - D[1]))
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(*E, *F, w=1.5))                 # BD 及其两端延长线
    p.append(L(*A, *C, w=1.5))
    p.append(L(*A, *E, w=1.5) + L(*C, *F, w=1.5))
    p.append(DOT(*A) + DOT(*B) + DOT(*C) + DOT(*D) + DOT(*O) + DOT(*E) + DOT(*F))
    p.append(T(A[0] - 12, A[1] - 4, "A", size=13))
    p.append(T(B[0] - 13, B[1] - 5, "B", size=13))   # 右边是 B→F 的线，标签放左侧
    p.append(T(C[0] + 12, C[1] + 6, "C", size=13))
    p.append(T(D[0] + 12, D[1] + 12, "D", size=13))
    p.append(T(O[0] - 2, O[1] - 13, "O", size=13))   # 两条对角线夹出的空当里，不压线
    p.append(T(E[0] - 10, E[1] + 14, "E", size=13))
    p.append(T(F[0] + 10, F[1] + 4, "F", size=13))
    return SVG(300, 240, p, "平行四边形 ABCD 与 BD 延长线上的 E、F")


def f_bn029():
    """bn029 四边形 ABCD 各边中点 E、F、G、H 连成中点四边形"""
    p = []
    A, B, C, D = (50, 40), (200, 30), (250, 140), (90, 175)
    E = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
    F = ((B[0] + C[0]) / 2.0, (B[1] + C[1]) / 2.0)
    G = ((C[0] + D[0]) / 2.0, (C[1] + D[1]) / 2.0)
    H = ((D[0] + A[0]) / 2.0, (D[1] + A[1]) / 2.0)
    p.append(PL([A, B, C, D], close=True, w=2))
    p.append(L(*A, *C, dash="5 4", color=GRAY) + L(*B, *D, dash="5 4", color=GRAY))
    p.append(PL([E, F, G, H], close=True, w=2, color=GRAY))
    for pt in (A, B, C, D):
        p.append(DOT(*pt))
    for pt in (E, F, G, H):
        p.append(DOT(*pt, r=2.0))
    p.append(T(A[0] - 12, A[1] + 2, "A", size=13))
    p.append(T(B[0] + 12, B[1] + 2, "B", size=13))
    p.append(T(C[0] + 12, C[1] + 8, "C", size=13))
    p.append(T(D[0] - 10, D[1] + 14, "D", size=13))
    p.append(T(E[0], E[1] - 10, "E", size=13))
    p.append(T(F[0] + 12, F[1] + 2, "F", size=13))
    p.append(T(G[0] + 6, G[1] + 16, "G", size=13))
    p.append(T(H[0] - 14, H[1] + 2, "H", size=13))
    return SVG(300, 220, p, "四边形 ABCD 与各边中点连成的中点四边形")


def f_bn030():
    """bn030 黄金分割点 C，正方形 ACDE 与等面积矩形 BCFG"""
    p = []
    ax, ay, ab = 50, 250, 200
    # AC/AB = (√5−1)/2
    ac = ab * (math.sqrt(5) - 1) / 2.0
    A, B, C = (ax, ay), (ax + ab, ay), (ax + ac, ay)
    # 矩形高 = AC² / BC，正好等于 AB
    h = ac * ac / (ab - ac)
    E, D = (A[0], ay - ac), (C[0], ay - ac)
    G, F = (B[0], ay - h), (C[0], ay - h)
    p.append(PL([A, C, D, E], close=True, w=2))
    p.append(PL([C, B, G, F], close=True, w=2))
    p.append(L(*A, *B, w=2))
    p.append(DOT(*A) + DOT(*B) + DOT(*C))
    p.append(T(A[0] - 12, A[1] + 16, "A", size=13))
    p.append(T(B[0] + 12, B[1] + 16, "B", size=13))
    p.append(T(C[0], C[1] + 18, "C", size=13))
    p.append(T(E[0] - 12, E[1] + 4, "E", size=13))
    p.append(T(D[0] + 14, D[1] + 4, "D", size=13))
    p.append(T(F[0] + 14, F[1] + 4, "F", size=13))
    p.append(T(G[0] + 14, G[1] + 4, "G", size=13))
    return SVG(300, 290, p, "黄金分割点 C，正方形 ACDE 与等面积矩形 BCFG")


FIGS = {
    "sh_228_2": f_fence_wall,
    "sh_236_2": f_arch_bridge,
    "sh_232_1": f_parabola_basic,
    "sh_232_2": f_parabola_tri,
    "sh_239_1": f_inverse_k,
    "sh_245_1": f_rotation,
    "sh_247_1": f_square_rotate,
    "sh_251_1": f_chord,
    "sh_253_1": f_inscribed_angle,
    "sh_255_1": f_cyclic_quad,
    "sh_257_1": f_sector,
    "sh_258_1": f_cone,
    "sh_262_1": f_tangent_prop,
    "sh_263_1": f_tangent_len,
    "sh_264_1": f_incircle,
    "sh_265_1": f_circumcircle,
    "sh_271_1": f_similar,
    "sh_279_1": f_elevation,
    "sh_280_1": f_slope,
    "sh_289_1": f_spinner,
    # ---- 北师大九上提高题 ----
    "bn_003": f_bn003,
    "bn_013": f_bn013,
    "bn_023": f_bn023,
    "bn_024": f_bn024,
    "bn_026": f_bn026,
    "bn_027": f_bn027,
    "bn_028": f_bn028,
    "bn_029": f_bn029,
    "bn_030": f_bn030,
    "bn_032": f_bn032,
    "bn_033": f_bn033,
    # ---- 北师大九下提高题 ----
    "bn9_001": f_bn9_001,
    "bn9_004": f_bn9_004,
    "bn9_007": f_bn9_007,
    "bn9_009": f_bn9_009,
    "bn9_011": f_bn9_011,
    "bn9_019": f_bn9_019,
    "bn9_020": f_bn9_020,
    "bn9_021": f_bn9_021,
    "bn9_022": f_bn9_022,
    "bn9_023": f_bn9_023,
    "bn9_024": f_bn9_024,
    "bn9_025": f_bn9_025,
    "bn9_026": f_bn9_026,
    "bn9_027": f_bn9_027,
    "bn9_028": f_bn9_028,
    "bn9_029": f_bn9_029,
    "bn9_030": f_bn9_030,
    "bn9_031": f_bn9_031,
    "bn9_032": f_bn9_032,
    "bn9_033": f_bn9_033,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/sh-figs.json")
    ap.add_argument("--sh", default="data/sh-questions.json")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    out = {}
    for qid, fn in FIGS.items():
        out[qid] = fn()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("题图: %d 张 -> %s" % (len(out), args.out))

    if args.preview:
        with open(args.sh, encoding="utf-8") as f:
            qs = {q["id"]: q for q in json.load(f)}
        cells = []
        for qid in FIGS:
            q = qs.get(qid, {})
            cells.append(
                '<figure><div class="fig-box">%s</div>'
                '<figcaption><b>%s</b><br>%s</figcaption></figure>'
                % (out[qid], qid, q.get("prompt", "")[:46]))
        html = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<title>题图预览</title><style>'
                'body{font:14px/1.6 system-ui,-apple-system,"PingFang SC",sans-serif;'
                'background:#f4f3f0;margin:0;padding:24px;color:#2b2b2b}'
                'h1{font-size:18px;margin:0 0 18px}'
                '.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}'
                'figure{margin:0;background:#fff;border:1px solid #e3e0da;border-radius:10px;'
                'padding:12px;display:flex;flex-direction:column}'
                '.fig-box{height:230px;display:flex;align-items:center;justify-content:center}'
                '.fig-box svg{max-width:100%%;max-height:220px}'
                'figcaption{font-size:12px;color:#666;border-top:1px solid #eee;padding-top:8px}'
                '</style></head><body><h1>题图预览 · %d 张</h1><div class="grid">%s</div>'
                '</body></html>' % (len(out), "".join(cells)))
        with open("figs-preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("预览: figs-preview.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
