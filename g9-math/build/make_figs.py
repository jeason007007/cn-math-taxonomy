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
