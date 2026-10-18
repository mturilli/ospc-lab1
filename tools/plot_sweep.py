"""Plots the elapsed time of the stats step against the number of workers, one line per laptop.

Usage, inside the container, from the repository folder:
    python3 tools/plot_sweep.py
Reads members/*/sweep.csv and writes results/sweep.svg (median of the runs).
Uses only the Python standard library.
"""

import csv
import glob
import math
import os
import statistics

WIDTH = 720
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
WORKERS = [1, 2, 4, 8, 16]


def marker(shape, x, y, color):
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if shape == 0:
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" {ring}/>'
    if shape == 1:
        return f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{color}" {ring}/>'
    if shape == 2:
        return f'<path d="M{x:.1f},{y - 6:.1f} L{x + 6:.1f},{y + 5:.1f} L{x - 6:.1f},{y + 5:.1f} Z" fill="{color}" {ring}/>'
    if shape == 3:
        return f'<path d="M{x:.1f},{y - 6:.1f} L{x + 6:.1f},{y:.1f} L{x:.1f},{y + 6:.1f} L{x - 6:.1f},{y:.1f} Z" fill="{color}" {ring}/>'
    if shape == 4:
        return f'<path d="M{x:.1f},{y + 6:.1f} L{x + 6:.1f},{y - 5:.1f} L{x - 6:.1f},{y - 5:.1f} Z" fill="{color}" {ring}/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{SURFACE}" stroke="{color}" stroke-width="2.5"/>'


def text(x, y, s, size=13, color=INK_2, anchor="start", weight="normal"):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def load():
    laptops = []
    for path in sorted(glob.glob(os.path.join("members", "*", "sweep.csv"))):
        user = path.split(os.sep)[1]
        runs = {}
        with open(path) as f:
            for row in csv.DictReader(f):
                runs.setdefault(int(row["workers"]), []).append(float(row["elapsed_s"]))
        cpus = "?"
        info = os.path.join(os.path.dirname(path), "machine.txt")
        if os.path.exists(info):
            for line in open(info):
                if line.startswith("cpus_in_container:"):
                    cpus = line.split(":")[1].strip()
        laptops.append((user, cpus, {w: statistics.median(t) for w, t in runs.items()}))
    return laptops[: len(COLORS)]


def main():
    laptops = load()
    if not laptops:
        raise SystemExit("No members/*/sweep.csv yet: run tools/sweep.sh first.")

    direct = len(laptops) <= 4
    rows = math.ceil(len(laptops) / 3)
    left, right, bottom = 64, (120 if direct else 30), 56
    top = 76 + 22 * rows
    pw, ph = WIDTH - left - right, 300
    height = top + ph + bottom

    peak = max(t for _, _, m in laptops for t in m.values())
    step = next(s for s in [1, 2, 5, 10, 20, 50, 100, 200, 500] if peak / s <= 6)
    ymax = step * math.ceil(peak / step)

    def px(w):
        return left + pw * math.log2(w) / 4

    def py(t):
        return top + ph * (1 - t / ymax)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
           f'<rect width="{WIDTH}" height="{height}" fill="{SURFACE}"/>',
           text(left, 30, "Elapsed time of the stats step", 17, INK, weight="bold"),
           text(left, 50, "Median of the runs on each laptop. Lower is faster.", 13)]

    # Legend above the plot, three entries per row
    for i, (user, cpus, _) in enumerate(laptops):
        x, y = left + 210 * (i % 3), 74 + 22 * (i // 3)
        out.append(marker(i, x + 6, y - 4, COLORS[i]))
        out.append(text(x + 18, y, f"{user} ({cpus} CPUs)", 12, INK))

    for k in range(int(ymax / step) + 1):
        y = py(k * step)
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + pw}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(left - 10, y + 4, f"{k * step:g}", 12, anchor="end"))
    out.append(text(left - 10, top - 14, "Seconds", 12, anchor="end"))
    for w in WORKERS:
        out.append(text(px(w), top + ph + 22, str(w), 12, anchor="middle"))
    out.append(text(left + pw / 2, top + ph + 46, "Workers", 13, anchor="middle"))

    ends = []
    for i, (user, _, median) in enumerate(laptops):
        points = [(px(w), py(median[w])) for w in WORKERS if w in median]
        path = " ".join(f"{'M' if j == 0 else 'L'}{x:.1f},{y:.1f}" for j, (x, y) in enumerate(points))
        out.append(f'<path d="{path}" fill="none" stroke="{COLORS[i]}" stroke-width="2" stroke-linejoin="round"/>')
        out += [marker(i, x, y, COLORS[i]) for x, y in points]
        ends.append([points[-1][1], user])

    # Direct labels at the end of each line, moved apart when they would overlap
    if direct:
        ends.sort()
        for j in range(1, len(ends)):
            ends[j][0] = max(ends[j][0], ends[j - 1][0] + 15)
        for y, user in ends:
            out.append(text(left + pw + 12, y + 4, user, 12, INK_2))
    out.append("</svg>")

    os.makedirs("results", exist_ok=True)
    with open(os.path.join("results", "sweep.svg"), "w") as f:
        f.write("\n".join(out))
    print("Saved results/sweep.svg")


if __name__ == "__main__":
    main()
