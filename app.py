"""Ứng dụng xử lý danh sách khám sức khỏe: gán đối tượng, ghép kết quả xét nghiệm, lập báo cáo."""
import datetime as dt
import os
import re
import sys
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

import core
import report_export

APP_DIR = Path(sys.argv[0]).resolve().parent

C_PRIMARY = "#1F5FA8"
C_PRIMARY_DARK = "#174A85"
C_BG = "#F3F6FA"
C_CARD = "#FFFFFF"
C_TEXT = "#1E2A38"
C_MUTED = "#5B6B7F"
C_OK = "#E7F5EA"
C_WARN = "#FFF4CC"
C_MISS = "#FBE0DC"
LEVEL_TAG = {"Khớp đủ": "ok", core.LEVEL_NY: "ok", "Lệch năm sinh": "warn", "Lệch số phiếu": "warn",
             "Không tìm thấy": "miss"}
LEVEL_COLOR = {"ok": C_OK, "warn": C_WARN, "miss": C_MISS}
SEP = "; "


def parse_vn_date(s):
    m = re.match(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$", s or "")
    if not m:
        return None
    return dt.date(int(m[3]), int(m[2]), int(m[1]))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Xử lý khám sức khỏe – Đối tượng & Xét nghiệm")
        self.geometry("1180x780")
        self.minsize(980, 640)
        self.configure(bg=C_BG)
        self._cache = {}
        self.report = None
        self._setup_style()

        self.var_ds = tk.StringVar()
        self.var_xn = tk.StringVar()
        self.var_out = tk.StringVar()
        self._autodetect()

        self._build_header()
        self._build_inputs()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(4, 0))
        self._build_tab_ds(nb)
        self._build_tab_xn(nb)
        self._build_tab_report(nb)
        self.status = tk.StringVar(value="Sẵn sàng. Chọn file và bấm nút ▶ ở từng bước.")
        tk.Label(self, textvariable=self.status, bg=C_BG, fg=C_MUTED, anchor="w",
                 font=("Segoe UI", 9)).pack(fill="x", padx=18, pady=6)

    # ------------------------------------------------------------ giao diện chung
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        base = ("Segoe UI", 10)
        self.option_add("*Font", base)
        s.configure(".", background=C_BG, foreground=C_TEXT, font=base)
        s.configure("Card.TFrame", background=C_CARD)
        s.configure("Card.TLabel", background=C_CARD, foreground=C_TEXT)
        s.configure("Muted.TLabel", background=C_CARD, foreground=C_MUTED, font=("Segoe UI", 9))
        s.configure("H.TLabel", background=C_CARD, foreground=C_PRIMARY, font=("Segoe UI Semibold", 11))
        s.configure("TNotebook", background=C_BG, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(18, 8), font=("Segoe UI Semibold", 10))
        s.map("TNotebook.Tab", background=[("selected", C_CARD)], foreground=[("selected", C_PRIMARY)])
        s.configure("Accent.TButton", background=C_PRIMARY, foreground="white",
                    font=("Segoe UI Semibold", 10), padding=(14, 7), borderwidth=0)
        s.map("Accent.TButton", background=[("active", C_PRIMARY_DARK), ("disabled", "#9BB3D1")])
        s.configure("TButton", padding=(10, 5))
        s.configure("Treeview", rowheight=26, background="white", fieldbackground="white")
        s.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#E4ECF6")
        s.configure("TLabelframe", background=C_CARD)
        s.configure("TLabelframe.Label", background=C_CARD, foreground=C_PRIMARY,
                    font=("Segoe UI Semibold", 10))

    def _build_header(self):
        h = tk.Frame(self, bg=C_PRIMARY, height=64)
        h.pack(fill="x")
        tk.Label(h, text="XỬ LÝ DANH SÁCH KHÁM SỨC KHỎE", bg=C_PRIMARY, fg="white",
                 font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=18, pady=(10, 0))
        tk.Label(h, text="1) Thêm cột Đối tượng  •  2) Ghép đối tượng vào kết quả xét nghiệm  •  3) Báo cáo tổng hợp (Excel / Word)",
                 bg=C_PRIMARY, fg="#D6E4F5", font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 10))

    def _card(self, parent, **pack):
        f = ttk.Frame(parent, style="Card.TFrame", padding=14)
        f.pack(**pack)
        return f

    def _build_inputs(self):
        c = self._card(self, fill="x", padx=16, pady=12)
        ttk.Label(c, text="Dữ liệu đầu vào", style="H.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        rows = [
            ("File danh sách khám\n(chọn được nhiều file):", self.var_ds, self._pick_ds),
            ("File kết quả xét nghiệm:", self.var_xn, self._pick_xn),
            ("Thư mục lưu kết quả:", self.var_out, self._pick_out),
        ]
        for i, (lb, var, cmd) in enumerate(rows, 1):
            ttk.Label(c, text=lb, style="Card.TLabel").grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)
            ttk.Entry(c, textvariable=var).grid(row=i, column=1, sticky="ew", pady=3)
            ttk.Button(c, text="Chọn…", command=cmd).grid(row=i, column=2, padx=(8, 0), pady=3)
        c.columnconfigure(1, weight=1)

    def _autodetect(self):
        files = sorted(APP_DIR.glob("*.xls*"))
        files = [f for f in files if "DOI TUONG" not in f.name.upper() and not f.name.startswith("~$")]
        ds = [f for f in files if f.name.upper().startswith("DANH SACH")]
        xn = [f for f in files if f.name.upper().startswith("XN")]
        if ds:
            self.var_ds.set(SEP.join(str(f) for f in ds))
        if xn:
            self.var_xn.set(str(xn[0]))
        self.var_out.set(str(APP_DIR))

    def _pick_ds(self):
        ps = filedialog.askopenfilenames(title="Chọn file danh sách khám (giữ Ctrl để chọn nhiều file)",
                                         filetypes=[("Excel", "*.xlsx *.xlsm")])
        if ps:
            self.var_ds.set(SEP.join(ps))
            self.var_out.set(str(Path(ps[0]).parent))

    def _pick_xn(self):
        p = filedialog.askopenfilename(title="Chọn file kết quả xét nghiệm", filetypes=[("Excel", "*.xls *.xlsx")])
        if p:
            self.var_xn.set(p)

    def _pick_out(self):
        p = filedialog.askdirectory(title="Chọn thư mục lưu")
        if p:
            self.var_out.set(p)

    def _make_tree(self, parent, columns, widths):
        wrap = ttk.Frame(parent, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, pady=(10, 0))
        tv = ttk.Treeview(wrap, columns=columns, show="headings")
        for col, w in zip(columns, widths):
            tv.heading(col, text=col)
            tv.column(col, width=w, anchor="w" if w >= 150 else "center", stretch=w >= 150)
        ys = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
        xs = ttk.Scrollbar(wrap, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        tv.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        tv.tag_configure("odd", background="#F7F9FC")
        tv.tag_configure("ok", background=C_OK)
        tv.tag_configure("warn", background=C_WARN)
        tv.tag_configure("miss", background=C_MISS)
        tv.tag_configure("total", font=("Segoe UI Semibold", 10), background="#EEF2F7")
        return tv

    # ------------------------------------------------------------ dữ liệu
    def _load(self, kind):
        raw = (self.var_ds if kind == "ds" else self.var_xn).get()
        paths = [x.strip() for x in raw.split(";") if x.strip()] if kind == "ds" else [raw.strip()]
        label = "danh sách" if kind == "ds" else "kết quả xét nghiệm"
        if not paths or not paths[0]:
            raise ValueError(f"Chưa chọn file {label}.")
        for p in paths:
            if not Path(p).exists():
                raise ValueError(f"Không tìm thấy file {label}: {p}")
        key = (kind, tuple((p, os.path.getmtime(p)) for p in paths))
        if key not in self._cache:
            self.status.set("Đang đọc " + ", ".join(Path(p).name for p in paths) + " …")
            self.update_idletasks()
            self._cache[key] = core.DanhSach(paths) if kind == "ds" else core.KetQuaXN(paths[0])
        return self._cache[key]

    def _out_dir(self):
        d = Path(self.var_out.get().strip() or APP_DIR)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _run(self, fn):
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            fn()
        except PermissionError as e:
            messagebox.showerror("Không ghi được file", f"File đang mở trong Excel/Word? Hãy đóng lại rồi thử lại.\n\n{e}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Lỗi", str(e))
            self.status.set("Lỗi: " + str(e))
        finally:
            self.config(cursor="")

    def _desc(self, parent, text):
        lb = ttk.Label(parent, style="Muted.TLabel", text=text, justify="left")
        lb.pack(anchor="w", fill="x")
        lb.bind("<Configure>", lambda e: lb.configure(wraplength=e.width - 4))

    def _done(self, path, msg):
        self.status.set(f"{msg.splitlines()[0]}  →  {path}")
        if messagebox.askyesno("Hoàn tất", f"{msg}\n\nĐã lưu: {path}\n\nMở file ngay?"):
            os.startfile(path)

    # ------------------------------------------------------------ Bước 1
    def _build_tab_ds(self, nb):
        tab = ttk.Frame(nb, style="Card.TFrame", padding=14)
        nb.add(tab, text="  1. Danh sách – thêm cột Đối tượng  ")
        self._desc(tab, (
            "Với mỗi dòng, các cột nhóm (Người cao tuổi, Người có công, Khuyết tật, Hộ nghèo, Cận nghèo, DTTS, "
            "Trẻ dưới 6 tuổi, Khác) có giá trị 1 sẽ được ghi vào cột mới “Đối tượng” ở cuối mỗi sheet. "
            "File gốc giữ nguyên, kết quả lưu thành file mới. File đã có sẵn cột “Đối tượng” (ghi tắt NCT, NKT, CC…) "
            "chỉ được đọc để ghép, không ghi lại."))
        bar = ttk.Frame(tab, style="Card.TFrame")
        bar.pack(fill="x", pady=(10, 0))
        ttk.Button(bar, text="▶  Thêm cột Đối tượng & lưu file", style="Accent.TButton",
                   command=lambda: self._run(self._do_ds)).pack(side="left")
        ttk.Label(bar, text="Lọc:", style="Card.TLabel").pack(side="left", padx=(20, 4))
        self.ds_filter = ttk.Combobox(bar, state="readonly", width=32, values=["Tất cả"])
        self.ds_filter.set("Tất cả")
        self.ds_filter.pack(side="left")
        self.ds_filter.bind("<<ComboboxSelected>>", lambda e: self._fill_ds())
        self.ds_info = tk.StringVar()
        ttk.Label(bar, textvariable=self.ds_info, style="Card.TLabel").pack(side="right")
        self.tv_ds = self._make_tree(tab, ("File", "Sheet", "Dòng", "Số phiếu", "Họ và tên", "Năm sinh", "Đối tượng"),
                                     (150, 130, 60, 80, 220, 80, 300))

    def _do_ds(self):
        ds = self._load("ds")
        saved = ds.save_with_doi_tuong(self._out_dir())
        self.ds_filter["values"] = ["Tất cả", "(Trống – không thuộc nhóm nào)"] + ds.group_labels
        self._fill_ds()
        if not saved:
            self.status.set(f"Đã đọc {len(ds.persons)} người. Các file đã có sẵn cột Đối tượng, không cần ghi lại.")
            messagebox.showinfo("Hoàn tất", "Các file đã chọn đều có sẵn cột “Đối tượng” nên không cần ghi file mới.")
            return
        lines = []
        for out, stats in saved.items():
            lines.append(Path(out).name)
            lines += [f"  • {k}: {v} người có đối tượng" for k, v in stats.items()]
        self._done(str(next(iter(saved))), f"Đã thêm cột Đối tượng ({len(saved)} file).\n" + "\n".join(lines))

    def _fill_ds(self):
        ds = self._load("ds")
        f = self.ds_filter.get()
        self.tv_ds.delete(*self.tv_ds.get_children())
        n = 0
        for p in ds.persons:
            if f.startswith("(Trống") and p.groups or f in ds.group_labels and f not in p.groups:
                continue
            self.tv_ds.insert("", "end", values=(Path(p.file).stem, p.sheet, p.row, p.phieu or "", p.name,
                                                 p.year or "", p.doi_tuong),
                              tags=("odd",) if n % 2 else ())
            n += 1
        self.ds_info.set(f"Hiển thị {n}/{len(ds.persons)} người")

    # ------------------------------------------------------------ Bước 2
    def _build_tab_xn(self, nb):
        tab = ttk.Frame(nb, style="Card.TFrame", padding=14)
        nb.add(tab, text="  2. Kết quả XN – điền Đối tượng  ")
        self._desc(tab, (
            "Ghép từng dòng xét nghiệm với danh sách theo Họ tên + Số phiếu + Năm sinh rồi ghi vào cột Đối tượng (cột G). "
            "Nếu không khớp đủ, thử Họ tên + Số phiếu, rồi Họ tên + Năm sinh (danh sách không có số phiếu thì ghép theo "
            "Họ tên + Năm sinh). Dòng xanh = đã khớp, vàng = cần kiểm tra, đỏ = không tìm thấy. "
            "File kết quả có thêm sheet “Kiem tra ghep”."))
        bar = ttk.Frame(tab, style="Card.TFrame")
        bar.pack(fill="x", pady=(10, 0))
        ttk.Button(bar, text="▶  Ghép đối tượng & lưu file XN", style="Accent.TButton",
                   command=lambda: self._run(self._do_xn)).pack(side="left")
        ttk.Label(bar, text="Lọc:", style="Card.TLabel").pack(side="left", padx=(20, 4))
        self.xn_filter = ttk.Combobox(bar, state="readonly", width=24, values=["Tất cả"] + core.LEVELS)
        self.xn_filter.set("Tất cả")
        self.xn_filter.pack(side="left")
        self.xn_filter.bind("<<ComboboxSelected>>", lambda e: self._fill_xn())
        self.chips = ttk.Frame(tab, style="Card.TFrame")
        self.chips.pack(fill="x", pady=(10, 0))
        self.tv_xn = self._make_tree(tab, ("Dòng", "Ngày lấy mẫu", "Số phiếu", "Họ tên", "Năm sinh", "Đối tượng", "Mức ghép"),
                                     (60, 100, 80, 220, 80, 280, 170))

    def _do_xn(self):
        ds, xn = self._load("ds"), self._load("xn")
        cnt = xn.match(ds)
        out = self._out_dir() / f"{Path(xn.path).stem} - DOI TUONG{Path(xn.path).suffix}"
        xn.save_with_doi_tuong(out)
        for w in self.chips.winfo_children():
            w.destroy()
        for k, v in cnt.items():
            tk.Label(self.chips, text=f"  {k}: {v}  ", bg=LEVEL_COLOR[LEVEL_TAG[k]], fg=C_TEXT,
                     font=("Segoe UI Semibold", 10), padx=6, pady=4).pack(side="left", padx=(0, 8))
        self._fill_xn()
        miss_dates = sorted({x.date for x in xn.rows if x.person is None and x.date})
        hint = ""
        if miss_dates:
            hint = "\n\nNgày có dòng không tìm thấy trong DS: " + ", ".join(core.fmt_date(d)[:5] for d in miss_dates)
        self._done(str(out), f"Đã điền đối tượng cho {len(xn.rows)} dòng xét nghiệm.\n"
                   + "\n".join(f"  • {k}: {v}" for k, v in cnt.items()) + hint)

    def _fill_xn(self):
        xn = self._load("xn")
        f = self.xn_filter.get()
        self.tv_xn.delete(*self.tv_xn.get_children())
        for x in xn.rows:
            if not x.level or (f != "Tất cả" and x.level != f):
                continue
            self.tv_xn.insert("", "end", tags=(LEVEL_TAG[x.level],), values=(
                x.row + 1, core.fmt_date(x.date), x.phieu or "", x.name, x.year or "",
                x.person.doi_tuong if x.person else "", x.level))

    # ------------------------------------------------------------ Bước 3
    def _build_tab_report(self, nb):
        tab = ttk.Frame(nb, style="Card.TFrame", padding=14)
        nb.add(tab, text="  3. Báo cáo tổng hợp  ")
        form = ttk.LabelFrame(tab, text="Thông tin báo cáo", padding=10)
        form.pack(fill="x")
        self.info = {k: tk.StringVar(value=v) for k, v in (
            ("co_quan", "SỞ Y TẾ THÀNH PHỐ ĐÀ NẴNG"),
            ("don_vi", "BỆNH VIỆN VIỆT - HÀN ĐÀ NẴNG"),
            ("tieu_de", "Báo cáo tổng hợp số lượng xét nghiệm theo đối tượng"),
            ("dia_ban", "Khám sức khỏe định kỳ cho người dân"),
            ("noi_ky", "Đà Nẵng"),
        )}
        self.var_from, self.var_to = tk.StringVar(), tk.StringVar()
        fields = [("Cơ quan chủ quản:", "co_quan"), ("Đơn vị:", "don_vi"), ("Tiêu đề:", "tieu_de"),
                  ("Dòng phụ (địa bàn):", "dia_ban"), ("Nơi ký:", "noi_ky")]
        for i, (lb, k) in enumerate(fields):
            r, c = divmod(i, 2)
            ttk.Label(form, text=lb, style="Card.TLabel").grid(row=r, column=c * 2, sticky="w", padx=(0 if c == 0 else 16, 6), pady=3)
            ttk.Entry(form, textvariable=self.info[k]).grid(row=r, column=c * 2 + 1, sticky="ew", pady=3)
        r = len(fields) // 2
        ttk.Label(form, text="Từ ngày – đến ngày:", style="Card.TLabel").grid(row=r, column=2, sticky="w", padx=(16, 6))
        dates = ttk.Frame(form, style="Card.TFrame")
        dates.grid(row=r, column=3, sticky="w")
        ttk.Entry(dates, textvariable=self.var_from, width=12).pack(side="left")
        ttk.Label(dates, text=" – ", style="Card.TLabel").pack(side="left")
        ttk.Entry(dates, textvariable=self.var_to, width=12).pack(side="left")
        ttk.Label(dates, text="  (dd/mm/yyyy, để trống = tất cả)", style="Muted.TLabel").pack(side="left")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        bar = ttk.Frame(tab, style="Card.TFrame")
        bar.pack(fill="x", pady=(10, 0))
        ttk.Button(bar, text="▶  Lập báo cáo", style="Accent.TButton",
                   command=lambda: self._run(self._do_report)).pack(side="left")
        self.btn_xlsx = ttk.Button(bar, text="Xuất Excel", state="disabled", command=lambda: self._run(lambda: self._export("xlsx")))
        self.btn_docx = ttk.Button(bar, text="Xuất Word", state="disabled", command=lambda: self._run(lambda: self._export("docx")))
        self.btn_xlsx.pack(side="left", padx=(10, 0))
        self.btn_docx.pack(side="left", padx=(6, 0))
        self.rep_info = tk.StringVar(value="Đếm số người làm từng xét nghiệm, chia theo đối tượng.")
        ttk.Label(bar, textvariable=self.rep_info, style="Muted.TLabel").pack(side="right")
        self.rep_wrap = ttk.Frame(tab, style="Card.TFrame")
        self.rep_wrap.pack(fill="both", expand=True)
        self.tv_rep = None

    def _do_report(self):
        ds, xn = self._load("ds"), self._load("xn")
        xn.match(ds)
        if xn.title_rows and xn.title_rows[0]:
            self._fill_info_from_xn(xn)
        d1, d2 = parse_vn_date(self.var_from.get()), parse_vn_date(self.var_to.get())
        for s, d in ((self.var_from.get(), d1), (self.var_to.get(), d2)):
            if s.strip() and d is None:
                raise ValueError(f"Ngày '{s}' không đúng dạng dd/mm/yyyy.")
        self.report = rep = core.build_report(xn, ds, d1, d2)
        if not self.var_from.get().strip():
            self.var_from.set(core.fmt_date(rep.date_from))
        if not self.var_to.get().strip():
            self.var_to.set(core.fmt_date(rep.date_to))

        cols = ["Tên xét nghiệm"] + rep.columns + [core.COL_TOTAL]
        if self.tv_rep is not None:
            self.tv_rep.master.destroy()
        self.tv_rep = self._make_tree(self.rep_wrap, cols, [210] + [110] * (len(cols) - 1))
        for i, (t, v) in enumerate(rep.table.items()):
            self.tv_rep.insert("", "end", values=[t] + [v[c] for c in cols[1:]], tags=("odd",) if i % 2 else ())
        self.tv_rep.insert("", "end", values=["Số người được xét nghiệm"] + [rep.total_people[c] for c in cols[1:]],
                           tags=("total",))
        unknown = rep.total_people[core.COL_UNKNOWN]
        self.rep_info.set(f"{rep.total_people[core.COL_TOTAL]} người • {unknown} người chưa xác định đối tượng")
        self.btn_xlsx.config(state="normal")
        self.btn_docx.config(state="normal")
        self.status.set("Đã lập báo cáo. Bấm Xuất Excel / Xuất Word để lưu.")

    def _fill_info_from_xn(self, xn):
        """Lấy tên cơ quan/đơn vị/địa bàn từ phần tiêu đề file XN (chỉ khi người dùng chưa sửa)."""
        if getattr(self, "_info_filled", False):
            return
        self._info_filled = True
        t = xn.title_rows
        if t[0] and core.has_value(t[0][0]):
            self.info["co_quan"].set(core.nfc(t[0][0]))
        if len(t) > 1 and t[1] and core.has_value(t[1][0]):
            self.info["don_vi"].set(core.nfc(t[1][0]))
        for c in t[0]:
            m = re.search(r"\bXÃ\s+(.+)$", core.nfc(c))
            if m:
                self.info["dia_ban"].set("Khám sức khỏe định kỳ cho người dân xã " + m.group(1).title())
                break

    def _export(self, kind):
        if not self.report:
            raise ValueError("Hãy bấm “Lập báo cáo” trước.")
        info = {k: v.get().strip() for k, v in self.info.items()}
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        out = self._out_dir() / f"BAO CAO XN THEO DOI TUONG {stamp}.{kind}"
        if kind == "xlsx":
            report_export.export_excel(self.report, out, info)
        else:
            report_export.export_word(self.report, out, info)
        self._done(str(out), f"Đã xuất báo cáo {'Excel' if kind == 'xlsx' else 'Word'}.")


if __name__ == "__main__":
    App().mainloop()
