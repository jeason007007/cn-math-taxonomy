# -*- coding: utf-8 -*-
"""
客观题题图：按题目里给出的数字算出坐标再画，保证图和题干一致。

用法:
    python build/make_figs_obj.py --preview
产出:
    data/obj-figs.json   {qid: "<svg .../>"}
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_figs import P, L, PL, CI, DOT, T, ARC, RA, SVG, INK, GRAY  # noqa: E402

RED = "#c0392b"
BLUE = "#1f6fb2"


# ---------------- 通用：坐标轴 + 曲线 ----------------

def plot(curves, xr, yr, w=340, h=214, pad=(46, 18, 24, 26),
         xticks=(), yticks=(), marks=(), extra=(), xlabel="x", ylabel="y",
         overlay=None):
    """curves: [[(x,y),...]]；xr/yr: (min,max) 显示范围

    extra 里的元素按**像素坐标**直接拼进 SVG；要按数学坐标画辅助线请用
    overlay=(sx, sy) -> [svg, ...]，plot 会把坐标换算好再交给你。
    """
    l, t, r, b = pad
    iw, ih = w - l - r, h - t - b
    sx = lambda x: l + (x - xr[0]) / (xr[1] - xr[0]) * iw
    sy = lambda y: t + (yr[1] - y) / (yr[1] - yr[0]) * ih
    p = []

    # 坐标轴
    if xr[0] <= 0 <= xr[1]:
        p.append(L(sx(0), t, sx(0), t + ih, w=1.2))
        p.append(T(sx(0) - 9, t + 12, ylabel, size=12))
    if yr[0] <= 0 <= yr[1]:
        p.append(L(l, sy(0), l + iw, sy(0), w=1.2))
        p.append(T(l + iw - 4, sy(0) - 8, xlabel, anchor="end", size=12))

    for x in xticks:
        p.append(L(sx(x), sy(0) - 3, sx(x), sy(0) + 3, w=1.2))
        p.append(T(sx(x), sy(0) + 16, "%g" % x, size=10, color=GRAY))
    for y in yticks:
        p.append(L(sx(0) - 3, sy(y), sx(0) + 3, sy(y), w=1.2))
        p.append(T(sx(0) - 8, sy(y) + 4, "%g" % y, anchor="end", size=10, color=GRAY))

    for cv in curves:
        pts = [(sx(x), sy(y)) for (x, y) in cv
               if xr[0] - 0.01 <= x <= xr[1] + 0.01 and yr[0] - 0.01 <= y <= yr[1] + 0.01]
        if len(pts) > 1:
            p.append(PL(pts, w=2.1, color=BLUE))

    for (x, y, lab, dx, dy) in marks:
        p.append(DOT(sx(x), sy(y)))
        p.append(T(sx(x) + dx, sy(y) + dy, lab, size=12, color=RED))
    if overlay:
        p.extend(overlay(sx, sy))
    for e in extra:
        p.append(e)
    return SVG(w, h, p, "函数图象")


def poly(f, x0, x1, n=120):
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        out.append((x, f(x)))
    return out


# ---------------- 圆 ----------------

def circle_base(cx=170, cy=112, r=86):
    return [CI(cx, cy, r)]


def arc_between(V, P1, P2, r):
    """在顶点 V 处，画 P1、P2 两条边之间的劣角弧。返回 (起点角, 终点角, 中点角)"""
    a1 = math.degrees(math.atan2(-(P1[1] - V[1]), P1[0] - V[0])) % 360
    a2 = math.degrees(math.atan2(-(P2[1] - V[1]), P2[0] - V[0])) % 360
    span = (a2 - a1) % 360
    if span <= 180:
        return a1, a1 + span, a1 + span / 2
    span = 360 - span
    return a2, a2 + span, a2 + span / 2


def fig_central_inscribed(central, c_on="major", inscribed=None, central_label=None):
    """圆心角 central；弦 AB 水平放在下方，C 在优弧（上）或劣弧（下）上"""
    cx, cy, r = 170, 116, 88
    half = central / 2.0
    g = (180 - central) / 2.0          # 弦 AB 相对水平的位置
    A = P(270 - half, r, cx, cy)
    B = P(270 + half, r, cx, cy)
    C = P(90, r, cx, cy) if c_on == "major" else P(270, r, cx, cy)
    p = [CI(cx, cy, r)]
    p.append(L(cx, cy, *A, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *B, dash="4 4", color=GRAY))
    p.append(L(*A, *B, dash="4 4", color=GRAY))
    p.append(L(*C, *A, w=1.8))
    p.append(L(*C, *B, w=1.8))
    # 圆心角
    s, e, mid = arc_between((cx, cy), A, B, 34)
    p.append(ARC(cx, cy, 34, s, e))
    cmid = mid if c_on == "major" else mid - 70
    p.append(T(*P(cmid, 50, cx, cy), central_label or ("%g°" % central), size=10))
    # 圆周角
    s2, e2, mid2 = arc_between(C, A, B, 28)
    p.append(ARC(C[0], C[1], 28, s2, e2))
    p.append(T(*P(mid2, 46, C[0], C[1]), inscribed or "?", size=11, color=RED))
    for pt, lab, dx, dy in [((cx, cy), "O", 11, 14), (A, "A", -13, 8),
                            (B, "B", 13, 8), (C, "C", 0, -10 if c_on == "major" else 18)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 226, p, "圆心角与圆周角")


def fig_diameter(angle_a=None, ac=None, ab=None, radius=86, show_angle=True, bc=None):
    """AB 为直径，C 在圆上，∠CAB=angle_a"""
    cx, cy = 170, 118
    A = (cx - radius, cy)
    B = (cx + radius, cy)
    a = angle_a if angle_a is not None else 40
    C = P(180 - 2 * a, radius, cx, cy)
    p = [CI(cx, cy, radius)]
    p.append(L(*A, *B, w=2.0))
    p.append(L(*A, *C, w=1.8))
    p.append(L(*B, *C, w=1.8))
    p.append(RA(C[0], C[1], (A[0] - C[0]) / 200.0, (A[1] - C[1]) / 200.0, 9))
    if angle_a is not None:
        s, e, mid = arc_between(A, C, B, 34)
        p.append(ARC(A[0], A[1], 34, s, e))
        p.append(T(*P(mid, 50, A[0], A[1]), "%g°" % round(a, 1), size=10))
    if ac:
        p.append(T((A[0] + C[0]) / 2 - 16, (A[1] + C[1]) / 2, str(ac), size=11))
    if bc:
        p.append(T((B[0] + C[0]) / 2 + 12, (B[1] + C[1]) / 2, str(bc), size=11))
    if ab:
        p.append(T((A[0] + B[0]) / 2 + 30, cy + 20, str(ab), size=11))
    for pt, lab, dx, dy in [((cx, cy), "O", -4, 18), (A, "A", -13, 6),
                            (B, "B", 13, 6), (C, "C", 0, -10)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "直径所对的圆周角")


def fig_cyclic(arcs=(), extend=False, bod=None):
    """圆内接四边形 ABCD；arcs: [(顶点, 边1端点, 边2端点, 文字)]"""
    cx, cy, r = 170, 112, 84
    A = P(95, r, cx, cy)
    B = P(340, r, cx, cy)
    C = P(250, r, cx, cy)
    D = P(170, r, cx, cy)
    pts = {"A": A, "B": B, "C": C, "D": D}
    p = [CI(cx, cy, r)]
    p.append(PL([A, B, C, D], close=True, w=2.0))
    if extend:
        dx, dy = C[0] - B[0], C[1] - B[1]
        n = math.hypot(dx, dy)
        E = (C[0] + dx / n * 44, C[1] + dy / n * 44)
        pts["E"] = E
        p.append(L(C[0], C[1], E[0], E[1], dash="5 4", color=GRAY))
        p.append(DOT(*E, 2.0))
        p.append(T(E[0] + 10, E[1] + 6, "E"))
    if bod:
        p.append(L(cx, cy, *B, dash="4 4", color=GRAY))
        p.append(L(cx, cy, *D, dash="4 4", color=GRAY))
        s, e, mid = arc_between((cx, cy), B, D, 32)
        p.append(ARC(cx, cy, 32, s, e))
        p.append(T(*P(mid, 46, cx, cy), "%g°" % bod, size=10))
    for (v, p1, p2, label) in arcs:
        V = pts[v]
        s, e, mid = arc_between(V, pts[p1], pts[p2], 26)
        p.append(ARC(V[0], V[1], 26, s, e))
        p.append(T(*P(mid, 46, V[0], V[1]), label, size=10, color=RED))
    pos = {"A": (A, -4, -10), "B": (B, 13, 6), "C": (C, 6, 17), "D": (D, -14, 6)}
    for k in "ABCD":
        pt, dx, dy = pos[k]
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, k))
    p.append(DOT(cx, cy, 2.0))
    p.append(T(cx + 11, cy + 14, "O"))
    return SVG(340, 232, p, "圆内接四边形")


def fig_sector(radius_label, angle, arc_label=None, show_radius=True, angle_label=None):
    """扇形，圆心角 angle"""
    cx, cy, R = 170, 192, 120
    d1, d2 = 90 - angle / 2.0, 90 + angle / 2.0
    p = [ARC(cx, cy, R, d1, d2)]
    p.append(L(cx, cy, *P(d1, R, cx, cy), w=1.8))
    p.append(L(cx, cy, *P(d2, R, cx, cy), w=1.8))
    p.append(ARC(cx, cy, 30, d1, d2))
    p.append(T(*P(90, 46, cx, cy), angle_label or ("%g°" % angle), size=10))
    if show_radius:
        p.append(T(*P(d1 + 10, R * 0.58, cx, cy), str(radius_label), size=11))
    if arc_label:
        p.append(T(*P(90, R + 16, cx, cy), str(arc_label), size=11, color=BLUE))
    p.append(DOT(cx, cy))
    p.append(T(cx - 11, cy + 16, "O"))
    return SVG(340, 216, p, "扇形")


def fig_square_arc(a):
    """正方形 ABCD，以 A 为圆心、边长 a 为半径作弧 BD"""
    side = 160
    A = (92, 48)
    B = (92 + side, 48)
    C = (92 + side, 48 + side)
    D = (92, 48 + side)
    p = [PL([A, B, C, D], close=True, w=2.0)]
    # 弧 BD（从 B 到 D，圆心 A，半径 side）
    p.append('<path d="M%.1f,%.1f A%d,%d 0 0 0 %.1f,%.1f" fill="none" stroke="%s" '
             'stroke-width="1.8"/>' % (B[0], B[1], side, side, D[0], D[1], BLUE))
    p.append(L(D[0], D[1], B[0], B[1], dash="5 4", color=GRAY))
    for pt, lab, dx, dy in [(A, "A", -13, -6), (B, "B", 12, -6),
                            (C, "C", 12, 14), (D, "D", -13, 14)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(T(A[0] + 34, A[1] + 52, "4", size=11))
    return SVG(340, 236, p, "正方形中的弧")


def fig_cone(r, l=None, h=None, top_note=None):
    cx, apex, by = 170, 48, 172
    rx, ry = 84, 20
    p = [L(cx, apex, cx - rx, by, w=1.8), L(cx, apex, cx + rx, by, w=1.8)]
    p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d"/>' % (cx, by, rx, ry))
    p.append('<path d="M%d,%d A%d,%d 0 0 0 %d,%d" fill="none"/>'
             % (cx + rx, by, rx, ry, cx - rx, by))
    p.append(L(cx, apex, cx, by, dash="5 4", color=GRAY))
    if l:
        p.append(T(cx + 44, (apex + by) / 2, str(l), size=11, color=BLUE))
    if h:
        p.append(T(cx + 8, (apex + by) / 2, str(h), size=11, color=GRAY))
    p.append(T(cx, by + 36, str(r), size=11, color=BLUE))
    if top_note:
        p.append(T(cx, apex - 12, top_note, size=11, color=GRAY))
    p.append(DOT(cx, apex))
    return SVG(340, 212, p, "圆锥")


# ---------------- 三角 / 坡度 ----------------

def fig_slope(vi, vh, hyp=None, angle_label=None, ratio_note=None):
    """铅直 vi : 水平 vh"""
    base, top = 200, 104
    x0, y0 = 74, 186
    x1 = x0 + base
    y1 = y0
    y2 = y0 - top
    p = [PL([(x0, y0), (x1, y1), (x1, y2)], close=True, w=2.0)]
    p.append(RA(x1, y1, -1, 0, 10))
    p.append(T((x0 + x1) / 2, y0 + 17, str(vh), size=11, color=GRAY))
    p.append(T(x1 + 10, (y1 + y2) / 2 + 4, str(vi), size=11, anchor="start", color=GRAY))
    if hyp:
        p.append(T((x0 + x1) / 2 - 26, (y0 + y2) / 2 + 2, str(hyp), size=11))
    if angle_label:
        p.append(ARC(x0, y0, 42, 0, math.degrees(math.atan2(top, base))))
        p.append(T(*P(math.degrees(math.atan2(top, base)) / 2, 58, x0, y0),
                   str(angle_label), size=11))
    if ratio_note:
        p.append(T(170, 208, ratio_note, size=11, color=GRAY))
    p.append(DOT(x0, y0) + DOT(x1, y2))
    return SVG(340, 234, p, "坡度")


def fig_dam(ad, height, s1, s2, note=None):
    """梯形坝：坝顶 AD，坝高 h，迎水坡 1:s1，背水坡 1:s2"""
    scale = 17.0
    left = 40 + (s1 * height * scale) * 0.0
    base_y = 190
    xa = 40 + s1 * height * scale
    xd = xa + ad * scale
    p = []
    A = (xa, base_y - height * scale)
    D = (xd, base_y - height * scale)
    B = (40, base_y)
    C = (xd + s2 * height * scale, base_y)
    p.append(PL([A, B, C, D], close=True, w=2.0))
    p.append(L(A[0], A[1], A[0], base_y, dash="5 4", color=GRAY))
    p.append(L(D[0], D[1], D[0], base_y, dash="5 4", color=GRAY))
    p.append(RA(A[0], base_y, 1, 0, 9))
    p.append(T((A[0] + D[0]) / 2, A[1] - 10, "AD=%g" % ad, size=11))
    p.append(T(A[0] - 8, (A[1] + base_y) / 2, "%g" % height, anchor="end", size=11, color=GRAY))
    p.append(T((A[0] + B[0]) / 2 - 18, (A[1] + base_y) / 2 + 4, "1:%g" % s1, size=10, color=BLUE))
    p.append(T((C[0] + D[0]) / 2 + 16, (C[1] + base_y) / 2 + 4, "1:%g" % s2, size=10, color=BLUE))
    for pt, lab, dx, dy in [(A, "A", -12, -4), (B, "B", -12, 14),
                            (C, "C", 10, 14), (D, "D", 10, -4)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    if note:
        p.append(T(170, 214, note, size=11, color=GRAY))
    return SVG(340, 226, p, "梯形坝横截面")


def fig_similar(k1, k2, note=None):
    """两个相似三角形，相似比 k1:k2"""
    s1, s2 = 92.0, 92.0 * k2 / k1
    ax, ay = 36, 190
    A = (ax, ay)
    B = (ax + s1, ay)
    C = (ax + s1 * 0.42, ay - s1 * 0.86)
    bx = ax + s1 + 34
    A2 = (bx, ay)
    B2 = (bx + s2, ay)
    C2 = (bx + s2 * 0.42, ay - s2 * 0.86)
    p = [PL([A, B, C], close=True, w=2.0), PL([A2, B2, C2], close=True, w=2.0, color=BLUE)]
    for pt, lab, dx, dy in [(A, "A", -13, 12), (B, "B", 8, 14), (C, "C", 0, -10)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    for pt, lab, dx, dy in [(A2, "D", -13, 12), (B2, "E", 8, 14), (C2, "F", 0, -10)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(T(170, 228, note or ("相似比 %g∶%g" % (k1, k2)), size=11, color=GRAY))
    return SVG(340, 240, p, "相似三角形")


# ---------------- 切线 / 直线与圆 ----------------

def fig_tangent(r, pa=None, angle_p=None, angle_aop=None):
    """PA 切⊙O 于 A"""
    cx, cy = 122, 128
    R = 74
    A = (cx, cy - R)
    Pp = (A[0] + 130, A[1])
    p = [CI(cx, cy, R)]
    p.append(L(40, A[1], 300, A[1], w=1.8))
    p.append(L(cx, cy, *A, w=1.5, color=BLUE))
    p.append(L(cx, cy, *Pp, w=1.5))
    p.append(RA(A[0], A[1], 1, 0, 10))
    if angle_p is not None:
        p.append(ARC(Pp[0], Pp[1], 42, 180, 180 + angle_p))
        p.append(T(*P(180 + angle_p / 2, 56, Pp[0], Pp[1]), "%g°" % angle_p, size=10))
    if angle_aop is not None:
        p.append(ARC(cx, cy, 30, 0, angle_aop))
        p.append(T(*P(angle_aop / 2, 44, cx, cy), "%g°" % angle_aop, size=10))
    p.append(T(A[0] - 13, A[1] - 8, "A"))
    p.append(T(Pp[0] + 8, Pp[1] - 8, "P"))
    p.append(T(cx + 6, cy + 17, "O"))
    if pa:
        p.append(T((A[0] + Pp[0]) / 2, A[1] - 10, str(pa), size=11, color=BLUE))
    p.append(DOT(*A) + DOT(*Pp) + DOT(cx, cy))
    return SVG(340, 214, p, "切线的性质")


def fig_two_tangents(r, angle_p, pa=None):
    """PA、PB 切⊙O 于 A、B，∠APB=angle_p"""
    cx, cy = 170, 108
    R = 66
    d = R / math.sin(math.radians(angle_p / 2))
    Pp = (cx, cy + d)
    hh = int(cy + d + 30)
    A = P(-90 + angle_p / 2, R, cx, cy)
    B = P(-90 - angle_p / 2, R, cx, cy)
    p = [CI(cx, cy, R)]
    p.append(L(*Pp, *A, w=1.8))
    p.append(L(*Pp, *B, w=1.8))
    p.append(L(cx, cy, *A, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *B, dash="4 4", color=GRAY))
    p.append(L(cx, cy, *Pp, w=1.2, dash="4 4", color=GRAY))
    p.append(ARC(Pp[0], Pp[1], 32, 90 - angle_p / 2, 90 + angle_p / 2))
    p.append(T(*P(90, 28, Pp[0], Pp[1]), "%g°" % angle_p, size=10))
    for pt, lab, dx, dy in [(A, "A", 12, -4), (B, "B", -12, -4), (Pp, "P", 0, 18)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(DOT(cx, cy))
    p.append(T(cx + 12, cy - 8, "O"))
    if pa:
        p.append(T((A[0] + Pp[0]) / 2 + 12, (A[1] + Pp[1]) / 2, str(pa), size=11, color=BLUE))
    return SVG(340, hh, p, "切线长定理")


def fig_line_circle(r, d, r_label=None):
    """圆心到直线距离 d，半径 r"""
    cx, cy = 170, 120
    R = 74
    ly = cy + d / max(r, 1) * R
    p = [CI(cx, cy, R)]
    p.append(L(50, ly, 292, ly, w=1.9))
    p.append(L(cx, cy, cx, ly, dash="5 4", color=BLUE))
    p.append(RA(cx, ly, 1, 0, 9))
    p.append(T(cx + 10, (cy + ly) / 2 + 4, "d=%g" % d, anchor="start", size=11, color=BLUE))
    p.append(T(cx - R / 2 - 6, cy - 8, r_label or ("r=%g" % r), size=11, color=GRAY))
    p.append(DOT(cx, cy))
    p.append(T(cx + 10, cy + 16, "O"))
    p.append(T(286, ly - 9, "l", anchor="end"))
    return SVG(340, 216, p, "直线与圆的位置关系")


def fig_circle_axes(x0, y0, r):
    """坐标系中的圆，圆心 (x0,y0)，等比例缩放"""
    xr = (-1, max(x0 + r + 1, 8))
    yr = (-1, max(y0 + r + 1, 8))
    k = min(240.0 / (xr[1] - xr[0]), 168.0 / (yr[1] - yr[0]))
    ox, oy = 56, 196
    sx = lambda x: ox + (x - xr[0]) * k
    sy = lambda y: oy - (y - yr[0]) * k
    p = [L(ox - 14, sy(0), ox + 262, sy(0), w=1.2),
         L(sx(0), oy + 14, sx(0), 20, w=1.2)]
    p.append(T(ox + 258, sy(0) - 8, "x", anchor="end", size=12))
    p.append(T(sx(0) + 10, 30, "y", size=12))
    p.append(CI(sx(x0), sy(y0), r * k))
    p.append(L(sx(x0), sy(y0), sx(x0), sy(0), dash="4 4", color=GRAY))
    p.append(L(sx(x0), sy(y0), sx(0), sy(y0), dash="4 4", color=GRAY))
    p.append(DOT(sx(x0), sy(y0), 2.2))
    p.append(T(sx(x0) + 8, sy(y0) - 7, "C(%g,%g)" % (x0, y0), anchor="start", size=10))
    for v, lab in [(x0, "x"), (y0, "y")]:
        pass
    return SVG(340, 220, p, "坐标系中的圆")


# ---------------- 函数图象 ----------------

def fig_parabola(a, b, c, marks=(), xticks=(), yticks=(), note=None):
    xv = -b / (2 * a) if a else 0
    yv = a * xv * xv + b * xv + c
    span = 3.2
    x0, x1 = xv - span, xv + span
    ys = [a * x * x + b * x + c for x in (x0, x1)]
    ylo = min(min(ys), yv, 0)
    yhi = max(max(ys), yv, 0)
    pad = (yhi - ylo) * 0.18 + 0.5
    yr = (ylo - pad, yhi + pad)
    if not xticks:
        xticks = sorted({round(xv, 2)})
    curves = [poly(lambda x: a * x * x + b * x + c, x0, x1)]
    extra = []
    if note:
        extra.append(T(300, 26, note, anchor="end", size=11, color=GRAY))
    return plot(curves, (x0, x1), yr, xticks=xticks, yticks=yticks, marks=marks, extra=extra)


def fig_hyperbola(k, marks=(), note=None):
    s = 1 if k > 0 else -1
    xm = math.sqrt(abs(k)) * 3.2
    curves = []
    for sgn in (1, -1):
        pts = []
        t = xm / 60.0
        while t <= xm:
            pts.append((sgn * t, k / (sgn * t)))
            t += xm / 60.0
        curves.append(pts)
    lim = abs(k) / (xm / 6.0)
    ys = [abs(y) for (_, y, _, _, _) in marks]
    xs = [abs(x) for (x, _, _, _, _) in marks]
    lim = max([lim] + [v * 1.35 for v in ys])
    xm = max([xm] + [v * 1.35 for v in xs])
    yr = (-lim, lim)
    extra = []
    if note:
        extra.append(T(300, 26, note, anchor="end", size=11, color=GRAY))
    return plot(curves, (-xm, xm), yr, marks=marks, extra=extra)


def fig_reflect(x, y):
    return plot([], (-abs(x) - 3, abs(x) + 3), (-abs(y) - 3, abs(y) + 3),
                marks=[(x, y, "P(%g,%g)" % (x, y), 6, -10),
                       (-x, -y, "P′(%g,%g)" % (-x, -y), 6, 16)],
                extra=[L(0, 0, 0, 0, w=0),
                       '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                       'stroke-dasharray="5 4" stroke="%s" stroke-width="1.3"/>'
                       % (60 + (x - (-abs(x) - 3)) / (2 * abs(x) + 6) * 250,
                          200 - (y - (-abs(y) - 3)) / (2 * abs(y) + 6) * 170,
                          60 + (-x - (-abs(x) - 3)) / (2 * abs(x) + 6) * 250,
                          200 - (-y - (-abs(y) - 3)) / (2 * abs(y) + 6) * 170, GRAY)])


def fig_rotate_point(deg, r_label="5"):
    """点 A 绕 O 旋转 deg"""
    cx, cy = 150, 176
    R = 108
    A = P(deg + 20, R, cx, cy)
    A2 = P(20, R, cx, cy)
    p = [L(cx, cy, *A, w=1.8), L(cx, cy, *A2, w=1.8, color=BLUE)]
    p.append(ARC(cx, cy, 40, 20, 20 + deg))
    p.append(T(*P(20 + deg / 2, 58, cx, cy), "%g°" % deg, size=10))
    p.append(T(*P(20 + deg + 8, R * 0.55, cx, cy), r_label, size=11, color=GRAY))
    for pt, lab, dx, dy in [(A, "A", 8, -8), (A2, "A′", 12, 6), ((cx, cy), "O", -14, 16)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 206, p, "点的旋转")


# ---------------- 第二批：垂径 / 内切圆 / 外接圆 / 仰角 / 车位 … ----------------

def _fit(pts, w=340, h=232, pad=30, flip=False):
    """把一组数学坐标等比缩放平移到画布中央（flip=True 时把 y 轴翻过来，让底边在下方）"""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bw, bh = max(xs) - min(xs) or 1, max(ys) - min(ys) or 1
    k = min((w - 2 * pad) / bw, (h - 2 * pad) / bh)
    ox = (w - bw * k) / 2 - min(xs) * k
    oy = (h - bh * k) / 2 - min(ys) * k
    if flip:
        return lambda p: (p[0] * k + ox, h - (p[1] * k + oy)), k
    return lambda p: (p[0] * k + ox, p[1] * k + oy), k


def circumcenter(A, B, C):
    ax, ay = A
    bx, by = B
    cx, cy = C
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax ** 2 + ay ** 2) * (by - cy) + (bx ** 2 + by ** 2) * (cy - ay)
          + (cx ** 2 + cy ** 2) * (ay - by)) / d
    uy = ((ax ** 2 + ay ** 2) * (cx - bx) + (bx ** 2 + by ** 2) * (ax - cx)
          + (cx ** 2 + cy ** 2) * (bx - ax)) / d
    return (ux, uy)


def fig_perpendicular_chord(radius, chord, d_label=False, mask=None):
    """⊙O 半径 radius，弦 AB=chord，OH⊥AB"""
    cx, cy, R = 170, 106, 84
    k = R / float(radius)
    half = chord / 2.0 * k
    d = math.sqrt(max(radius ** 2 - (chord / 2.0) ** 2, 0)) * k
    A = (cx - half, cy + d)
    B = (cx + half, cy + d)
    H = (cx, cy + d)
    p = [CI(cx, cy, R)]
    p.append(L(*A, *B, w=2.0))
    p.append(L(cx, cy, *A, w=1.3, color=GRAY))
    p.append(L(cx, cy, *H, dash="5 4", color=GRAY))
    p.append(RA(H[0], H[1], 0, -1, 8))
    p.append(T((cx + A[0]) / 2 - 2, (cy + A[1]) / 2 - 6,
               "?" if mask == "radius" else str(radius), size=11, color=BLUE))
    p.append(T(A[0] + half * 0.52, A[1] + 19,
               "?" if mask == "chord" else str(chord), size=11, color=BLUE))
    if d_label and d > 10:
        p.append(T(cx + 7, (cy + H[1]) / 2 + 4, "?", size=11, color=RED))
    for pt, lab, dx, dy in [((cx, cy), "O", -14, 15), (A, "A", -13, 5),
                            (B, "B", 13, 5), (H, "H", 12, 16)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "垂径定理")


def fig_parallel_chords(radius, c1, c2):
    """两条平行弦 AB、CD 分居圆心两侧"""
    cx, cy, R = 170, 116, 84
    k = R / float(radius)
    h1 = math.sqrt(max(radius ** 2 - (c1 / 2.0) ** 2, 0)) * k
    h2 = math.sqrt(max(radius ** 2 - (c2 / 2.0) ** 2, 0)) * k
    A = (cx - c1 / 2.0 * k, cy - h1)
    B = (cx + c1 / 2.0 * k, cy - h1)
    C = (cx - c2 / 2.0 * k, cy + h2)
    D = (cx + c2 / 2.0 * k, cy + h2)
    p = [CI(cx, cy, R)]
    p.append(L(*A, *B, w=2.0))
    p.append(L(*C, *D, w=2.0))
    p.append(L(cx, cy, *A, w=1.3, color=GRAY))
    p.append(L(cx, cy - h1, cx, cy + h2, dash="5 4", color=GRAY))
    p.append(RA(cx, cy - h1, 0, 1, 8))
    p.append(T((cx + A[0]) / 2 + 4, (cy + A[1]) / 2 - 4, str(radius), size=11, color=BLUE))
    p.append(T((A[0] + B[0]) / 2, A[1] - 8, str(c1), size=11, color=BLUE))
    p.append(T((C[0] + D[0]) / 2, C[1] + 18, str(c2), size=11, color=BLUE))
    for pt, lab, dx, dy in [((cx, cy), "O", -14, 15), (A, "A", -13, -4),
                            (B, "B", 13, -4), (C, "C", -13, 14), (D, "D", 13, 14)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 236, p, "两条平行弦")


def fig_incircle(a, b, c, note=None):
    """△ABC，三边 a=BC, b=CA, c=AB，画内切圆与 BC 上的切点 E"""
    B0 = (0.0, 0.0)
    C0 = (float(a), 0.0)
    x = (c ** 2 + a ** 2 - b ** 2) / (2.0 * a)
    A0 = (x, math.sqrt(max(c ** 2 - x ** 2, 0.01)))
    s = (a + b + c) / 2.0
    area = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.01))
    r = area / s
    I0 = ((a * A0[0] + b * B0[0] + c * C0[0]) / (a + b + c),
          (a * A0[1] + b * B0[1] + c * C0[1]) / (a + b + c))
    f, k = _fit([A0, B0, C0], flip=True)
    A, B, C, I = f(A0), f(B0), f(C0), f(I0)
    R = r * k
    p = [PL([A, B, C], close=True, w=2.0), CI(I[0], I[1], R)]
    Tp = (I[0], B[1])          # BC 上的切点
    p.append(L(I[0], I[1], *Tp, dash="4 4", color=GRAY))
    p.append(RA(Tp[0], Tp[1], 0, -1, 7))
    p.append(T(I[0] + 8, (I[1] + Tp[1]) / 2 + 4, "r", size=11, color=BLUE))
    p.append(DOT(*Tp))
    p.append(T(Tp[0] + 4, Tp[1] + 17, "E", size=12))
    # 直角三角形顺手把直角标出来
    for V, P1, P2 in ((A, B, C), (B, A, C), (C, A, B)):
        u1 = (P1[0] - V[0], P1[1] - V[1])
        u2 = (P2[0] - V[0], P2[1] - V[1])
        n1 = math.hypot(*u1) or 1
        n2 = math.hypot(*u2) or 1
        if abs(u1[0] * u2[0] + u1[1] * u2[1]) / (n1 * n2) < 0.02:
            p.append(RA(V[0], V[1], u1[0] / n1, u1[1] / n1, 9))
    for pt, lab, dx, dy in [(A, "A", 0, -11), (B, "B", -14, 14),
                            (C, "C", 14, 14), (I, "I", 6, 18)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    if note:
        p.append(T(170, 224, note, size=10, color=GRAY))
    return SVG(340, 236, p, "三角形的内切圆")


def fig_circumcircle(kind="right"):
    """直角三角形的外接圆 / 钝角三角形的外心"""
    if kind == "right":
        cx, cy, R = 170, 116, 84
        A = (cx - R, cy)
        B = (cx + R, cy)
        C = P(58, R, cx, cy)
        p = [CI(cx, cy, R), L(*A, *B, w=2.0), L(*A, *C, w=1.8), L(*B, *C, w=1.8)]
        p.append(RA(C[0], C[1], (A[0] - C[0]) / 190.0, (A[1] - C[1]) / 190.0, 9))
        p.append(T((A[0] + B[0]) / 2 + 26, cy + 18, "O", size=12))
        p.append(DOT(cx, cy))
        for pt, lab, dx, dy in [(A, "A", -13, 6), (B, "B", 13, 6), (C, "C", 0, -10)]:
            p.append(DOT(*pt))
            p.append(T(pt[0] + dx, pt[1] + dy, lab))
        p.append(T(170, 224, "O 是斜边的中点", size=10, color=GRAY))
        return SVG(340, 236, p, "直角三角形的外接圆")

    cx, cy, R = 170, 126, 88
    A = P(45, R, cx, cy)
    B = P(100, R, cx, cy)
    C = P(155, R, cx, cy)
    p = [CI(cx, cy, R), PL([A, B, C], close=True, w=2.0)]
    p.append(L(cx, cy, *B, dash="4 4", color=GRAY))
    p.append(DOT(cx, cy))
    p.append(T(cx - 15, cy + 16, "O", size=12))
    for pt, lab, dx, dy in [(A, "A", 10, 8), (B, "B", 0, -11), (C, "C", -12, 8)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(T(170, 228, "外心在三角形外", size=10, color=GRAY))
    return SVG(340, 236, p, "钝角三角形的外心")


def fig_elevation(angle, dist, eye=0.0, note=None):
    """在地面测得仰角 angle，水平距离 dist"""
    gx0, gx1, gy = 52, 300, 196
    px, py = 66, gy - (16 if eye else 0)
    bx = 258
    top = py - math.tan(math.radians(angle)) * (bx - px)
    top = max(top, 34)
    p = [L(gx0, gy, gx1, gy, w=1.6)]
    p.append(L(bx, gy, bx, top, w=2.0))
    if eye:
        p.append(L(px, gy, px, py, w=1.6))
        p.append(T(px - 8, (gy + py) / 2, "%.1f" % eye, anchor="end", size=10, color=GRAY))
    p.append(L(px, py, bx, top, w=1.6, color=BLUE))
    p.append(L(px, py, bx, py, dash="5 4", color=GRAY))
    p.append(ARC(px, py, 30, 0, angle))
    p.append(T(px + 40, py - 6, "%g°" % angle, size=10, color=RED))
    p.append(T((px + bx) / 2, py + 17, "%g m" % dist, size=11, color=BLUE))
    p.append(T(bx + 8, (gy + top) / 2, "?", anchor="start", size=12, color=RED))
    p.append(DOT(px, py))
    p.append(T(px - 4, py - 8, "眼" if eye else "O", size=11))
    if note:
        p.append(T(170, 224, note, size=10, color=GRAY))
    return SVG(340, 232, p, "仰角")


def fig_depression(height, tan_a, note=None):
    """从高 height 的楼顶看地面点 A，俯角 α，tanα=tan_a"""
    gx0, gx1, gy = 52, 310, 196
    bx = 78
    top = 52
    ax = bx + height / float(tan_a) * 9
    ax = min(ax, 300)
    p = [L(gx0, gy, gx1, gy, w=1.6), L(bx, gy, bx, top, w=2.0)]
    p.append(L(bx, top, ax, gy, w=1.6, color=BLUE))
    p.append(L(bx, top, ax, top, dash="5 4", color=GRAY))
    ang = math.degrees(math.atan2(gy - top, ax - bx))
    p.append(ARC(bx, top, 34, -ang, 0))
    p.append(T(bx + 44, top + 16, "α", size=11, color=RED))
    p.append(T(bx - 9, (gy + top) / 2, "%g m" % height, anchor="end", size=11, color=BLUE))
    p.append(T((bx + ax) / 2, gy + 18, "?", size=12, color=RED))
    p.append(DOT(bx, top))
    p.append(DOT(ax, gy))
    p.append(T(ax + 4, gy - 9, "A", size=12))
    if note:
        p.append(T(170, 224, note, size=10, color=GRAY))
    return SVG(340, 232, p, "俯角")


def fig_parking(theta, line_len=None, sep=None, ask="depth"):
    """斜列车位：车位线与行车道成锐角 theta"""
    road_y = 186
    x0 = 96
    Lp = 118
    a = math.radians(theta)
    tip = (x0 + Lp * math.cos(a), road_y - Lp * math.sin(a))
    p = [L(40, road_y, 310, road_y, w=2.2)]
    p.append(T(300, road_y + 18, "行车道", anchor="end", size=10, color=GRAY))
    p.append(L(x0, road_y, tip[0], tip[1], w=2.0))
    foot = (tip[0], road_y)
    p.append(L(tip[0], tip[1], *foot, dash="5 4", color=GRAY))
    p.append(RA(foot[0], foot[1], 0, -1, 8))
    # 角度弧（车位线与行车道）
    p.append(ARC(x0, road_y, 34, 0, theta))
    p.append(T(x0 + 46, road_y - 8, "%g°" % theta, size=10, color=RED))
    if ask == "depth":
        p.append(T(tip[0] + 8, (tip[1] + road_y) / 2, "?", anchor="start", size=12, color=RED))
        if line_len:
            p.append(T((x0 + tip[0]) / 2 - 14, (road_y + tip[1]) / 2 - 6,
                       "%g m" % line_len, size=11, color=BLUE))
    else:
        # 两条平行车位线，垂直间距 sep
        sep_px = sep * 8.6
        off = sep_px / math.sin(a)
        x1 = x0 + off
        tip2 = (x1 + Lp * math.cos(a), road_y - Lp * math.sin(a))
        p.append(L(x1, road_y, tip2[0], tip2[1], w=2.0))
        m1 = ((x0 + tip[0]) / 2, (road_y + tip[1]) / 2)
        m2 = (m1[0] + sep_px * math.sin(a), m1[1] + sep_px * math.cos(a))
        p.append(L(m1[0], m1[1], m2[0], m2[1], w=1.4, color=RED))
        p.append(RA(m2[0], m2[1], -math.sin(a), -math.cos(a), 7))
        p.append(T(m1[0] - 12, (m1[1] + m2[1]) / 2 + 4, "%g m" % sep,
                   anchor="end", size=11, color=BLUE))
        # 沿行车道方向占用的长度
        p.append(L(x0, road_y + 26, x1, road_y + 26, w=1.2, color=RED))
        p.append(L(x0, road_y + 21, x0, road_y + 31, w=1.2, color=RED))
        p.append(L(x1, road_y + 21, x1, road_y + 31, w=1.2, color=RED))
        p.append(T((x0 + x1) / 2, road_y + 44, "?", size=12, color=RED))
    p.append(DOT(x0, road_y))
    return SVG(340, 232, p, "斜列车位")


def fig_hyperbola_triangle(k, kind="tri"):
    """点 P 在 y=k/x 上，PA⊥x 轴于 A，求 △POA / 矩形 OAPB 面积"""
    px = 2.0
    py = k / px
    xr = (-4.6, 4.6)
    yr = (-abs(py) - 1.6, abs(py) + 1.6)
    marks = [(px, py, "P", 8, -8), (px, 0, "A", 2, 15)]
    if kind == "rect":
        marks.append((0, py, "B", -13, 4))

    def ov(sx, sy):
        o = [L(sx(0), sy(0), sx(px), sy(0), w=1.6),
             L(sx(px), sy(0), sx(px), sy(py), w=1.8, color=BLUE),
             L(sx(0), sy(0), sx(px), sy(py), w=1.6, color=BLUE)]
        if kind == "rect":
            o.append(L(sx(0), sy(py), sx(px), sy(py), w=1.8, color=BLUE))
        o.append(RA(sx(px), sy(0), -1, 0, 8))
        return o

    curve = poly(lambda x: k / x, 0.42, 4.4) if k > 0 else poly(lambda x: k / x, -4.4, -0.42)
    return plot([curve], xr, yr, marks=marks, overlay=ov, ylabel="y")


def fig_line_hyperbola(k=6, b=-1):
    """一次函数 y=x+b 与 y=k/x 交于 A、B，与 y 轴交于 C，求 △AOB"""
    disc = math.sqrt(b * b + 4 * k)
    x1 = (-b + disc) / 2
    x2 = (-b - disc) / 2
    y1, y2 = k / x1, k / x2
    marks = [(x1, y1, "A", 8, -6), (x2, y2, "B", -12, 14), (0, b, "C", -12, 12)]

    def ov(sx, sy):
        return [L(sx(x1), sy(y1), sx(x2), sy(y2), w=1.8, color=BLUE),
                L(sx(0), sy(b), sx(x1), sy(y1), w=1.8, color=BLUE),
                L(sx(0), sy(0), sx(x1), sy(y1), w=1.3, color=GRAY),
                L(sx(0), sy(0), sx(x2), sy(y2), w=1.3, color=GRAY),
                L(sx(x2), sy(0), sx(x2), sy(y2), dash="4 4", color=GRAY),
                L(sx(x1), sy(0), sx(x1), sy(y1), dash="4 4", color=GRAY)]

    return plot([poly(lambda x: k / x, 0.4, 5.2)], (-5.0, 5.4), (-4.6, 4.6),
                marks=marks, overlay=ov, ylabel="y")


def fig_rotate_on_side(angle_a):
    """△ABC 绕 C 旋转得 △A′B′C，A′ 落在 AB 上，∠A=angle_a，求旋转角 ∠ACA′"""
    a = math.radians(angle_a)
    C0 = (0.0, 0.0)
    A0 = (1.0, 0.0)
    # A′ 在 AB 上且 CA′=CA，则 ∠ACA′ = 180° - 2∠A
    rot = math.radians(180 - 2 * angle_a)
    A1 = (math.cos(rot), math.sin(rot))
    t = 1.7
    B0 = (1 - t * math.cos(a), t * math.sin(a))
    B1 = (B0[0] * math.cos(rot) - B0[1] * math.sin(rot),
          B0[0] * math.sin(rot) + B0[1] * math.cos(rot))
    f, _k = _fit([A0, B0, C0, A1, B1], flip=True)
    A, B, C, Ap, Bp = f(A0), f(B0), f(C0), f(A1), f(B1)
    p = [PL([A, B, C], close=True, w=2.0)]
    p.append(PL([Ap, Bp, C], close=True, w=1.5, dash="5 4", color=BLUE))
    p.append(L(C[0], C[1], *A, w=1.2, color=GRAY))
    p.append(L(C[0], C[1], *Ap, w=1.2, color=GRAY))
    s, e, mid = arc_between(C, A, Ap, 46)
    p.append(ARC(C[0], C[1], 46, s, e))
    p.append(T(*P(mid, 66, C[0], C[1]), "?", size=12, color=RED))
    sa, ea, ma = arc_between(A, B, C, 26)
    p.append(ARC(A[0], A[1], 26, sa, ea))
    p.append(T(*P(ma, 44, A[0], A[1]), "%g°" % angle_a, size=10, color=RED))
    for pt, lab, dx, dy in [(A, "A", 8, 12), (B, "B", -4, -11),
                            (C, "C", -15, 10), (Ap, "A′", 10, -6),
                            (Bp, "B′", 12, 4)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 236, p, "旋转后对应点落在边上")


def fig_rotate_grid(x, y, cx=0, cy=0, ccw=True, deg=90):
    """坐标系中点 (x,y) 绕 (cx,cy) 旋转 deg，求对应点"""
    a = math.radians(deg) * (1 if ccw else -1)
    dx, dy = x - cx, y - cy
    rx = cx + dx * math.cos(a) - dy * math.sin(a)
    ry = cy + dx * math.sin(a) + dy * math.cos(a)
    xm = max(abs(x), abs(rx), abs(cx), 1) + 2
    ym = max(abs(y), abs(ry), abs(cy), 1) + 2
    marks = [(x, y, "P(%g,%g)" % (x, y), 6, -9), (rx, ry, "P′", 6, 16)]
    if cx or cy:
        marks.append((cx, cy, "C(%g,%g)" % (cx, cy), 6, 16))
    else:
        marks.append((0, 0, "O", -12, 15))

    def ov(sx, sy):
        return [L(sx(cx), sy(cy), sx(x), sy(y), w=1.4, color=GRAY),
                L(sx(cx), sy(cy), sx(rx), sy(ry), w=1.4, color=GRAY),
                L(sx(x), sy(y), sx(rx), sy(ry), dash="4 4", color=GRAY)]

    return plot([], (-xm, xm), (-ym, ym), marks=marks, overlay=ov)


def fig_square_rotate_f(df):
    """正方形 ABCD，F 在 CD 上，把 △ADF 绕 A 旋转 90° 使 AD 与 AB 重合，F 的对应点为 F′"""
    side = 138
    A = (94, 50)
    B = (94 + side, 50)
    C = (94 + side, 50 + side)
    D = (94, 50 + side)
    k = df / 6.0
    F = (D[0] + side * k, D[1])
    Fp = (B[0], B[1] + side * k)
    p = [PL([A, B, C, D], close=True, w=2.0)]
    p.append(PL([A, D, F], close=True, w=1.6))
    p.append(PL([A, B, Fp], close=True, w=1.5, dash="5 4", color=BLUE))
    p.append(L(A[0], A[1], *F, w=1.2, color=GRAY))
    p.append(T((D[0] + F[0]) / 2, D[1] + 18, "%g" % df, size=11, color=BLUE))
    p.append(T(B[0] + 12, (B[1] + Fp[1]) / 2 + 4, "?", size=12, color=RED))
    p.append(T(Fp[0] - 16, Fp[1] - 8, "F′", size=12))
    for pt, lab, dx, dy in [(A, "A", -13, -5), (B, "B", 13, -5),
                            (C, "C", 13, 16), (D, "D", -13, 16), (F, "F", 2, 17)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    p.append(DOT(*Fp))
    return SVG(340, 240, p, "正方形中的旋转")


def fig_square_half(be=None, df=None, rotate=False):
    """正方形 ABCD，E 在 BC、F 在 CD，∠EAF=45°"""
    side = 132
    A = (96, 52)
    B = (96 + side, 52)
    C = (96 + side, 52 + side)
    D = (96, 52 + side)
    p = [PL([A, B, C, D], close=True, w=2.0)]
    eb = (be if be is not None else 2) / 6.0
    fd = (df if df is not None else 3) / 6.0
    E = (B[0], B[1] + side * eb)
    F = (D[0] + side * fd, D[1])
    p.append(L(A[0], A[1], *E, w=1.6))
    p.append(L(A[0], A[1], *F, w=1.6))
    p.append(L(E[0], E[1], *F, w=1.6, color=BLUE))
    s, e, mid = arc_between(A, E, F, 34)
    p.append(ARC(A[0], A[1], 34, s, e))
    p.append(T(*P(mid, 54, A[0], A[1]), "45°", size=10, color=RED))
    if be is not None:
        p.append(T(B[0] + 9, (B[1] + E[1]) / 2, str(be), size=11, color=BLUE))
    if df is not None:
        p.append(T((D[0] + F[0]) / 2, D[1] - 8, str(df), size=11, color=BLUE))
    for pt, lab, dx, dy in [(A, "A", -13, -6), (B, "B", 13, -6),
                            (C, "C", 13, 15), (D, "D", -13, 15),
                            (E, "E", 13, 6), (F, "F", 4, -11)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 236, p, "正方形中的半角")


def fig_equilateral_inner(p1, p2, p3):
    """等边三角形 ABC 内一点 P，PA=p1、PB=p2、PC=p3（边长由三个距离反推）"""
    def build(s):
        A = (0.0, 0.0)
        B = (s, 0.0)
        C = (s / 2.0, s * math.sqrt(3) / 2.0)
        a = (p1 ** 2 - p2 ** 2 + s * s) / (2 * s)
        h2 = p1 ** 2 - a * a
        if h2 <= 0:
            return None
        P = (a, math.sqrt(h2))
        return A, B, C, P

    lo, hi = abs(p1 - p2) + 0.05, p1 + p2 - 0.05
    for _ in range(90):
        mid = (lo + hi) / 2.0
        g = build(mid)
        if not g:
            lo = mid
            continue
        if math.hypot(g[3][0] - g[2][0], g[3][1] - g[2][1]) < p3:
            lo = mid
        else:
            hi = mid
    g = build((lo + hi) / 2.0) or build(lo) or build(hi)
    A0, B0, C0, P0 = g
    f, _k = _fit([A0, B0, C0], flip=True)
    A, B, C, Pp = f(A0), f(B0), f(C0), f(P0)
    p = [PL([A, B, C], close=True, w=2.0)]
    for pt, lab, val, dx, dy in [(A, "A", p1, 0, -11), (B, "B", p2, -14, 12),
                                 (C, "C", p3, 14, 12)]:
        p.append(L(Pp[0], Pp[1], pt[0], pt[1], w=1.5))
        p.append(T((Pp[0] + pt[0]) / 2 + dx / 2.2, (Pp[1] + pt[1]) / 2 + dy / 2.6,
                   str(val), size=11, color=BLUE))
    for pt, lab, dx, dy in [(A, "A", 0, -11), (B, "B", -14, 12),
                            (C, "C", 14, 12), (Pp, "P", 10, 12)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 236, p, "等边三角形内一点")


def fig_fence(total, wall_side=True, area=None, sep=None):
    """一面靠墙围矩形，篱笆总长 total"""
    p = []
    wall_x = 52
    top, bot = 62, 190
    if wall_side:
        p.append(L(wall_x, top - 14, wall_x, bot + 14, w=3.2))
        p.append(T(wall_x, top - 22, "墙", size=10, color=GRAY))
        # 三段篱笆：上、右、下
        x2 = 262
        p.append(L(wall_x, top, x2, top, w=2.0))
        p.append(L(x2, top, x2, bot, w=2.0))
        p.append(L(wall_x, bot, x2, bot, w=2.0))
        p.append(T((wall_x + x2) / 2, top - 7, "x", size=11, color=BLUE))
        p.append(T(x2 + 11, (top + bot) / 2, "x", size=11, color=BLUE))
        p.append(T((wall_x + x2) / 2, bot + 17, "x", size=11, color=BLUE))
    else:
        x1, x2 = 66, 274
        p.append(PL([(x1, top), (x2, top), (x2, bot), (x1, bot)], close=True, w=2.0))
        p.append(T((x1 + x2) / 2, top - 7, "x", size=11, color=BLUE))
        p.append(T((x1 + x2) / 2, bot + 17, "x", size=11, color=BLUE))
        p.append(T(x2 + 11, (top + bot) / 2, "y", size=11, color=BLUE))
        p.append(T(x1 - 11, (top + bot) / 2, "y", size=11, color=BLUE))
    if area:
        p.append(T(170, 224, "面积 %s" % area, size=10, color=GRAY))
    else:
        p.append(T(170, 224, "篱笆总长 %g m" % total, size=10, color=GRAY))
    return SVG(340, 236, p, "篱笆围矩形")


def fig_arch_bridge(a=1 / 8.0, drop=8.0):
    """抛物线拱桥 y=-x²/8，水面在拱顶下方 drop"""
    half = math.sqrt(drop / a)
    xr = (-half * 1.35, half * 1.35)
    yr = (-drop * 0.75, drop * 0.62)
    marks = [(-half, -drop, "A", -12, 14), (half, -drop, "B", 12, 14),
             (0, 0, "O", -12, -6)]

    def ov(sx, sy):
        return [L(sx(-half), sy(-drop), sx(half), sy(-drop), w=2.4, color=BLUE),
                L(sx(-half), sy(-drop), sx(-half), sy(0), dash="4 4", color=GRAY),
                L(sx(half), sy(-drop), sx(half), sy(0), dash="4 4", color=GRAY)]

    return plot([poly(lambda x: -a * x * x, -half, half)],
                xr, yr, marks=marks, overlay=ov, xlabel="x", ylabel="y")


def fig_pie(parts):
    """扇形统计图。parts: [(名称, 圆心角)]"""
    cx, cy, R = 170, 112, 82
    p = []
    start = 90.0
    palette = [BLUE, RED, "#2e8b57", "#8e6bbf"]
    for i, (name, deg) in enumerate(parts):
        end = start - deg
        x1, y1 = P(start, R, cx, cy)
        x2, y2 = P(end, R, cx, cy)
        large = 1 if deg > 180 else 0
        col = palette[i % len(palette)]
        p.append('<path d="M%.1f,%.1f L%.1f,%.1f A%d,%d 0 %d 1 %.1f,%.1f Z" '
                 'fill="%s" fill-opacity="0.14" stroke="%s" stroke-width="1.4"/>'
                 % (cx, cy, x1, y1, R, R, large, x2, y2, col, col))
        p.append(T(*P((start + end) / 2, R * 0.70, cx, cy), name, size=12))
        p.append(T(*P((start + end) / 2, R * 0.44, cx, cy), "%g°" % deg,
                   size=10, color=col))
        start = end
    p.append(CI(cx, cy, R))
    p.append(DOT(cx, cy, 2.0))
    return SVG(340, 232, p, "扇形统计图")


def fig_equal_chords(deg, label=None):
    """同圆中 ∠AOB = ∠COD = deg"""
    cx, cy, R = 170, 112, 84
    A = P(90 + deg / 2, R, cx, cy)
    B = P(90 - deg / 2, R, cx, cy)
    C = P(90 + deg / 2 + 150, R, cx, cy)
    D = P(90 - deg / 2 + 150, R, cx, cy)
    p = [CI(cx, cy, R)]
    p.append(L(*A, *B, w=2.0, color=BLUE))
    p.append(L(*C, *D, w=2.0, color=BLUE))
    p.append(L(cx, cy, *A, w=1.2))
    p.append(L(cx, cy, *B, w=1.2))
    p.append(L(cx, cy, *C, w=1.2))
    p.append(L(cx, cy, *D, w=1.2))
    s, e, m = arc_between((cx, cy), A, B, 30)
    p.append(ARC(cx, cy, 30, s, e))
    p.append(T(*P(m, 48, cx, cy), "%g°" % deg, size=10, color=RED))
    s, e, m = arc_between((cx, cy), C, D, 30)
    p.append(ARC(cx, cy, 30, s, e))
    p.append(T(*P(m, 48, cx, cy), "%g°" % deg, size=10, color=RED))
    if label:
        p.append(T((A[0] + B[0]) / 2, (A[1] + B[1]) / 2 - 6, label, size=11, color=BLUE))
    for pt, lab, dx, dy in [(A, "A", 0, -11), (B, "B", 0, 17),
                            (C, "C", -6, -11), (D, "D", -6, 17),
                            ((cx, cy), "O", -13, 15)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "同圆中的等圆心角")


def fig_two_hyperbolas(k1=8, k2=2):
    """A 在 y=k1/x、B 在 y=k2/x，AB∥y 轴，求 △OAB"""
    x = 2.2
    y1, y2 = k1 / x, k2 / x
    yr = (-0.6, y1 + 1.2)
    marks = [(x, y1, "A", 8, -6), (x, y2, "B", 8, 15)]

    def ov(sx, sy):
        return [L(sx(x), sy(y2), sx(x), sy(y1), w=2.0, color=BLUE),
                L(sx(0), sy(0), sx(x), sy(y1), w=1.3, color=GRAY),
                L(sx(0), sy(0), sx(x), sy(y2), w=1.3, color=GRAY)]

    return plot([poly(lambda t: k1 / t, 0.55, 5.2), poly(lambda t: k2 / t, 0.42, 5.2)],
                (-0.8, 5.4), yr, marks=marks, overlay=ov, ylabel="y")


# ======================= 题目 -> 图 =======================


def fig_grid_blocks(rows):
    """俯视图：rows 为二维数字列表（每格小正方体个数）"""
    n, m = len(rows), len(rows[0])
    cell = 66
    x0 = (340 - m * cell) / 2
    y0 = (232 - n * cell) / 2
    p = []
    for i in range(n):
        for j in range(m):
            x = x0 + j * cell
            y = y0 + i * cell
            p.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" fill="none"/>'
                     % (x, y, cell, cell))
            p.append(T(x + cell / 2, y + cell / 2 + 7, str(rows[i][j]),
                       size=17, color=BLUE))
    p.append(T(340 - 10, 20, "俯视图", anchor="end", size=10, color=GRAY))
    return SVG(340, 232, p, "俯视图方格")


def fig_cuboid(a, b, h, note=None):
    """长方体：主视图 长 a 高 h，左视图 宽 b 高 h"""
    ox, oy = 96, 150
    dx, dy = 58, -34
    p = [PL([(ox, oy), (ox + a * 9, oy), (ox + a * 9, oy - h * 9), (ox, oy - h * 9)],
            close=True, w=1.8)]
    p.append(PL([(ox, oy - h * 9), (ox + dx, oy - h * 9 + dy),
                 (ox + a * 9 + dx, oy - h * 9 + dy), (ox + a * 9, oy - h * 9)],
                w=1.6))
    p.append(L(ox + a * 9, oy, ox + a * 9 + dx, oy + dy, w=1.6))
    p.append(L(ox + a * 9 + dx, oy + dy, ox + a * 9 + dx, oy - h * 9 + dy, w=1.6))
    p.append(L(ox, oy, ox + dx, oy + dy, w=1.6, dash="4 4", color=GRAY))
    p.append(T(ox + a * 4.5, oy + 18, "%g" % a, size=11, color=BLUE))
    p.append(T(ox - 9, oy - h * 4.5, "%g" % h, anchor="end", size=11, color=BLUE))
    p.append(T(ox + a * 9 + dx + 9, oy - h * 4.5 + dy, "%g" % b, size=11, color=BLUE))
    if note:
        p.append(T(170, 222, note, size=10, color=GRAY))
    return SVG(340, 232, p, "长方体")


def fig_regular_polygon(n, apothem_label=None, side_label=None, diag=False):
    """正 n 边形及其外接圆"""
    cx, cy, R = 170, 112, 84
    pts = [P(90 + 360.0 * i / n, R, cx, cy) for i in range(n)]
    p = [CI(cx, cy, R, dash="4 4"), PL(pts, close=True, w=2.0)]
    p.append(L(cx, cy, *pts[0], w=1.2, color=GRAY))
    p.append(L(cx, cy, *pts[1], w=1.2, color=GRAY))
    mid = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
    p.append(L(cx, cy, *mid, w=1.2, color=GRAY, dash="4 4"))
    p.append(RA(mid[0], mid[1], (cx - mid[0]) / 90.0, (cy - mid[1]) / 90.0, 7))
    if apothem_label:
        p.append(T((cx + mid[0]) / 2 + 7, (cy + mid[1]) / 2, apothem_label,
                   size=11, color=BLUE))
    if side_label:
        p.append(T(mid[0] + 12, mid[1] - 8, side_label, size=11, color=BLUE))
    p.append(DOT(cx, cy))
    p.append(T(cx - 13, cy + 16, "O"))
    for i, pt in enumerate(pts):
        p.append(DOT(*pt, 2.0))
        ang = 90 + 360.0 * i / n
        lx, ly = P(ang, R + 15, cx, cy)
        p.append(T(lx, ly + 4, chr(65 + i), size=12))
    return SVG(340, 232, p, "正多边形")


def fig_equal_arcs():
    """⊙O 中劣弧 AB = 劣弧 AC，∠ABC 已知"""
    cx, cy, R = 170, 116, 84
    A = P(90, R, cx, cy)
    B = P(210, R, cx, cy)
    C = P(330, R, cx, cy)
    p = [CI(cx, cy, R), PL([A, B, C], close=True, w=2.0)]
    for v, p1, p2, lab in [("B", A, C, "70°")]:
        s, e, m = arc_between(B, A, C, 26)
        p.append(ARC(B[0], B[1], 26, s, e))
        p.append(T(*P(m, 48, B[0], B[1]), lab, size=10, color=RED))
    for pt, lab, dx, dy in [(A, "A", 0, -11), (B, "B", -14, 6),
                            (C, "C", 14, 6), ((cx, cy), "O", -13, 15)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "同圆中的等弧")


def fig_six_points():
    """圆周六等分，求弦 AB"""
    cx, cy, R = 170, 112, 84
    pts = [P(90 + 60 * i, R, cx, cy) for i in range(6)]
    p = [CI(cx, cy, R)]
    for i, pt in enumerate(pts):
        p.append(DOT(*pt))
        p.append(T(pt[0] + (13 if pt[0] > cx else -13), pt[1] + 4,
                   chr(65 + i), size=12))
        p.append(L(cx, cy, *pt, w=1.0, color=GRAY))
    p.append(L(*pts[0], *pts[1], w=2.2, color=BLUE))
    p.append(T((pts[0][0] + pts[1][0]) / 2 + 12, (pts[0][1] + pts[1][1]) / 2,
               "?", size=12, color=RED))
    p.append(DOT(cx, cy, 2.0))
    p.append(T(cx - 13, cy + 16, "O"))
    return SVG(340, 232, p, "圆周六等分")


def fig_similar_de():
    """△ABC 中 D 在 AB、E 在 AC，DE∥BC"""
    A = (170, 48)
    B = (62, 190)
    C = (288, 190)
    D = (A[0] + (B[0] - A[0]) * 0.45, A[1] + (B[1] - A[1]) * 0.45)
    E = (A[0] + (C[0] - A[0]) * 0.45, A[1] + (C[1] - A[1]) * 0.45)
    p = [PL([A, B, C], close=True, w=2.0)]
    p.append(L(D[0], D[1], E[0], E[1], w=1.8, color=BLUE))
    for pt, lab, dx, dy in [(A, "A", 0, -11), (B, "B", -13, 10),
                            (C, "C", 13, 10), (D, "D", -14, 4), (E, "E", 14, 4)]:
        p.append(DOT(*pt))
        p.append(T(pt[0] + dx, pt[1] + dy, lab))
    return SVG(340, 232, p, "平行线截三角形")


def fig_circle_point(r, d, label=None):
    """⊙O 半径 r，点 P 到 O 的距离 d"""
    cx, cy, R = 170, 112, 84
    k = R / float(r)
    Px = (cx + d * k, cy)
    p = [CI(cx, cy, R), L(cx, cy, *Px, w=1.6, color=BLUE)]
    p.append(T((cx + Px[0]) / 2, cy - 7, "%g" % d, size=11, color=BLUE))
    p.append(T(cx - 24, cy - 38, "r=%g" % r, size=11, color=GRAY))
    p.append(DOT(cx, cy))
    p.append(T(cx - 13, cy + 16, "O"))
    p.append(DOT(*Px))
    p.append(T(Px[0] + 8, cy - 8, "P", size=12))
    if label:
        p.append(T(170, 224, label, size=10, color=GRAY))
    return SVG(340, 232, p, "点与圆的位置关系")


def _solid_cylinder(cx, cy, w=44, h=54):
    rx, ry = w / 2.0, 9
    top, bot = cy - h / 2.0, cy + h / 2.0
    p = [L(cx - rx, top, cx - rx, bot, w=1.6), L(cx + rx, top, cx + rx, bot, w=1.6)]
    p.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/>' % (cx, top, rx, ry))
    p.append('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 0 %.1f,%.1f" fill="none"/>'
             % (cx - rx, bot, rx, ry, cx + rx, bot))
    p.append('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f" fill="none" '
             'stroke-dasharray="4 3"/>' % (cx - rx, bot, rx, ry, cx + rx, bot))
    return p


def _solid_cone(cx, cy, w=46, h=58):
    rx, ry = w / 2.0, 9
    apex = cy - h / 2.0
    bot = cy + h / 2.0
    p = [L(cx, apex, cx - rx, bot, w=1.6), L(cx, apex, cx + rx, bot, w=1.6)]
    p.append('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 0 %.1f,%.1f" fill="none"/>'
             % (cx - rx, bot, rx, ry, cx + rx, bot))
    p.append('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f" fill="none" '
             'stroke-dasharray="4 3"/>' % (cx - rx, bot, rx, ry, cx + rx, bot))
    return p


def _solid_cube(cx, cy, s=40):
    x0, y0 = cx - s / 2.0, cy - s / 2.0 + 6
    d = 13
    p = [PL([(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)], close=True, w=1.6)]
    p.append(PL([(x0, y0), (x0 + d, y0 - d), (x0 + s + d, y0 - d), (x0 + s, y0)], w=1.4))
    p.append(L(x0 + s, y0 + s, x0 + s + d, y0 + s - d, w=1.4))
    p.append(L(x0 + s + d, y0 - d, x0 + s + d, y0 + s - d, w=1.4))
    p.append(L(x0, y0 + s, x0 + d, y0 + s - d, w=1.4, dash="4 3", color=GRAY))
    return p


def _solid_sphere(cx, cy, r=28):
    return ['<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r),
            '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="7" stroke-dasharray="4 3"/>'
            % (cx, cy, r)]


def fig_solids():
    """四种几何体并排，选「三视图都是正方形」"""
    y = 108
    p = []
    for lab, cx, parts in [("A", 62, _solid_cylinder(62, y)),
                           ("B", 140, _solid_cone(140, y)),
                           ("C", 210, _solid_sphere(210, y)),
                           ("D", 282, _solid_cube(282, y))]:
        p.extend(parts)
        p.append(T(cx, 196, lab, size=12, bold=True))
    return SVG(340, 232, p, "四种几何体")


def fig_three_views(kind="cylinder"):
    """立体图 + 三视图（主、左、俯）"""
    p = []
    if kind == "cylinder":
        p.extend(_solid_cylinder(74, 104, 48, 62))
        p.append(T(74, 190, "圆柱", size=10, color=GRAY))
        p.append(PL([(150, 66), (206, 66), (206, 142), (150, 142)], close=True, w=1.6))
        p.append(T(178, 160, "主视图", size=10, color=GRAY))
        p.append(PL([(226, 66), (282, 66), (282, 142), (226, 142)], close=True, w=1.6))
        p.append(T(254, 160, "左视图", size=10, color=GRAY))
        p.append(CI(178, 198, 22))
        p.append(T(178, 234, "俯视图", size=10, color=GRAY))
    else:
        p.extend(_solid_cone(74, 104, 50, 66))
        p.append(T(74, 190, "圆锥", size=10, color=GRAY))
        p.append(PL([(150, 64), (206, 64), (178, 142)], close=True, w=1.6))
        p.append(T(178, 160, "主视图", size=10, color=GRAY))
        p.append(PL([(226, 64), (282, 64), (254, 142)], close=True, w=1.6))
        p.append(T(254, 160, "左视图", size=10, color=GRAY))
        p.append(CI(178, 200, 22))
        p.append(CI(178, 200, 4))
        p.append(T(178, 234, "俯视图", size=10, color=GRAY))
    return SVG(340, 242, p, "三视图")


def fig_projection(kind="parallel"):
    """平行投影 / 中心投影"""
    ground = 176
    p = [L(30, ground, 320, ground, w=1.6)]
    p.append(PL([(96, ground), (150, ground), (150, ground - 54), (96, ground - 54)],
                close=True, w=1.8))
    if kind == "parallel":
        for x in (110, 150, 190):
            p.append(L(x, 34, x + 46, ground, w=1.2, color=BLUE))
        p.append(T(150, 24, "光线互相平行", size=10, color=GRAY))
    else:
        S = (150, 30)
        for x in (96, 150, 204):
            p.append(L(S[0], S[1], x + 22, ground, w=1.2, color=BLUE))
        p.append(DOT(*S, 3))
        p.append(T(S[0], S[1] - 8, "点光源", size=10, color=GRAY))
    return SVG(340, 216, p, "投影")


def fig_parabola_family(items=(("A", 2), ("B", 1), ("C", -0.5), ("D", -3))):
    """同一个坐标系里的四条抛物线，比较开口大小（按选项系数画，端点标 A/B/C/D）"""
    ymax = 3.2
    curves, ends = [], []
    for lab, a in items:
        xm = min(2.2, math.sqrt(ymax / abs(a)))
        curves.append(poly(lambda x, a=a: a * x * x, -xm, xm))
        ends.append((lab, xm, a * xm * xm, a))

    def ov(sx, sy):
        return [T(sx(ex) + 9, sy(ey) + 15, lab, size=12, color=RED)
                for (lab, ex, ey, a) in ends]

    return plot(curves, (-2.4, 2.4), (-ymax, ymax), w=340, h=232, overlay=ov)


def fig_similar_aa():
    """两个三角形，两组角分别相等"""
    A = (58, 44)
    B = (26, 150)
    C = (150, 150)
    A2 = (250, 62)
    B2 = (206, 168)
    C2 = (300, 168)
    p = [PL([A, B, C], close=True, w=1.8), PL([A2, B2, C2], close=True, w=1.8)]
    for V, P1, P2, lab in [(A, B, C, "∠A"), (B, A, C, "∠B")]:
        s, e, m = arc_between(V, P1, P2, 22)
        p.append(ARC(V[0], V[1], 22, s, e))
        p.append(T(*P(m, 40, V[0], V[1]), lab, size=9, color=RED))
    for V, P1, P2, lab in [(A2, B2, C2, "∠D"), (B2, A2, C2, "∠E")]:
        s, e, m = arc_between(V, P1, P2, 22)
        p.append(ARC(V[0], V[1], 22, s, e))
        p.append(T(*P(m, 40, V[0], V[1]), lab, size=9, color=RED))
    for pt, lab, dx, dy in [(A, "A", 0, -10), (B, "B", -13, 8), (C, "C", 13, 8),
                            (A2, "D", 0, -10), (B2, "E", -13, 8), (C2, "F", 13, 8)]:
        p.append(DOT(*pt, 2.2))
        p.append(T(pt[0] + dx, pt[1] + dy, lab, size=12))
    p.append(T(170, 214, "∠A=∠D，∠B=∠E", size=10, color=GRAY))
    return SVG(340, 226, p, "两角分别相等的两个三角形")


# ======================= 题目 -> 图 =======================

def build():
    F = {}

    # --- 圆周角定理 ---
    F["cnm_253_q1"] = fig_central_inscribed(100, "major")
    F["cnm_253_q2"] = fig_central_inscribed(70, "major", "35°", central_label="?")
    F["cnm_253_q3"] = fig_central_inscribed(64, "major", "32°", central_label="?")
    F["cnm_253_q5"] = fig_central_inscribed(100, "minor")

    # --- 直径所对的圆周角 ---
    F["cnm_254_q1"] = fig_diameter(45)
    F["cnm_254_q2"] = fig_diameter(35)
    F["cnm_254_q3"] = fig_diameter(53.1, ac="6", ab="10", show_angle=False)
    F["cnm_254_q5"] = fig_diameter(30, bc="3")

    # --- 圆内接四边形 ---
    F["cnm_255_q1"] = fig_cyclic(arcs=[("A", "B", "D", "70°"), ("C", "B", "D", "?")])
    F["cnm_255_q2"] = fig_cyclic(arcs=[("B", "A", "C", "95°"), ("D", "A", "C", "?")])
    F["cnm_255_q3"] = fig_cyclic(extend=True,
                                 arcs=[("C", "D", "E", "80°"), ("A", "B", "D", "?")])
    F["cnm_255_q4"] = fig_cyclic(arcs=[("A", "B", "D", "3k"), ("B", "A", "C", "4k"),
                                       ("C", "B", "D", "6k")])
    F["cnm_255_q5"] = fig_cyclic(arcs=[("C", "B", "D", "?")], bod=140)

    # --- 弧长 / 扇形 ---
    F["cnm_256_q1"] = fig_sector(6, 60)
    F["cnm_256_q2"] = fig_sector(9, 120)
    F["cnm_256_q3"] = fig_sector(6, 120, arc_label="4π", angle_label="?")
    F["cnm_256_q5"] = fig_sector(2, 90, arc_label="π")
    F["cnm_257_q1"] = fig_sector(6, 60)
    F["cnm_257_q2"] = fig_sector(3, 120)
    F["cnm_257_q3"] = fig_sector(6, 120, arc_label="12π", angle_label="?")
    F["cnm_257_q4"] = fig_sector(5, 90, arc_label="4π")
    F["cnm_257_q5"] = fig_square_arc(4)

    # --- 圆锥 ---
    F["cnm_258_q1"] = fig_cone(3, l=5)
    F["cnm_258_q3"] = fig_cone(3, l=5)
    F["cnm_258_q4"] = fig_cone(5, h=12)
    F["cnm_258_q5"] = fig_sector(6, 120, arc_label="展开图")

    # --- 坡度 ---
    F["cnm_280_q1"] = fig_slope(1, 2, ratio_note="坡度 1∶2，水平 10 m")
    F["cnm_280_q2"] = fig_slope(6, 8, ratio_note="铅直 6 m，水平 8 m")
    F["cnm_280_q3"] = fig_slope(3, 4, hyp="50 m", ratio_note="坡度 3∶4")
    F["cnm_280_q4"] = fig_slope(1, 1.732, angle_label="?", ratio_note="坡度 1∶√3")
    F["cnm_280_q5"] = fig_dam(6, 4, 1.5, 2, note="坝高 4 m，求坝底 BC")

    # --- 切线 ---
    F["cnm_262_q1"] = fig_tangent(3)
    F["cnm_262_q2"] = fig_tangent(3, pa="4")
    F["cnm_262_q3"] = fig_tangent(3, angle_aop=65)
    F["cnm_262_q5"] = fig_tangent(6, angle_p=30)

    # --- 切线长 ---
    F["cnm_263_q1"] = fig_two_tangents(3, 60, pa="6")
    F["cnm_263_q2"] = fig_two_tangents(3, 70)
    F["cnm_263_q3"] = fig_two_tangents(3, 60, pa="6")
    F["cnm_263_q4"] = fig_two_tangents(3, 50)
    F["cnm_263_q5"] = fig_two_tangents(3, 74)

    # --- 直线与圆 ---
    F["cnm_260_q1"] = fig_line_circle(5, 5)
    F["cnm_260_q2"] = fig_line_circle(5, 3)
    F["cnm_260_q3"] = fig_line_circle(5, 6, r_label="r=?")
    F["cnm_260_q4"] = fig_circle_axes(3, 4, 4)

    # --- 二次函数 ---
    F["cnm_230_q1"] = fig_parabola(-2, 0, 0, marks=[(0, 0, "O", -12, 16)], note="y = −2x²")
    F["cnm_234_q1"] = fig_parabola(1, -2, -3, xticks=[-1, 1, 3],
                                   marks=[(-1, 0, "A", -10, 16), (3, 0, "B", 10, 16)],
                                   note="y = x²−2x−3")
    F["cnm_234_q2"] = fig_parabola(1, 2, 5, note="y = x²+2x+5")
    F["cnm_234_q3"] = fig_parabola(1, -4, -5, xticks=[-1, 2, 5],
                                   marks=[(-1, 0, "A", -10, 16), (5, 0, "B", 10, 16)],
                                   note="y = x²−4x−5")
    F["cnm_231_q1"] = fig_parabola(1, -2, 3, xticks=[1],
                                   marks=[(1, 2, "顶点", 8, -8)], note="y = (x−1)²+2")
    F["cnm_231_q3"] = fig_parabola(1, 4, 1, xticks=[-2],
                                   marks=[(-2, -3, "顶点", 8, 16)], note="y = (x+2)²−3")

    # --- 反比例 ---
    F["cnm_238_q1"] = fig_hyperbola(-6, note="y = −6/x")
    F["cnm_238_q2"] = fig_hyperbola(-6, marks=[(2, -3, "P(2,m)", 8, 14)], note="y = −6/x")
    F["cnm_238_q3"] = fig_hyperbola(6, marks=[(1, 6, "A", 8, -6), (2, 3, "B", 8, -6),
                                              (-3, -2, "C", -10, 14)], note="y = 6/x")

    # --- 关于原点对称 ---
    F["cnm_249_q1"] = fig_reflect(3, -2)
    F["cnm_249_q2"] = fig_reflect(-4, -7)

    # --- 旋转 ---
    F["cnm_244_q1"] = fig_rotate_point(90, "OA")
    F["cnm_244_q3"] = fig_rotate_point(90, "5")

    # --- 相似 ---
    F["cnm_272_q2"] = fig_similar(3, 5, note="相似比 3∶5，小三角形周长 12")
    F["cnm_272_q3"] = fig_similar(2, 3, note="相似比 2∶3，S△ABC=24")

    # ============ 第二批：题干说了「图」却缺图，以及成组的几何题 ============

    # --- 题干明确引用图，原来没有图（缺陷修复） ---
    F["cnm_273_q1"] = fig_similar_de()
    F["cnm_313_q3"] = fig_pie([("步行", 90), ("骑车", 150), ("乘车", 120)])

    # --- 垂径定理 ---
    F["cnm_251_q1"] = fig_perpendicular_chord(5, 8)
    F["cnm_251_q2"] = fig_perpendicular_chord(10, 16, mask="chord")
    F["cnm_251_q3"] = fig_perpendicular_chord(13, 24, mask="radius")
    F["cnm_251_q5"] = fig_parallel_chords(5, 6, 8)

    # --- 内切圆 / 外接圆 ---
    F["cnm_264_q1"] = fig_incircle(4, 3, 5)
    F["cnm_264_q3"] = fig_incircle(12, 5, 13)
    F["cnm_264_q5"] = fig_incircle(8, 9, 7)
    F["cnm_265_q1"] = fig_circumcircle("right")
    F["cnm_265_q2"] = fig_circumcircle("right")
    F["cnm_265_q3"] = fig_circumcircle("right")
    F["cnm_265_q4"] = fig_circumcircle("obtuse")

    # --- 仰角 / 俯角 ---
    F["cnm_279_q2"] = fig_elevation(45, 40)
    F["cnm_279_q3"] = fig_elevation(45, 30, eye=1.6)
    F["cnm_279_q4"] = fig_depression(24, 0.75)

    # --- 斜列车位 ---
    F["cnm_290_q1"] = fig_parking(60, line_len=5)
    F["cnm_290_q2"] = fig_parking(30, line_len=6)
    F["cnm_290_q3"] = fig_parking(30, sep=2.5, ask="sep")

    # --- 反比例函数里的面积 ---
    F["cnm_239_q1"] = fig_hyperbola_triangle(6)
    F["cnm_239_q2"] = fig_hyperbola_triangle(-8, kind="rect")
    F["cnm_239_q3"] = fig_hyperbola_triangle(-8)
    F["cnm_239_q4"] = fig_two_hyperbolas(8, 2)
    F["cnm_241_q3"] = fig_line_hyperbola(6, -1)

    # --- 旋转 ---
    F["cnm_244_q4"] = fig_rotate_on_side(70)
    F["cnm_245_q4"] = fig_rotate_on_side(65)
    F["cnm_246_q3"] = fig_rotate_grid(-3, 4, ccw=False)
    F["cnm_246_q4"] = fig_rotate_grid(4, 3, cx=1, cy=1, ccw=True)

    # --- 正方形半角 / 等边三角形内点 ---
    F["cnm_247_q2"] = fig_square_rotate_f(3)
    F["cnm_247_q3"] = fig_square_half(2, 3)
    F["cnm_247_q4"] = fig_equilateral_inner(3, 4, 5)

    # --- 篱笆 / 拱桥 ---
    F["cnm_228_q3"] = fig_fence(20)
    F["cnm_236_q3"] = fig_fence(30)
    F["cnm_267_q3"] = fig_fence(24)
    F["cnm_236_q5"] = fig_arch_bridge()

    # --- 三视图 ---
    F["cnm_283_q3"] = fig_grid_blocks([[2, 1], [1, 3]])
    F["cnm_283_q5"] = fig_cuboid(5, 2, 3)

    # --- 正多边形 ---
    F["cnm_266_q1"] = fig_regular_polygon(6, side_label="2")
    F["cnm_266_q3"] = fig_regular_polygon(3, apothem_label="?")

    # --- 同圆中的等圆心角 / 等分圆周 ---
    F["cnm_252_q2"] = fig_equal_chords(50, "6")
    F["cnm_252_q3"] = fig_six_points()
    F["cnm_252_q5"] = fig_equal_arcs()

    # --- 选择题里需要图的（提高选择题区的图形覆盖） ---
    F["cnm_259_q1"] = fig_circle_point(5, 4)
    F["cnm_254_q4"] = fig_diameter(None, show_angle=False)
    F["cnm_264_q2"] = fig_incircle(8, 9, 7)
    F["cnm_265_q1"] = fig_circumcircle("right")
    F["cnm_271_q1"] = fig_similar_aa()
    F["cnm_283_q1"] = fig_three_views("cylinder")
    F["cnm_283_q2"] = fig_solids()
    F["cnm_283_q4"] = fig_three_views("cone")
    F["cnm_281_q1"] = fig_projection("parallel")
    F["cnm_281_q2"] = fig_projection("parallel")
    F["cnm_230_q3"] = fig_parabola_family()

    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/obj-figs.json")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    figs = build()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(figs, f, ensure_ascii=False, indent=1)
    print("客观题题图: %d 张 -> %s" % (len(figs), args.out))

    if args.preview:
        src = open("data/bundle.js", encoding="utf-8").read()
        i = src.index("window.CN_DATA=")
        d = json.loads(src[i + len("window.CN_DATA="):].rstrip().rstrip(";"))
        qs = {q["id"]: q for q in d["questions"]}
        cells = []
        for qid, svg in figs.items():
            q = qs.get(qid, {})
            cells.append('<figure><div class="b">%s</div><figcaption><b>%s</b><br>%s</figcaption></figure>'
                         % (svg, qid, q.get("prompt", "")[:52]))
        html = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<title>客观题题图预览</title><style>'
                'body{font:13px/1.55 system-ui,-apple-system,"PingFang SC",sans-serif;'
                'background:#f4f3f0;margin:0;padding:20px;color:#2b2b2b}'
                'h1{font-size:17px;margin:0 0 14px}'
                '.g{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}'
                'figure{margin:0;background:#fff;border:1px solid #e3e0da;border-radius:9px;'
                'padding:9px;display:flex;flex-direction:column}'
                '.b{height:180px;display:flex;align-items:center;justify-content:center}'
                '.b svg{max-width:100%%;max-height:172px}'
                'figcaption{font-size:11px;color:#666;border-top:1px solid #eee;padding-top:6px}'
                '</style></head><body><h1>客观题题图 · %d 张</h1><div class="g">%s</div>'
                '</body></html>' % (len(figs), "".join(cells)))
        with open("obj-figs-preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("预览: obj-figs-preview.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
