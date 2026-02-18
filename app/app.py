#!/usr/bin/env python3
"""
Image Resizer — Modern Dark UI
CustomTkinter + drag & drop + image previews
"""

import os
import re
import threading
from pathlib import Path
from tkinter import filedialog

from PIL import Image
import customtkinter as ctk

# ── Drag & drop ─────────────────────────────────────────────────────────────
# CTk widgets work with any Tk root — we use TkinterDnD.Tk() directly so the
# tkdnd extension is loaded correctly from the start. No combined class needed.
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# ── Theme ───────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
THUMB_PX   = 96          # thumbnail size in pixels
GRID_COLS  = 5           # thumbnails per row


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail card
# ─────────────────────────────────────────────────────────────────────────────
class ThumbnailCard(ctk.CTkFrame):
    """A small card showing an image preview + filename + remove button."""

    def __init__(self, parent, image_path: str, on_remove, **kw):
        super().__init__(parent, fg_color="#32324a", corner_radius=10,
                         width=THUMB_PX + 16, **kw)
        self.image_path = image_path
        self.grid_propagate(False)

        # ── Thumbnail image ──────────────────────────────────────────────
        try:
            pil = Image.open(image_path)
            pil.thumbnail((THUMB_PX, THUMB_PX), Image.Resampling.LANCZOS)
            self._ctk_img = ctk.CTkImage(pil, size=(pil.width, pil.height))
            ctk.CTkLabel(self, image=self._ctk_img, text="").pack(
                padx=8, pady=(8, 2))
        except Exception:
            ctk.CTkLabel(self, text="?", font=("Arial", 28),
                         text_color="#555577").pack(padx=8, pady=(8, 2))

        # ── Filename (truncated) ─────────────────────────────────────────
        name = Path(image_path).name
        short = name if len(name) <= 13 else name[:10] + "…"
        ctk.CTkLabel(self, text=short,
                     font=ctk.CTkFont(size=10), text_color="#9999cc",
                     wraplength=THUMB_PX).pack(padx=4)

        # ── Remove button ────────────────────────────────────────────────
        ctk.CTkButton(
            self, text="✕", width=24, height=20,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color="#7a1f1f", text_color="#665577",
            command=lambda: on_remove(image_path)
        ).pack(pady=(2, 6))


