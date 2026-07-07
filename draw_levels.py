#!/usr/bin/env python3
"""
Interactive tool to draw click-zone outlines on pyramid.png.

Controls:
  Left click     Add a point to the current level
  Right click    Remove the last point
  1-6            Switch level
  Enter / C      Close the current polygon (needs at least 3 points)
  R              Reset points for the current level
  S              Save coordinates to level_coords.json and print HTML snippet
  Q / Escape     Quit

Run:
  python3 draw_levels.py
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    print("Pillow is required but not installed for this Python.")
    print(f"  Python: {sys.executable}")
    if Path("venv").exists():
        print("\nYou have a venv folder. Install into it with:")
        print("  ./venv/bin/pip install -r requirements.txt")
        print("  ./venv/bin/python draw_levels.py")
    else:
        print("\nInstall with:")
        print("  pip install pillow")
        print("  python3 draw_levels.py")
    sys.exit(1)

IMAGE_PATH = Path(__file__).with_name("pyramid.png")
OUTPUT_PATH = Path(__file__).with_name("level_coords.json")

LEVEL_COLORS = {
    1: "#e8913a",
    2: "#e8c43a",
    3: "#5cb85c",
    4: "#3aafa9",
    5: "#4a7fd4",
    6: "#8b5cf6",
}

LEVEL_NAMES = {
    1: "I — Clear Vision (orange, bottom)",
    2: "II — Charged Teachers (yellow)",
    3: "III — Day-to-day Care (green)",
    4: "IV — Cooperation with Parents (teal)",
    5: "V — Academic Training (blue)",
    6: "VI — Bridge to Society (purple, top)",
}


class LevelDrawer:
    def __init__(self) -> None:
        if not IMAGE_PATH.exists():
            raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

        self.original = Image.open(IMAGE_PATH).convert("RGBA")
        self.img_w, self.img_h = self.original.size

        self.levels: dict[int, list[tuple[int, int]]] = {i: [] for i in range(1, 7)}
        self.closed: dict[int, bool] = {i: False for i in range(1, 7)}
        self.current_level = 1
        self.scale = 1.0
        self.hover_point: tuple[int, int] | None = None

        self._load_saved_coords()

        self.root = tk.Tk()
        self.root.title("Pyramid Level Outliner")
        self.root.configure(bg="#1e1e1e")

        self._build_ui()
        self._bind_events()
        self._redraw()

    def _load_saved_coords(self) -> None:
        if not OUTPUT_PATH.exists():
            return
        try:
            data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        for key, value in data.get("levels", {}).items():
            level = int(key)
            points = [tuple(p) for p in value.get("points", [])]
            if points:
                self.levels[level] = points
                self.closed[level] = bool(value.get("closed", len(points) >= 3))

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, bg="#1e1e1e")
        top.pack(fill="x", padx=10, pady=8)

        self.status_var = tk.StringVar()
        tk.Label(
            top,
            textvariable=self.status_var,
            fg="#f2f2f2",
            bg="#1e1e1e",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        self.help_var = tk.StringVar()
        tk.Label(
            top,
            textvariable=self.help_var,
            fg="#b8b8b8",
            bg="#1e1e1e",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(4, 0))

        canvas_frame = tk.Frame(self.root, bg="#1e1e1e")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        max_w = min(1200, self.root.winfo_screenwidth() - 80)
        max_h = min(800, self.root.winfo_screenheight() - 180)
        self.scale = min(max_w / self.img_w, max_h / self.img_h, 1.0)
        disp_w = int(self.img_w * self.scale)
        disp_h = int(self.img_h * self.scale)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=disp_w,
            height=disp_h,
            bg="#2a2a2a",
            highlightthickness=1,
            highlightbackground="#444",
            cursor="crosshair",
        )
        self.canvas.pack()

        bottom = tk.Frame(self.root, bg="#1e1e1e")
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        for level in range(1, 7):
            tk.Button(
                bottom,
                text=str(level),
                width=3,
                command=lambda lv=level: self._set_level(lv),
            ).pack(side="left", padx=2)

        tk.Button(bottom, text="Close polygon", command=self._close_polygon).pack(side="left", padx=8)
        tk.Button(bottom, text="Reset level", command=self._reset_level).pack(side="left", padx=2)
        tk.Button(bottom, text="Save", command=self._save).pack(side="left", padx=8)
        tk.Button(bottom, text="Quit", command=self.root.destroy).pack(side="right")

        self.output = tk.Text(
            self.root,
            height=8,
            bg="#111",
            fg="#d8ffd8",
            insertbackground="#d8ffd8",
            font=("Consolas", 10),
        )
        self.output.pack(fill="x", padx=10, pady=(0, 10))

        self._update_status()

    def _bind_events(self) -> None:
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        self.root.bind("1", lambda _e: self._set_level(1))
        self.root.bind("2", lambda _e: self._set_level(2))
        self.root.bind("3", lambda _e: self._set_level(3))
        self.root.bind("4", lambda _e: self._set_level(4))
        self.root.bind("5", lambda _e: self._set_level(5))
        self.root.bind("6", lambda _e: self._set_level(6))
        self.root.bind("<Return>", lambda _e: self._close_polygon())
        self.root.bind("c", lambda _e: self._close_polygon())
        self.root.bind("C", lambda _e: self._close_polygon())
        self.root.bind("r", lambda _e: self._reset_level())
        self.root.bind("R", lambda _e: self._reset_level())
        self.root.bind("s", lambda _e: self._save())
        self.root.bind("S", lambda _e: self._save())
        self.root.bind("q", lambda _e: self.root.destroy())
        self.root.bind("<Escape>", lambda _e: self.root.destroy())

    def _image_to_canvas(self, x: int, y: int) -> tuple[float, float]:
        return x * self.scale, y * self.scale

    def _canvas_to_image(self, x: float, y: float) -> tuple[int, int]:
        ix = int(round(x / self.scale))
        iy = int(round(y / self.scale))
        ix = max(0, min(self.img_w - 1, ix))
        iy = max(0, min(self.img_h - 1, iy))
        return ix, iy

    def _set_level(self, level: int) -> None:
        self.current_level = level
        self.hover_point = None
        self._update_status()
        self._redraw()

    def _current_points(self) -> list[tuple[int, int]]:
        return self.levels[self.current_level]

    def _on_left_click(self, event: tk.Event) -> None:
        if self.closed[self.current_level] and self._current_points():
            self.closed[self.current_level] = False
            self.levels[self.current_level] = []

        point = self._canvas_to_image(event.x, event.y)
        self.levels[self.current_level].append(point)
        self._update_status()
        self._redraw()

    def _on_right_click(self, event: tk.Event) -> None:
        points = self._current_points()
        if points:
            points.pop()
            self.closed[self.current_level] = False
            self._update_status()
            self._redraw()

    def _on_motion(self, event: tk.Event) -> None:
        self.hover_point = self._canvas_to_image(event.x, event.y)
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self.hover_point = None
        self._redraw()

    def _close_polygon(self) -> None:
        points = self._current_points()
        if len(points) < 3:
            self.status_var.set("Need at least 3 points before closing the polygon.")
            return
        self.closed[self.current_level] = True
        self._update_status()
        self._redraw()
        self._refresh_output()

    def _reset_level(self) -> None:
        self.levels[self.current_level] = []
        self.closed[self.current_level] = False
        self._update_status()
        self._redraw()
        self._refresh_output()

    def _update_status(self) -> None:
        lv = self.current_level
        count = len(self._current_points())
        state = "closed" if self.closed[lv] else "open"
        self.status_var.set(
            f"Level {lv}: {LEVEL_NAMES[lv]}  |  points: {count}  |  {state}"
        )
        self.help_var.set(
            "Left click = add point   Right click = undo last point   "
            "1-6 = switch level   Enter/C = close polygon   R = reset   S = save"
        )

    def _compose_image(self) -> Image.Image:
        base = self.original.copy()
        draw = ImageDraw.Draw(base, "RGBA")

        for level in range(1, 7):
            points = self.levels[level]
            if len(points) < 2:
                continue

            color = LEVEL_COLORS[level]
            fill = color + "55" if self.closed[level] else color + "33"
            outline = color

            if self.closed[level] and len(points) >= 3:
                draw.polygon(points, fill=fill, outline=outline, width=3)
            else:
                draw.line(points, fill=outline, width=3)

            for x, y in points:
                r = 6
                draw.ellipse((x - r, y - r, x + r, y + r), fill=outline, outline="white", width=2)

        lv = self.current_level
        points = self.levels[lv]
        if points and not self.closed[lv] and self.hover_point is not None:
            draw.line([points[-1], self.hover_point], fill=LEVEL_COLORS[lv], width=2)

        return base

    def _redraw(self) -> None:
        composed = self._compose_image()
        disp_w = int(self.img_w * self.scale)
        disp_h = int(self.img_h * self.scale)
        resized = composed.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

        for level in range(1, 7):
            points = self.levels[level]
            if not points:
                continue
            color = LEVEL_COLORS[level]
            canvas_points: list[float] = []
            for x, y in points:
                cx, cy = self._image_to_canvas(x, y)
                canvas_points.extend([cx, cy])

            if len(canvas_points) >= 4:
                if self.closed[level] and len(points) >= 3:
                    self.canvas.create_polygon(
                        *canvas_points,
                        outline=color,
                        fill="",
                        width=2,
                        dash=() if level == self.current_level else (4, 4),
                    )
                else:
                    self.canvas.create_line(
                        *canvas_points,
                        fill=color,
                        width=2,
                        dash=() if level == self.current_level else (4, 4),
                    )

            for x, y in points:
                cx, cy = self._image_to_canvas(x, y)
                r = 4
                self.canvas.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    fill=color,
                    outline="white",
                    width=1,
                )

        if (
            self.hover_point is not None
            and self._current_points()
            and not self.closed[self.current_level]
        ):
            x1, y1 = self._image_to_canvas(*self._current_points()[-1])
            x2, y2 = self._image_to_canvas(*self.hover_point)
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=LEVEL_COLORS[self.current_level],
                width=1,
                dash=(3, 3),
            )

    def _points_to_attr(self, points: list[tuple[int, int]]) -> str:
        return " ".join(f"{x},{y}" for x, y in points)

    def _refresh_output(self) -> None:
        lines = ["<!-- Paste into index.html -->", ""]
        for level in range(6, 0, -1):
            points = self.levels[level]
            if not points:
                continue
            lines.append(
                f'<polygon class="level-hit" data-level="{level}" '
                f'points="{self._points_to_attr(points)}" />'
            )

        self.output.delete("1.0", "end")
        self.output.insert("1.0", "\n".join(lines))

    def _save(self) -> None:
        payload = {
            "image": {
                "width": self.img_w,
                "height": self.img_h,
            },
            "levels": {
                str(level): {
                    "name": LEVEL_NAMES[level],
                    "points": self.levels[level],
                    "closed": self.closed[level],
                }
                for level in range(1, 7)
            },
        }
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._refresh_output()
        closed_count = sum(1 for lv in range(1, 7) if self.closed[lv] and self.levels[lv])
        self.status_var.set(
            f"Saved {OUTPUT_PATH.name} ({closed_count}/6 levels closed). "
            "HTML snippet updated below."
        )

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = LevelDrawer()
    app.run()


if __name__ == "__main__":
    main()
