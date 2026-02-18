#!/usr/bin/env python3
"""
Image Resizer — Modern UI with Dark / Light mode
CustomTkinter + drag & drop + image previews
"""

import os
import re
import threading
from pathlib import Path
from tkinter import filedialog

from PIL import Image
import customtkinter as ctk

# ── Drag & drop ──────────────────────────────────────────────────────────────
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

ctk.set_default_color_theme("blue")

SUPPORTED  = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
THUMB_PX   = 96
GRID_COLS  = 5

# ── Colour palettes ───────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "mode":           "dark",
        "root_bg":        "#1a1a2e",
        "header_bg":      "#1e1e30",
        "header_title":   "#e0e0ff",
        "header_sub":     "#7070a0",
        "drop_bg":        "#272740",
        "drop_border":    "#404065",
        "ph_arrow":       "#4a4a7a",
        "ph_title":       "#6a6aaa",
        "ph_or":          "#505075",
        "ph_formats":     "#4a4a70",
        "settings_bg":    "#272740",
        "settings_sub":   "#7070a0",
        "folder_text":    "#8888cc",
        "count_text":     "#6666aa",
        "progress_text":  "#8888cc",
        "log_bg":         "#1a1a2a",
        "log_text":       "#aaaadd",
        "card_bg":        "#32324a",
        "card_text":      "#9999cc",
        "btn_browse_fg":  "#8a4500",
        "btn_browse_hv":  "#c46000",
        "btn_more_fg":    "#6a3300",
        "btn_more_hv":    "#8a4500",
        "btn_resize_fg":  "#c46000",
        "btn_resize_hv":  "#e07a00",
        "btn_clear_fg":   "#2a1010",
        "btn_clear_hv":   "#552020",
        "btn_remove_hv":  "#7a1f1f",
        "btn_remove_txt": "#665577",
        "toggle_icon":    "☀️",
    },
    "light": {
        "mode":           "light",
        "root_bg":        "#f0f0f8",
        "header_bg":      "#e0e0f0",
        "header_title":   "#22225a",
        "header_sub":     "#7070a0",
        "drop_bg":        "#e8e8f4",
        "drop_border":    "#b0b0cc",
        "ph_arrow":       "#aaaacc",
        "ph_title":       "#7070aa",
        "ph_or":          "#9090b0",
        "ph_formats":     "#9090b0",
        "settings_bg":    "#e8e8f4",
        "settings_sub":   "#7070a0",
        "folder_text":    "#5555aa",
        "count_text":     "#7777bb",
        "progress_text":  "#5555aa",
        "log_bg":         "#dcdcf0",
        "log_text":       "#333366",
        "card_bg":        "#d8d8ee",
        "card_text":      "#555588",
        "btn_browse_fg":  "#c46000",
        "btn_browse_hv":  "#e07a00",
        "btn_more_fg":    "#a05200",
        "btn_more_hv":    "#c46000",
        "btn_resize_fg":  "#c46000",
        "btn_resize_hv":  "#e07a00",
        "btn_clear_fg":   "#cc4444",
        "btn_clear_hv":   "#aa2222",
        "btn_remove_hv":  "#cc3333",
        "btn_remove_txt": "#aa5555",
        "toggle_icon":    "🌙",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail card
# ─────────────────────────────────────────────────────────────────────────────
class ThumbnailCard(ctk.CTkFrame):
    """Image preview card — re-themed via apply_theme()."""

    def __init__(self, parent, image_path: str, on_remove, theme: dict, **kw):
        super().__init__(parent, fg_color=theme["card_bg"],
                         corner_radius=10, width=THUMB_PX + 16, **kw)
        self.image_path = image_path
        self.grid_propagate(False)

        try:
            pil = Image.open(image_path)
            pil.thumbnail((THUMB_PX, THUMB_PX), Image.Resampling.LANCZOS)
            self._ctk_img = ctk.CTkImage(pil, size=(pil.width, pil.height))
            ctk.CTkLabel(self, image=self._ctk_img, text="").pack(padx=8, pady=(8, 2))
        except Exception:
            ctk.CTkLabel(self, text="?", font=("Arial", 28),
                         text_color=theme["card_text"]).pack(padx=8, pady=(8, 2))

        name  = Path(image_path).name
        short = name if len(name) <= 13 else name[:10] + "…"
        self.name_lbl = ctk.CTkLabel(
            self, text=short, font=ctk.CTkFont(size=10),
            text_color=theme["card_text"], wraplength=THUMB_PX)
        self.name_lbl.pack(padx=4)

        self.remove_btn = ctk.CTkButton(
            self, text="✕", width=24, height=20,
            font=ctk.CTkFont(size=10), fg_color="transparent",
            hover_color=theme["btn_remove_hv"],
            text_color=theme["btn_remove_txt"],
            command=lambda: on_remove(image_path))
        self.remove_btn.pack(pady=(2, 6))

    def apply_theme(self, t: dict):
        self.configure(fg_color=t["card_bg"])
        self.name_lbl.configure(text_color=t["card_text"])
        self.remove_btn.configure(hover_color=t["btn_remove_hv"],
                                  text_color=t["btn_remove_txt"])


# ─────────────────────────────────────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────────────────────────────────────
class ImageResizerApp:

    def __init__(self):
        self._theme_name = "dark"

        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()

        self.root.title("Image Resizer")
        self.root.geometry("860x700")
        self.root.minsize(640, 520)

        self.file_paths:  list           = []
        self.thumb_cards: dict           = {}
        self.size_var = ctk.StringVar(value="1024")

        self._build_ui()
        self.apply_theme()      # paint initial dark theme

    # ─────────────────────────────────────────────────────────────────────
    # Theme
    # ─────────────────────────────────────────────────────────────────────
    @property
    def theme(self) -> dict:
        return THEMES[self._theme_name]

    def toggle_theme(self):
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        ctk.set_appearance_mode(self.theme["mode"])
        self.apply_theme()

    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["root_bg"])

        self.hdr.configure(fg_color=t["header_bg"])
        self.hdr_title.configure(text_color=t["header_title"])
        self.hdr_sub.configure(text_color=t["header_sub"])
        self.theme_btn.configure(text=t["toggle_icon"])

        self.drop_frame.configure(fg_color=t["drop_bg"], border_color=t["drop_border"])
        self.ph_arrow.configure(text_color=t["ph_arrow"])
        self.ph_title.configure(text_color=t["ph_title"])
        self.ph_or.configure(text_color=t["ph_or"])
        self.ph_formats.configure(text_color=t["ph_formats"])
        self.btn_browse.configure(fg_color=t["btn_browse_fg"], hover_color=t["btn_browse_hv"])
        self.btn_more.configure(fg_color=t["btn_more_fg"], hover_color=t["btn_more_hv"])

        self.settings_row.configure(fg_color=t["settings_bg"])
        self.lbl_px.configure(text_color=t["settings_sub"])
        self.folder_label.configure(text_color=t["folder_text"])

        self.resize_btn.configure(fg_color=t["btn_resize_fg"], hover_color=t["btn_resize_hv"])
        self.count_label.configure(text_color=t["count_text"])
        self.progress_label.configure(text_color=t["progress_text"])
        self.btn_clear.configure(fg_color=t["btn_clear_fg"], hover_color=t["btn_clear_hv"])

        self.log_box.configure(fg_color=t["log_bg"], text_color=t["log_text"])

        for card in self.thumb_cards.values():
            card.apply_theme(t)

    # ─────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self.body = ctk.CTkFrame(self.root, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=16, pady=(12, 8))
        self._build_drop_zone(self.body)
        self._build_settings(self.body)
        self._build_action(self.body)
        self._build_log(self.body)

    def _build_header(self):
        self.hdr = ctk.CTkFrame(self.root, corner_radius=0, height=58)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)

        self.hdr_title = ctk.CTkLabel(
            self.hdr, text="🖼  Image Resizer",
            font=ctk.CTkFont(size=20, weight="bold"))
        self.hdr_title.pack(side="left", padx=22, pady=14)

        self.hdr_sub = ctk.CTkLabel(
            self.hdr, text="Batch resize · aspect-ratio preserved",
            font=ctk.CTkFont(size=12))
        self.hdr_sub.pack(side="left", pady=14)

        self.theme_btn = ctk.CTkButton(
            self.hdr, text="☀️", width=42, height=32,
            font=ctk.CTkFont(size=18),
            fg_color="transparent", hover_color="#44445a",
            command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=16, pady=12)

    def _build_drop_zone(self, parent):
        self.drop_frame = ctk.CTkFrame(parent, corner_radius=14, border_width=2)
        self.drop_frame.pack(fill="both", expand=True)

        self.placeholder = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.ph_arrow = ctk.CTkLabel(
            self.placeholder, text="⬆", font=ctk.CTkFont(size=52))
        self.ph_arrow.pack()

        self.ph_title = ctk.CTkLabel(
            self.placeholder, text="Drop images here",
            font=ctk.CTkFont(size=17, weight="bold"))
        self.ph_title.pack()

        self.ph_or = ctk.CTkLabel(
            self.placeholder, text="or", font=ctk.CTkFont(size=12))
        self.ph_or.pack(pady=2)

        self.btn_browse = ctk.CTkButton(
            self.placeholder, text="Browse Files",
            font=ctk.CTkFont(size=13), command=self.browse_files,
            width=150, height=38, corner_radius=20)
        self.btn_browse.pack(pady=4)

        self.ph_formats = ctk.CTkLabel(
            self.placeholder, text="JPG · PNG · BMP · GIF · TIFF · WebP",
            font=ctk.CTkFont(size=10))
        self.ph_formats.pack(pady=(6, 0))

        self.thumb_scroll = ctk.CTkScrollableFrame(
            self.drop_frame, fg_color="transparent")

        self.btn_more = ctk.CTkButton(
            self.drop_frame, text="+ Add more",
            font=ctk.CTkFont(size=12),
            width=110, height=28, corner_radius=14,
            command=self.browse_files)

        self.drop_frame.bind("<Button-1>", lambda _: self.browse_files())
        if DND_AVAILABLE:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)

    def _build_settings(self, parent):
        self.settings_row = ctk.CTkFrame(parent, corner_radius=12)
        self.settings_row.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(self.settings_row, text="Target size:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(16, 8), pady=12)

        ctk.CTkSegmentedButton(
            self.settings_row, values=["512", "768", "1024"],
            variable=self.size_var, width=210,
            font=ctk.CTkFont(size=13)
        ).pack(side="left", pady=12)

        self.lbl_px = ctk.CTkLabel(
            self.settings_row, text="px · longest side",
            font=ctk.CTkFont(size=11))
        self.lbl_px.pack(side="left", padx=(6, 20), pady=12)

        ctk.CTkFrame(self.settings_row, fg_color="transparent",
                     width=1).pack(side="left", expand=True)

        ctk.CTkLabel(self.settings_row, text="Output:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        self.folder_label = ctk.CTkLabel(
            self.settings_row,
            text="Resized_<size>  next to source images",
            font=ctk.CTkFont(size=11), wraplength=220, anchor="w")
        self.folder_label.pack(side="left", padx=(0, 16), pady=12)

    def _build_action(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))

        self.resize_btn = ctk.CTkButton(
            row, text="Resize Images",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_resize,
            height=44, width=180, corner_radius=22)
        self.resize_btn.pack(side="left")

        self.count_label = ctk.CTkLabel(
            row, text="No images selected", font=ctk.CTkFont(size=12))
        self.count_label.pack(side="left", padx=14)

        self.progress_label = ctk.CTkLabel(
            row, text="", font=ctk.CTkFont(size=12))
        self.progress_label.pack(side="right", padx=(6, 0))

        self.progress = ctk.CTkProgressBar(row, width=200, height=10, corner_radius=6)
        self.progress.set(0)
        self.progress.pack(side="right")

        self.btn_clear = ctk.CTkButton(
            row, text="Clear all", command=self.clear_all,
            width=90, height=32, font=ctk.CTkFont(size=12), corner_radius=16)
        self.btn_clear.pack(side="right", padx=(0, 16))

    def _build_log(self, parent):
        self.log_box = ctk.CTkTextbox(
            parent, height=130,
            font=ctk.CTkFont(family="Courier", size=12),
            corner_radius=10, state="disabled")
        self.log_box.pack(fill="x", pady=(10, 0))

    # ─────────────────────────────────────────────────────────────────────
    # File management
    # ─────────────────────────────────────────────────────────────────────
    def browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                       ("All files", "*.*")])
        if paths:
            self.add_files(list(paths))

    def _on_drop(self, event):
        paths = []
        for match in re.finditer(r'\{([^}]+)\}|(\S+)', event.data):
            p = match.group(1) or match.group(2)
            if p:
                paths.append(p)
        valid = [p for p in paths if Path(p).suffix.lower() in SUPPORTED]
        if valid:
            self.add_files(valid)

    def add_files(self, paths: list):
        new = [p for p in paths if p not in self.file_paths]
        if not new:
            return
        self.file_paths.extend(new)
        for p in new:
            card = ThumbnailCard(
                self.thumb_scroll, p,
                on_remove=self.remove_file,
                theme=self.theme)
            self.thumb_cards[p] = card
        self._refresh_grid()
        self._update_state()

    def _refresh_grid(self):
        for idx, (_, card) in enumerate(self.thumb_cards.items()):
            r, c = divmod(idx, GRID_COLS)
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nw")

    def remove_file(self, path: str):
        self.file_paths = [p for p in self.file_paths if p != path]
        if path in self.thumb_cards:
            self.thumb_cards.pop(path).destroy()
        self._refresh_grid()
        self._update_state()

    def clear_all(self):
        for card in self.thumb_cards.values():
            card.destroy()
        self.thumb_cards.clear()
        self.file_paths.clear()
        self.progress.set(0)
        self.progress_label.configure(text="")
        self._update_state()

    def _update_state(self):
        count = len(self.file_paths)
        if count == 0:
            self.thumb_scroll.pack_forget()
            self.btn_more.pack_forget()
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.count_label.configure(text="No images selected")
        else:
            self.placeholder.place_forget()
            self.thumb_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 4))
            self.btn_more.pack(side="right", padx=12, pady=6)
            noun = "image" if count == 1 else "images"
            self.count_label.configure(text=f"{count} {noun} selected")

    # ─────────────────────────────────────────────────────────────────────
    # Resize
    # ─────────────────────────────────────────────────────────────────────
    def start_resize(self):
        if not self.file_paths:
            self._append_log("⚠  No images selected.")
            return
        size    = int(self.size_var.get())
        out_dir = os.path.join(os.path.dirname(self.file_paths[0]), f"Resized_{size}")
        os.makedirs(out_dir, exist_ok=True)
        self.folder_label.configure(text=out_dir)
        self.resize_btn.configure(state="disabled", text="Processing…")
        self.progress.set(0)
        threading.Thread(target=self._process, args=(out_dir,), daemon=True).start()

    def _process(self, out_dir: str):
        paths   = list(self.file_paths)
        size    = int(self.size_var.get())
        total   = len(paths)
        success = 0

        self._log(f"\n▶  Resizing {total} image(s)  →  {size}px longest side")
        self._log(f"   Output: {out_dir}\n")

        for i, path in enumerate(paths, 1):
            fname = os.path.basename(path)
            try:
                img    = Image.open(path)
                w, h   = img.size
                scale  = size / max(w, h)
                nw, nh = int(w * scale), int(h * scale)
                resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
                name, ext = os.path.splitext(fname)
                out_path  = os.path.join(out_dir, f"{name}_resized{ext}")
                try:
                    resized.save(out_path, quality=95, optimize=True)
                except Exception:
                    out_path = os.path.join(out_dir, f"{name}_resized.png")
                    resized.save(out_path, "PNG")
                success += 1
                self._log(f"   ✓  {fname}  ({w}×{h}  →  {nw}×{nh})")
            except Exception as exc:
                self._log(f"   ✗  {fname}  ERROR: {exc}")

            pct = i / total
            self.root.after(0, lambda p=pct: self.progress.set(p))
            self.root.after(0, lambda i=i: self.progress_label.configure(text=f"{i}/{total}"))

        self._log(f"\n✅  Done — {success}/{total} resized successfully.")
        self.root.after(0, lambda: self.resize_btn.configure(
            state="normal", text="Resize Images"))
        self.root.after(0, lambda: self.progress_label.configure(text=""))
        self.root.after(1500, lambda: self.progress.set(0))
        self.root.after(1500, lambda: self.folder_label.configure(
            text="Resized_<size>  next to source images"))

    def _log(self, msg: str):
        self.root.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ImageResizerApp().run()