# ─────────────────────────────────────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────────────────────────────────────
class ImageResizerApp:

    def __init__(self):
        # ── Root window ──────────────────────────────────────────────────
        # TkinterDnD.Tk() loads the tkdnd extension correctly from the start.
        # CTk widgets work with any Tk root so no combined class is needed.
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
            self.root.configure(bg="#1a1a2e")
        else:
            self.root = ctk.CTk()

        self.root.title("Image Resizer")
        self.root.geometry("860x700")
        self.root.minsize(640, 520)

        # ── State ────────────────────────────────────────────────────────
        self.file_paths: list[str] = []
        self.thumb_cards: dict[str, ThumbnailCard] = {}
        self.size_var    = ctk.StringVar(value="1024")

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.root, fg_color="#1e1e30", corner_radius=0, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🖼  Image Resizer",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#e0e0ff").pack(side="left", padx=22, pady=14)
        ctk.CTkLabel(hdr, text="Batch resize · aspect-ratio preserved",
                     font=ctk.CTkFont(size=12), text_color="#7070a0"
                     ).pack(side="left", padx=0, pady=14)

        # ── Body ─────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        # Drop zone
        self._build_drop_zone(body)

        # Settings row
        self._build_settings(body)

        # Action row
        self._build_action(body)

        # Log
        self._build_log(body)

    def _build_drop_zone(self, parent):
        """Large drag-and-drop / thumbnail area."""
        self.drop_frame = ctk.CTkFrame(
            parent, fg_color="#272740", corner_radius=14,
            border_color="#404065", border_width=2)
        self.drop_frame.pack(fill="both", expand=True)

        # ── Placeholder (shown when empty) ───────────────────────────────
        self.placeholder = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.placeholder, text="⬆",
                     font=ctk.CTkFont(size=52), text_color="#4a4a7a").pack()
        ctk.CTkLabel(self.placeholder, text="Drop images here",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="#6a6aaa").pack()
        ctk.CTkLabel(self.placeholder, text="or",
                     font=ctk.CTkFont(size=12), text_color="#505075").pack(pady=2)
        ctk.CTkButton(
            self.placeholder, text="Browse Files",
            font=ctk.CTkFont(size=13), command=self.browse_files,
            fg_color="#8a4500", hover_color="#c46000",
            width=150, height=38, corner_radius=20
        ).pack(pady=4)
        ctk.CTkLabel(self.placeholder,
                     text="JPG · PNG · BMP · GIF · TIFF · WebP",
                     font=ctk.CTkFont(size=10), text_color="#4a4a70").pack(pady=(6, 0))

        # ── Thumbnail scroll area (hidden when empty) ─────────────────────
        self.thumb_scroll = ctk.CTkScrollableFrame(
            self.drop_frame, fg_color="transparent")
        # not packed yet — shown when images arrive

        # ── "Add more" button (shown when images present) ────────────────
        self.add_more_btn = ctk.CTkButton(
            self.drop_frame, text="+ Add more",
            font=ctk.CTkFont(size=12),
            fg_color="#6a3300", hover_color="#8a4500",
            width=110, height=28, corner_radius=14,
            command=self.browse_files)
        # not packed yet

        # ── Click + DnD bindings ─────────────────────────────────────────
        self.drop_frame.bind("<Button-1>", lambda _: self.browse_files())
        if DND_AVAILABLE:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)

    def _build_settings(self, parent):
        row = ctk.CTkFrame(parent, fg_color="#272740", corner_radius=12)
        row.pack(fill="x", pady=(10, 0))

        # Size selector
        ctk.CTkLabel(row, text="Target size:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(16, 8), pady=12)
        ctk.CTkSegmentedButton(
            row, values=["512", "768", "1024"],
            variable=self.size_var, width=210,
            font=ctk.CTkFont(size=13)
        ).pack(side="left", pady=12)
        ctk.CTkLabel(row, text="px · longest side",
                     font=ctk.CTkFont(size=11), text_color="#7070a0"
                     ).pack(side="left", padx=(6, 20), pady=12)

        # Spacer
        ctk.CTkFrame(row, fg_color="transparent", width=1).pack(side="left", expand=True)

        # Auto output folder indicator
        ctk.CTkLabel(row, text="Output:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))
        self.folder_label = ctk.CTkLabel(
            row, text="Resized_<size>  next to source images",
            font=ctk.CTkFont(size=11), text_color="#8888cc",
            wraplength=220, anchor="w")
        self.folder_label.pack(side="left", padx=(0, 16), pady=12)

    def _build_action(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))

        self.resize_btn = ctk.CTkButton(
            row, text="Resize Images",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_resize,
            fg_color="#c46000", hover_color="#e07a00",
            height=44, width=180, corner_radius=22)
        self.resize_btn.pack(side="left")

        self.count_label = ctk.CTkLabel(
            row, text="No images selected",
            font=ctk.CTkFont(size=12), text_color="#6666aa")
        self.count_label.pack(side="left", padx=14)

        self.progress_label = ctk.CTkLabel(
            row, text="", font=ctk.CTkFont(size=12), text_color="#8888cc")
        self.progress_label.pack(side="right", padx=(6, 0))

        self.progress = ctk.CTkProgressBar(row, width=200, height=10, corner_radius=6)
        self.progress.set(0)
        self.progress.pack(side="right")

        # Clear button
        ctk.CTkButton(
            row, text="Clear all", command=self.clear_all,
            fg_color="#2a1010", hover_color="#552020",
            width=90, height=32, font=ctk.CTkFont(size=12), corner_radius=16
        ).pack(side="right", padx=(0, 16))

    def _build_log(self, parent):
        self.log_box = ctk.CTkTextbox(
            parent, height=130,
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color="#1a1a2a", text_color="#aaaadd",
            corner_radius=10, state="disabled")
        self.log_box.pack(fill="x", pady=(10, 0))

    # ─────────────────────────────────────────────────────────────────────
    # File management
    # ─────────────────────────────────────────────────────────────────────
    def browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")])
        if paths:
            self.add_files(list(paths))

    def _on_drop(self, event):
        """Parse paths from a DnD drop event (handles spaces-in-paths)."""
        raw = event.data
        paths = []
        for match in re.finditer(r'\{([^}]+)\}|(\S+)', raw):
            p = match.group(1) or match.group(2)
            if p:
                paths.append(p)
        valid = [p for p in paths if Path(p).suffix.lower() in SUPPORTED]
        if valid:
            self.add_files(valid)

    def add_files(self, paths: list[str]):
        new = [p for p in paths if p not in self.file_paths]
        if not new:
            return
        self.file_paths.extend(new)
        for p in new:
            self._add_card(p)
        self._refresh_grid()
        self._update_state()

    def _add_card(self, path: str):
        card = ThumbnailCard(
            self.thumb_scroll, path, on_remove=self.remove_file)
        self.thumb_cards[path] = card

    def _refresh_grid(self):
        """Re-position all cards in a tidy grid."""
        for idx, (path, card) in enumerate(self.thumb_cards.items()):
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

    def choose_output(self):
        pass  # no longer used — output folder is auto-computed

    def start_resize(self):
        if not self.file_paths:
            self._append_log("⚠  No images selected.")
            return
        size     = int(self.size_var.get())
        out_dir  = os.path.join(os.path.dirname(self.file_paths[0]), f"Resized_{size}")
        os.makedirs(out_dir, exist_ok=True)
        self.folder_label.configure(text=out_dir)
        self.resize_btn.configure(state="disabled", text="Processing…")
        self.progress.set(0)
        threading.Thread(target=self._process, args=(out_dir,), daemon=True).start()

    def _update_state(self):
        """Toggle placeholder vs thumbnail grid depending on selection."""
        count = len(self.file_paths)
        if count == 0:
            self.thumb_scroll.pack_forget()
            self.add_more_btn.pack_forget()
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.count_label.configure(text="No images selected")
        else:
            self.placeholder.place_forget()
            self.thumb_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 4))
            self.add_more_btn.pack(side="right", padx=12, pady=6)
            noun = "image" if count == 1 else "images"
            self.count_label.configure(text=f"{count} {noun} selected")

    # ─────────────────────────────────────────────────────────────────────
    # Resize logic (runs in background thread)
    # ─────────────────────────────────────────────────────────────────────
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
                img   = Image.open(path)
                w, h  = img.size
                scale = size / max(w, h)
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
            self.root.after(0, self.progress.set, pct)
            self.root.after(0, self.progress_label.configure,
                            {"text": f"{i}/{total}"})

        self._log(f"\n✅  Done — {success}/{total} resized successfully.")
        self.root.after(0, self.resize_btn.configure,
                        {"state": "normal", "text": "Resize Images"})
        self.root.after(0, self.progress.set, 1.0)

    def _log(self, msg: str):
        """Thread-safe log write."""
        self.root.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ─────────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ImageResizerApp().run()
