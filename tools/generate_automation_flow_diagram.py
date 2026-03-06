"""Generate automation flow diagram assets for README.

Primary renderer: Graphviz (python package + `dot` executable).
Fallback renderer: Pillow + lightweight SVG writer when Graphviz is unavailable.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    x: int
    y: int
    kind: str  # start, process, decision, optional, end


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str = ""
    optional: bool = False


NODE_STYLES: Dict[str, Dict[str, str]] = {
    "start": {"fill": "#1d4ed8", "stroke": "#1e3a8a", "text": "#ffffff"},
    "process": {"fill": "#0f766e", "stroke": "#134e4a", "text": "#ecfeff"},
    "decision": {"fill": "#b45309", "stroke": "#78350f", "text": "#fff7ed"},
    "optional": {"fill": "#7e22ce", "stroke": "#581c87", "text": "#faf5ff"},
    "end": {"fill": "#166534", "stroke": "#14532d", "text": "#f0fdf4"},
}

BOX_WIDTH = 360
BOX_HEIGHT = 96
ROUNDED = 20
CANVAS_WIDTH = 1700
CANVAS_HEIGHT = 1600

NODES: List[Node] = [
    Node("start", "Scheduler /\nManual Trigger", 160, 60, "start"),
    Node("load", "Load mission data\n+ launch browser", 160, 220, "process"),
    Node("auth", "Auth state\navailable?", 160, 380, "decision"),
    Node("manual", "Notify manual login\nrequired", 860, 380, "optional"),
    Node("mission", "Mission\nphase", 160, 540, "process"),
    Node("shop_decision", "Shopping execution\nenabled?", 160, 700, "decision"),
    Node("shop_exec", "Shopping execution\n(before draw)", 860, 700, "optional"),
    Node("draw_decision", "Draw enabled?", 160, 860, "decision"),
    Node("draw", "Draw phase", 860, 860, "optional"),
    Node("gather_decision", "Shopping gather\nenabled?", 160, 1020, "decision"),
    Node("gather", "Shopping gather\n(after draw)", 860, 1020, "optional"),
    Node("hunt", "Reschedule\nhunt tasks", 860, 1180, "optional"),
    Node("post", "Save run state, notify,\nand save storage", 160, 1260, "process"),
    Node("end", "Run complete", 160, 1420, "end"),
]

EDGES: List[Edge] = [
    Edge("start", "load"),
    Edge("load", "auth"),
    Edge("auth", "mission", label="Yes"),
    Edge("auth", "manual", label="No", optional=True),
    Edge("manual", "end", optional=True),
    Edge("mission", "shop_decision"),
    Edge("shop_decision", "shop_exec", label="Yes", optional=True),
    Edge("shop_decision", "draw_decision", label="No"),
    Edge("shop_exec", "draw_decision", optional=True),
    Edge("draw_decision", "draw", label="Yes", optional=True),
    Edge("draw_decision", "gather_decision", label="No"),
    Edge("draw", "gather_decision", optional=True),
    Edge("gather_decision", "gather", label="Yes", optional=True),
    Edge("gather_decision", "post", label="No"),
    Edge("gather", "hunt", optional=True),
    Edge("hunt", "post", optional=True),
    Edge("post", "end"),
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("segoeui.ttf", "arial.ttf", "calibri.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _node_geometry(node: Node) -> tuple[int, int, int, int]:
    return node.x, node.y, node.x + BOX_WIDTH, node.y + BOX_HEIGHT


def _center(node: Node) -> tuple[float, float]:
    return node.x + BOX_WIDTH / 2, node.y + BOX_HEIGHT / 2


def _connection_points(source: Node, target: Node) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy = _center(source)
    tx, ty = _center(target)

    if tx > sx + BOX_WIDTH / 2:
        start = (source.x + BOX_WIDTH, sy)
        end = (target.x, ty)
    elif tx < sx - BOX_WIDTH / 2:
        start = (source.x, sy)
        end = (target.x + BOX_WIDTH, ty)
    elif ty > sy:
        start = (sx, source.y + BOX_HEIGHT)
        end = (tx, target.y)
    else:
        start = (sx, source.y)
        end = (tx, target.y + BOX_HEIGHT)

    return start, end


def _elbow_points(start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
    sx, sy = start
    ex, ey = end
    if abs(sx - ex) < 2 or abs(sy - ey) < 2:
        return [start, end]
    mid_x = (sx + ex) / 2
    return [start, (mid_x, sy), (mid_x, ey), end]


def _draw_arrowhead(draw: ImageDraw.ImageDraw, point_from: tuple[float, float], point_to: tuple[float, float], color: str) -> None:
    x1, y1 = point_from
    x2, y2 = point_to
    size = 12

    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 >= x1:
            p1 = (x2, y2)
            p2 = (x2 - size, y2 - 5)
            p3 = (x2 - size, y2 + 5)
        else:
            p1 = (x2, y2)
            p2 = (x2 + size, y2 - 5)
            p3 = (x2 + size, y2 + 5)
    else:
        if y2 >= y1:
            p1 = (x2, y2)
            p2 = (x2 - 5, y2 - size)
            p3 = (x2 + 5, y2 - size)
        else:
            p1 = (x2, y2)
            p2 = (x2 - 5, y2 + size)
            p3 = (x2 + 5, y2 + size)

    draw.polygon([p1, p2, p3], fill=color)


def _draw_dashed_axis(
    draw: ImageDraw.ImageDraw,
    *,
    fixed: float,
    start: float,
    end: float,
    horizontal: bool,
    color: str,
    width: int,
    dash: int,
    gap: int,
) -> None:
    segment_start, segment_end = sorted((start, end))
    step = dash + gap
    cursor = segment_start
    while cursor < segment_end:
        dash_end = min(cursor + dash, segment_end)
        if horizontal:
            draw.line([(cursor, fixed), (dash_end, fixed)], fill=color, width=width)
        else:
            draw.line([(fixed, cursor), (fixed, dash_end)], fill=color, width=width)
        cursor += step


def _draw_dashed_line(draw: ImageDraw.ImageDraw, points: Iterable[tuple[float, float]], color: str, width: int = 3) -> None:
    points_list = list(points)
    dash = 10
    gap = 8

    for i in range(len(points_list) - 1):
        x1, y1 = points_list[i]
        x2, y2 = points_list[i + 1]

        if abs(x2 - x1) < 2:
            _draw_dashed_axis(
                draw,
                fixed=x1,
                start=y1,
                end=y2,
                horizontal=False,
                color=color,
                width=width,
                dash=dash,
                gap=gap,
            )
        elif abs(y2 - y1) < 2:
            _draw_dashed_axis(
                draw,
                fixed=y1,
                start=x1,
                end=x2,
                horizontal=True,
                color=color,
                width=width,
                dash=dash,
                gap=gap,
            )
        else:
            draw.line([(x1, y1), (x2, y2)], fill=color, width=width)


def _draw_wrapped_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fill: str) -> None:
    font = _font(21)
    lines = text.split("\n")
    x1, y1, x2, y2 = box
    line_heights = []
    line_widths = []
    for line in lines:
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        line_widths.append(right - left)
        line_heights.append(bottom - top)

    total_h = sum(line_heights) + max(0, len(lines) - 1) * 6
    cur_y = y1 + (BOX_HEIGHT - total_h) / 2

    for line, lw, lh in zip(lines, line_widths, line_heights):
        draw.text((x1 + (BOX_WIDTH - lw) / 2, cur_y), line, fill=fill, font=font)
        cur_y += lh + 6


def _render_with_graphviz(output_dir: Path) -> tuple[bool, str]:
    try:
        import graphviz
    except ImportError:
        return False, "python package `graphviz` is not installed"

    try:
        subprocess.run(
            ["dot", "-V"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False, "Graphviz executable `dot` is not on PATH"

    dot = graphviz.Digraph("ZZZBotAutomationFlow")
    dot.attr(rankdir="LR", bgcolor="transparent", splines="spline", nodesep="0.55", ranksep="0.9", pad="0.3")
    dot.attr("node", shape="box", style="rounded,filled", penwidth="2", fontname="Segoe UI", fontsize="11")
    dot.attr("edge", color="#334155", penwidth="2", arrowsize="0.8", fontname="Segoe UI", fontsize="10")

    for node in NODES:
        style = NODE_STYLES[node.kind]
        dot.node(node.node_id, node.label, fillcolor=style["fill"], color=style["stroke"], fontcolor=style["text"])

    for edge in EDGES:
        attrs = {"style": "dashed", "color": "#7c3aed"} if edge.optional else {}
        if edge.label:
            attrs["label"] = edge.label
        dot.edge(edge.source, edge.target, **attrs)

    base_name = output_dir / "automation-flow"
    try:
        dot.format = "svg"
        dot.render(filename=str(base_name), cleanup=True)
        dot.format = "png"
        dot.render(filename=str(base_name), cleanup=True)
    except graphviz.ExecutableNotFound as exc:
        return False, f"Graphviz executable missing: {exc}"

    return True, "rendered with Graphviz"


def _render_png_fallback(output_png: Path) -> None:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#f8fafc")
    draw = ImageDraw.Draw(image)

    by_id = {node.node_id: node for node in NODES}

    for node in NODES:
        style = NODE_STYLES[node.kind]
        box = _node_geometry(node)
        draw.rounded_rectangle(box, radius=ROUNDED, fill=style["fill"], outline=style["stroke"], width=4)
        _draw_wrapped_text(draw, box, node.label, style["text"])

    label_font = _font(18)
    for edge in EDGES:
        source = by_id[edge.source]
        target = by_id[edge.target]
        start, end = _connection_points(source, target)
        points = _elbow_points(start, end)
        color = "#7c3aed" if edge.optional else "#334155"

        if edge.optional:
            _draw_dashed_line(draw, points, color, width=3)
        else:
            draw.line(points, fill=color, width=4)

        _draw_arrowhead(draw, points[-2], points[-1], color)

        if edge.label:
            lx, ly = points[0]
            _, _, tw, th = draw.textbbox((0, 0), edge.label, font=label_font)
            draw.rounded_rectangle((lx + 8, ly - 28, lx + tw + 18, ly - 3), radius=6, fill="#ffffff", outline="#cbd5e1", width=1)
            draw.text((lx + 13, ly - 25), edge.label, fill="#0f172a", font=label_font)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png, format="PNG", optimize=True)


def _render_svg_fallback(output_svg: Path) -> None:
    by_id = {node.node_id: node for node in NODES}
    svg: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">',
        '<defs>',
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />',
        '</marker>',
        '<marker id="arrowOptional" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#7c3aed" />',
        '</marker>',
        '</defs>',
        '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc"/>',
    ]

    for node in NODES:
        style = NODE_STYLES[node.kind]
        svg.append(
            f'<rect x="{node.x}" y="{node.y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="{ROUNDED}" ry="{ROUNDED}" fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="4"/>'
        )
        lines = node.label.split("\n")
        line_y = node.y + BOX_HEIGHT / 2 - (len(lines) - 1) * 15
        for line in lines:
            svg.append(
                f'<text x="{node.x + BOX_WIDTH / 2}" y="{line_y}" text-anchor="middle" dominant-baseline="middle" fill="{style["text"]}" font-family="Segoe UI, Arial, sans-serif" font-size="22">{line}</text>'
            )
            line_y += 30

    for edge in EDGES:
        source = by_id[edge.source]
        target = by_id[edge.target]
        start, end = _connection_points(source, target)
        points = _elbow_points(start, end)
        color = "#7c3aed" if edge.optional else "#334155"
        marker = "arrowOptional" if edge.optional else "arrow"
        dash = ' stroke-dasharray="10,8"' if edge.optional else ""
        point_str = " ".join(f"{x},{y}" for x, y in points)
        svg.append(
            f'<polyline points="{point_str}" fill="none" stroke="{color}" stroke-width="3"{dash} marker-end="url(#{marker})"/>'
        )
        if edge.label:
            lx, ly = points[0]
            svg.append(
                f'<rect x="{lx + 8}" y="{ly - 30}" width="44" height="26" rx="6" ry="6" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>'
            )
            svg.append(
                f'<text x="{lx + 30}" y="{ly - 13}" text-anchor="middle" dominant-baseline="middle" fill="#0f172a" font-family="Segoe UI, Arial, sans-serif" font-size="16">{edge.label}</text>'
            )

    svg.append("</svg>")

    output_svg.parent.mkdir(parents=True, exist_ok=True)
    output_svg.write_text("\n".join(svg), encoding="utf-8")


def generate(output_dir: Path) -> tuple[Path, Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_svg = output_dir / "automation-flow.svg"
    output_png = output_dir / "automation-flow.png"

    success, reason = _render_with_graphviz(output_dir)
    if success:
        return output_svg, output_png, reason

    _render_png_fallback(output_png)
    _render_svg_fallback(output_svg)
    return output_svg, output_png, f"fallback renderer used ({reason})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate README automation flow diagram assets.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/assets"),
        help="Directory where diagram assets are written (default: docs/assets)",
    )
    args = parser.parse_args()

    output_svg, output_png, mode = generate(args.output_dir)
    print(f"Diagram generation mode: {mode}")
    print(f"Wrote: {output_svg}")
    print(f"Wrote: {output_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
