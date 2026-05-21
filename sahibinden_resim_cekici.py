"""
Sahibinden Resim Çekici
- Kaynak kodu yapıştır, JPG resimleri önizle ve indir
- Gereksinimler: pip install Pillow requests
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import threading
import os
import io
import urllib.request

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Hata", "Pillow kurulu değil!\nKomut satırına yaz:\npip install Pillow requests")
    raise SystemExit

# ─── Sabitler ────────────────────────────────────────────────────────────────

THUMB_SIZE   = (160, 120)
PREVIEW_SIZE = (700, 525)
COLS         = 4
BG           = "#0f0f0f"
SURFACE      = "#1a1a1a"
BORDER       = "#2e2e2e"
ACCENT       = "#f0c040"
TEXT         = "#eeebe6"
MUTED        = "#777"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.sahibinden.com/",
}

# ─── URL Çekme ───────────────────────────────────────────────────────────────

def extract_jpg_groups(html: str) -> list[dict]:
    """
    HTML kaynağından JPG resim gruplarını çıkarır.
    Her grup: thumb_url (önizleme) + full_url (tam boyut).
    thmb_ prefix'li  → küçük thumbnail
    x16_ / x5_ vb.  → büyük versiyon
    prefix yok       → orijinal
    """
    pattern = re.compile(
        r"https://i\d+\.shbdn\.com/photos/[\w/]+\.jpg",
        re.IGNORECASE,
    )
    all_urls = list(dict.fromkeys(pattern.findall(html)))  # sırayı koru, tekrar yok

    thumbs = [u for u in all_urls if "/thmb_" in u]
    fulls  = [u for u in all_urls if "/thmb_" not in u]

    # Thumbnail'dan suffix'i çıkar, full ile eşleştir
    def suffix(url):
        fname = url.rsplit("/", 1)[-1]          # örn: thmb_1316519601gzy.jpg
        fname = re.sub(r"^thmb_", "", fname)    # → 1316519601gzy.jpg
        fname = re.sub(r"^x\d+_", "", fname)    # prefix'li full için
        return fname

    full_by_suffix = {}
    for u in fulls:
        full_by_suffix[suffix(u)] = u

    groups = []
    seen = set()
    for t in thumbs:
        s = suffix(t)
        if s in seen:
            continue
        seen.add(s)
        full = full_by_suffix.get(s, t)  # full bulunamazsa thumb'ı kullan
        groups.append({"thumb": t, "full": full, "suffix": s})

    # Eşleşmeyen full'ları da ekle
    for u in fulls:
        s = suffix(u)
        if s not in seen:
            seen.add(s)
            groups.append({"thumb": u, "full": u, "suffix": s})

    return groups


# ─── Resim İndirme ───────────────────────────────────────────────────────────

def fetch_image(url: str, size: tuple | None = None) -> ImageTk.PhotoImage | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        if size:
            img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def download_file(url: str, dest_path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            with open(dest_path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception:
        return False


# ─── Ana Uygulama ─────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sahibinden Resim Çekici")
        self.configure(bg=BG)
        self.geometry("1050x750")
        self.minsize(800, 600)

        self.groups: list[dict] = []          # {thumb, full, suffix, tk_img, selected}
        self.thumb_cache: dict[str, ImageTk.PhotoImage] = {}
        self.loading_lock = threading.Lock()

        self._build_ui()

    # ── UI kurulumu ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self._style()

        # ── Alt footer (önce pack edilmeli) ──
        footer = tk.Frame(self, bg="#111", height=32)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        made_by = tk.Label(footer, text="♥  Toprak tarafından yapıldı",
                           font=("Courier", 10, "bold"), fg="#555", bg="#111",
                           cursor="hand2")
        made_by.pack(expand=True)
        made_by.bind("<Enter>", lambda e: made_by.config(fg=ACCENT))
        made_by.bind("<Leave>", lambda e: made_by.config(fg="#555"))
        made_by.bind("<Button-1>", lambda e: __import__("webbrowser").open(
            "https://github.com/toprak1224"))

        # ── Sol panel: kaynak giriş ──
        left = tk.Frame(self, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(14, 0), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Sahibinden", font=("Courier", 13, "bold"),
                 fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(left, text="Resim Çekici", font=("Courier", 11),
                 fg=TEXT, bg=BG).pack(anchor="w")
        # ── Kullanım talimatları ──
        info_frame = tk.Frame(left, bg="#141414",
                              highlightthickness=1, highlightbackground=BORDER)
        info_frame.pack(fill="x", pady=(12, 0))

        tk.Label(info_frame, text="  Nasıl kullanılır?",
                 font=("Courier", 8, "bold"), fg=ACCENT, bg="#141414",
                 anchor="w").pack(fill="x", padx=6, pady=(6, 2))

        steps = [
            "1. Sahibinden ilan sayfasını aç",
            "2. Sağ tıkla → 'Sayfa Kaynağını",
            "   Görüntüle'  ya da  Ctrl + U",
            "3. Açılan sayfada  Ctrl + A  ile",
            "   tüm kodu seç,  Ctrl + C  ile",
            "   kopyala",
            "4. Aşağıya  Ctrl + V  ile yapıştır",
            "5. ▶ Çek butonuna tıkla",
        ]
        for s in steps:
            tk.Label(info_frame, text=s, font=("Courier", 7),
                     fg="#aaa", bg="#141414", anchor="w",
                     justify="left").pack(fill="x", padx=10)
        tk.Label(info_frame, text="", bg="#141414").pack(pady=2)

        tk.Label(left, text="Kaynak kodu buraya yapıştır:",
                 font=("Courier", 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(10, 3))

        self.txt = tk.Text(left, bg=SURFACE, fg="#666", insertbackground=TEXT,
                           relief="flat", font=("Courier", 8),
                           highlightthickness=1, highlightbackground=BORDER,
                           highlightcolor=ACCENT)
        self.txt.pack(fill="both", expand=True)
        self.txt.insert("1.0", "Ctrl+A → Ctrl+V ile yapıştır...")
        self.txt.bind("<FocusIn>", self._clear_placeholder)

        btn_frame = tk.Frame(left, bg=BG)
        btn_frame.pack(fill="x", pady=(8, 0))

        self._btn(btn_frame, "▶  Çek", self._parse, ACCENT, "#000").pack(fill="x", pady=2)
        self._btn(btn_frame, "✕  Temizle", self._clear_all, SURFACE, MUTED,
                  border=True).pack(fill="x", pady=2)

        self.lbl_status = tk.Label(left, text="", font=("Courier", 8),
                                   fg=MUTED, bg=BG, wraplength=260, justify="left")
        self.lbl_status.pack(anchor="w", pady=(6, 0))

        # ── Sağ panel: galeri ──
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=14, pady=14)

        # Üst bar
        top_bar = tk.Frame(right, bg=BG)
        top_bar.pack(fill="x", pady=(0, 8))

        self.lbl_count = tk.Label(top_bar, text="", font=("Courier", 8),
                                  fg=MUTED, bg=BG)
        self.lbl_count.pack(side="left")

        self._btn(top_bar, "⬇  Seçilenleri İndir", self._download_selected,
                  "#c04000", "#fff").pack(side="right")
        self._btn(top_bar, "Tümünü Seç", self._select_all,
                  SURFACE, MUTED, border=True).pack(side="right", padx=4)
        self._btn(top_bar, "Seçimi Temizle", self._deselect_all,
                  SURFACE, MUTED, border=True).pack(side="right")

        # Galeri canvas + scrollbar
        gallery_frame = tk.Frame(right, bg=BG)
        gallery_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(gallery_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(gallery_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.gallery_inner = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.gallery_inner, anchor="nw")

        self.gallery_inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._show_placeholder()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        troughcolor=SURFACE, background=BORDER,
                        arrowcolor=MUTED, bordercolor=BG)

    def _btn(self, parent, text, cmd, bg, fg, border=False):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                      font=("Courier", 8, "bold"), relief="flat",
                      padx=10, pady=5, cursor="hand2",
                      highlightthickness=1 if border else 0,
                      highlightbackground=BORDER)
        return b

    # ── Placeholder & temizleme ───────────────────────────────────────────────

    def _clear_placeholder(self, _event=None):
        if self.txt.get("1.0", "end-1c") == "Ctrl+A → Ctrl+V ile yapıştır...":
            self.txt.delete("1.0", tk.END)
            self.txt.configure(fg=TEXT)

    def _show_placeholder(self):
        for w in self.gallery_inner.winfo_children():
            w.destroy()
        tk.Label(self.gallery_inner,
                 text="Kaynak kodu yapıştırıp\n▶ Çek butonuna tıkla",
                 font=("Courier", 10), fg="#333", bg=BG).pack(pady=80)

    def _clear_all(self):
        self.txt.delete("1.0", tk.END)
        self.txt.insert("1.0", "Ctrl+A → Ctrl+V ile yapıştır...")
        self.txt.configure(fg="#666")
        self.groups = []
        self.thumb_cache.clear()
        self._show_placeholder()
        self.lbl_count.config(text="")
        self.lbl_status.config(text="")

    # ── Parse ─────────────────────────────────────────────────────────────────

    def _parse(self):
        html = self.txt.get("1.0", tk.END)
        if not html.strip() or html.strip() == "Ctrl+A → Ctrl+V ile yapıştır...":
            self.lbl_status.config(text="⚠ Önce kaynak kodu yapıştır!", fg="#f06040")
            return

        self.lbl_status.config(text="İşleniyor...", fg=MUTED)
        self.update()

        groups = extract_jpg_groups(html)
        if not groups:
            self.lbl_status.config(text="⚠ JPG resim bulunamadı.", fg="#f06040")
            return

        self.groups = [dict(g, tk_img=None, selected=False) for g in groups]
        self.thumb_cache.clear()
        self.lbl_status.config(text=f"✓ {len(groups)} resim bulundu.", fg=ACCENT)
        self._render_gallery()
        self._load_thumbs_async()

    # ── Galeri render ─────────────────────────────────────────────────────────

    def _render_gallery(self):
        for w in self.gallery_inner.winfo_children():
            w.destroy()

        for i, g in enumerate(self.groups):
            row, col = divmod(i, COLS)
            cell = tk.Frame(self.gallery_inner, bg=SURFACE,
                            highlightthickness=1,
                            highlightbackground=ACCENT if g["selected"] else BORDER,
                            cursor="hand2")
            cell.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Resim alanı
            img_frame = tk.Frame(cell, bg="#111", width=THUMB_SIZE[0], height=THUMB_SIZE[1])
            img_frame.pack()
            img_frame.pack_propagate(False)

            lbl_img = tk.Label(img_frame, bg="#111", text="⏳", fg="#444",
                               font=("Courier", 10))
            lbl_img.place(relx=0.5, rely=0.5, anchor="center")

            g["lbl_img"] = lbl_img
            g["cell"] = cell

            # Alt bar
            bottom = tk.Frame(cell, bg=SURFACE)
            bottom.pack(fill="x", padx=4, pady=3)

            fname = g["suffix"][:16] + ("…" if len(g["suffix"]) > 16 else "")
            tk.Label(bottom, text=fname, font=("Courier", 7),
                     fg=MUTED, bg=SURFACE).pack(side="left")

            # Tıklama: seç/kaldır
            for w in (cell, img_frame, lbl_img):
                w.bind("<Button-1>", lambda e, idx=i: self._toggle_select(idx))

            # Çift tık: büyük önizleme
            for w in (cell, img_frame, lbl_img):
                w.bind("<Double-Button-1>", lambda e, idx=i: self._preview(idx))

            # Tek sağ tık: menü
            cell.bind("<Button-3>", lambda e, idx=i: self._right_menu(e, idx))

        self._update_count()

    def _update_count(self):
        sel = sum(1 for g in self.groups if g["selected"])
        total = len(self.groups)
        self.lbl_count.config(text=f"{total} resim  •  {sel} seçili", fg=MUTED)

    # ── Thumbnail async yükleme ───────────────────────────────────────────────

    def _load_thumbs_async(self):
        def worker():
            for i, g in enumerate(self.groups):
                url = g["thumb"]
                photo = None
                if url in self.thumb_cache:
                    photo = self.thumb_cache[url]
                else:
                    photo = fetch_image(url, THUMB_SIZE)
                    if photo:
                        with self.loading_lock:
                            self.thumb_cache[url] = photo

                self.after(0, self._set_thumb, i, photo)

        threading.Thread(target=worker, daemon=True).start()

    def _set_thumb(self, idx: int, photo):
        if idx >= len(self.groups):
            return
        g = self.groups[idx]
        lbl = g.get("lbl_img")
        if not lbl or not lbl.winfo_exists():
            return
        if photo:
            g["tk_img"] = photo
            lbl.config(image=photo, text="")
        else:
            lbl.config(text="✕", fg="#c04000")

    # ── Seçim ─────────────────────────────────────────────────────────────────

    def _toggle_select(self, idx: int):
        g = self.groups[idx]
        g["selected"] = not g["selected"]
        cell = g.get("cell")
        if cell and cell.winfo_exists():
            cell.config(highlightbackground=ACCENT if g["selected"] else BORDER)
        self._update_count()

    def _select_all(self):
        for g in self.groups:
            g["selected"] = True
            if c := g.get("cell"):
                c.config(highlightbackground=ACCENT)
        self._update_count()

    def _deselect_all(self):
        for g in self.groups:
            g["selected"] = False
            if c := g.get("cell"):
                c.config(highlightbackground=BORDER)
        self._update_count()

    # ── Önizleme (çift tık) ───────────────────────────────────────────────────

    def _preview(self, idx: int):
        g = self.groups[idx]
        url = g["full"]

        win = tk.Toplevel(self)
        win.title(g["suffix"])
        win.configure(bg=BG)
        win.geometry("760x600")

        lbl = tk.Label(win, text="Yükleniyor...", fg=MUTED, bg=BG,
                       font=("Courier", 10))
        lbl.pack(expand=True)

        info = tk.Label(win, text=url, fg="#444", bg=BG,
                        font=("Courier", 7), wraplength=720)
        info.pack(pady=(0, 4))

        def dl_btn_cmd():
            self._download_one(idx, win)

        tk.Button(win, text="⬇  Bu resmi indir", command=dl_btn_cmd,
                  bg=ACCENT, fg="#000", font=("Courier", 9, "bold"),
                  relief="flat", padx=10, pady=5).pack(pady=(0, 10))

        def load():
            photo = fetch_image(url, PREVIEW_SIZE)
            def show():
                if not win.winfo_exists():
                    return
                if photo:
                    lbl.config(image=photo, text="")
                    lbl.image = photo  # referans tut
                else:
                    lbl.config(text="⚠ Resim yüklenemedi", fg="#f06040")
            win.after(0, show)

        threading.Thread(target=load, daemon=True).start()

    # ── İndirme ───────────────────────────────────────────────────────────────

    def _download_one(self, idx: int, parent=None):
        g = self.groups[idx]
        url = g["full"]
        fname = url.rsplit("/", 1)[-1]
        dest = filedialog.asksaveasfilename(
            parent=parent or self,
            initialfile=fname,
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("Tüm dosyalar", "*.*")],
        )
        if not dest:
            return
        if download_file(url, dest):
            messagebox.showinfo("Tamam", f"İndirildi:\n{dest}", parent=parent or self)
        else:
            messagebox.showerror("Hata", "İndirme başarısız.", parent=parent or self)

    def _download_selected(self):
        sel = [g for g in self.groups if g["selected"]]
        if not sel:
            messagebox.showwarning("Uyarı", "Hiç resim seçilmedi!")
            return

        folder = filedialog.askdirectory(title="Kayıt klasörünü seç")
        if not folder:
            return

        prog_win = tk.Toplevel(self)
        prog_win.title("İndiriliyor...")
        prog_win.configure(bg=BG)
        prog_win.geometry("360x110")
        prog_win.resizable(False, False)

        tk.Label(prog_win, text=f"{len(sel)} resim indiriliyor...",
                 fg=TEXT, bg=BG, font=("Courier", 9)).pack(pady=(14, 4))

        bar = ttk.Progressbar(prog_win, length=320, mode="determinate",
                              maximum=len(sel))
        bar.pack(pady=4)

        lbl_prog = tk.Label(prog_win, text="", fg=MUTED, bg=BG, font=("Courier", 8))
        lbl_prog.pack()

        def worker():
            ok = 0
            for i, g in enumerate(sel):
                url = g["full"]
                fname = url.rsplit("/", 1)[-1]
                dest = os.path.join(folder, fname)
                # Aynı isim varsa numara ekle
                if os.path.exists(dest):
                    base, ext = os.path.splitext(fname)
                    dest = os.path.join(folder, f"{base}_{i}{ext}")
                success = download_file(url, dest)
                if success:
                    ok += 1
                prog_win.after(0, lambda v=i+1, f=fname: (
                    bar.configure(value=v),
                    lbl_prog.configure(text=f)
                ))

            prog_win.after(0, lambda: (
                prog_win.destroy(),
                messagebox.showinfo("Tamam",
                    f"{ok}/{len(sel)} resim indirildi.\nKlasor: {folder}")
            ))

        threading.Thread(target=worker, daemon=True).start()

    # ── Sağ tık menüsü ───────────────────────────────────────────────────────

    def _right_menu(self, event, idx: int):
        menu = tk.Menu(self, tearoff=0, bg=SURFACE, fg=TEXT,
                       activebackground=ACCENT, activeforeground="#000",
                       font=("Courier", 9))
        menu.add_command(label="🔍 Önizle", command=lambda: self._preview(idx))
        menu.add_command(label="⬇ İndir", command=lambda: self._download_one(idx))
        menu.add_separator()
        menu.add_command(label="✓ Seç / Kaldır",
                         command=lambda: self._toggle_select(idx))
        menu.tk_popup(event.x_root, event.y_root)

    # ── Scroll yardımcıları ───────────────────────────────────────────────────

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ─── Giriş noktası ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
