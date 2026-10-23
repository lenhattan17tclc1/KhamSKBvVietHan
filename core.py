"""Xử lý dữ liệu: đọc danh sách khám, gán đối tượng, ghép kết quả xét nghiệm, tổng hợp."""
import datetime as dt
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from copy import copy

# ---------------------------------------------------------------- tiện ích


def nfc(s):
    return " ".join(unicodedata.normalize("NFC", str(s or "")).split())


def key_text(s):
    """Chuẩn hoá để so sánh: bỏ dấu, viết hoa, gộp khoảng trắng.
    Tránh lệch do kiểu bỏ dấu (THUỲ / THÙY) hoặc gõ dấu khác bảng mã."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("Đ", "D").replace("đ", "d")
    return " ".join(s.upper().split())


def parse_int(v):
    if v is None or v == "":
        return None
    try:
        return int(float(str(v).strip()))
    except ValueError:
        return None


def parse_year(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.year
    if isinstance(v, (int, float)):
        v = int(v)
        if 1900 <= v <= 2100:
            return v
        if 3000 < v < 80000:  # số serial ngày của Excel
            return (dt.datetime(1899, 12, 30) + dt.timedelta(days=v)).year
        return None
    m = re.search(r"\b(19\d{2}|20\d{2})\b", str(v or ""))
    return int(m.group(1)) if m else None


def is_one(v):
    if isinstance(v, (int, float)):
        return v == 1
    return str(v or "").strip() == "1"


def has_value(v):
    return v is not None and str(v).strip() != ""


def fmt_date(d):
    return d.strftime("%d/%m/%Y") if d else ""


# ---------------------------------------------------------------- danh sách

LEVEL_OK = "Khớp đủ"
LEVEL_NY = "Khớp họ tên + năm sinh"
LEVELS = [LEVEL_OK, LEVEL_NY, "Lệch năm sinh", "Lệch số phiếu", "Không tìm thấy"]
GOOD_LEVELS = {LEVEL_OK, LEVEL_NY}

@dataclass
class Person:
    file: str
    sheet: str
    row: int
    name: str
    phieu: int
    year: int
    groups: list = field(default_factory=list)

    @property
    def doi_tuong(self):
        return ", ".join(self.groups)


def _group_label(header):
    return nfc(str(header).split("\n")[0])


GROUP_ORDER = ["Người cao tuổi", "Người có công", "Người khuyết tật", "Hộ nghèo", "Hộ cận nghèo",
               "Dân tộc thiểu số/hải đảo", "Trẻ em dưới 6 tuổi", "Khác"]
# Cách ghi tắt / khác nhau trong cột "Đối tượng" có sẵn -> tên nhóm chuẩn
_DT_ALIAS = {
    "NCT": "Người cao tuổi", "NGUOI CAO TUOI": "Người cao tuổi", "CAO TUOI": "Người cao tuổi",
    "CC": "Người có công", "NCC": "Người có công", "NGUOI CO CONG": "Người có công", "CO CONG": "Người có công",
    "NKT": "Người khuyết tật", "KT": "Người khuyết tật", "NGUOI KHUYET TAT": "Người khuyết tật",
    "KHUYET TAT": "Người khuyết tật",
    "HO NGHEO": "Hộ nghèo", "NGHEO": "Hộ nghèo", "HN": "Hộ nghèo",
    "HO CAN NGHEO": "Hộ cận nghèo", "CAN NGHEO": "Hộ cận nghèo", "HCN": "Hộ cận nghèo",
    "DTTS": "Dân tộc thiểu số/hải đảo", "DAN TOC THIEU SO": "Dân tộc thiểu số/hải đảo",
    "DAN TOC THIEU SO/HAI DAO": "Dân tộc thiểu số/hải đảo",
    "TRE EM DUOI 6 TUOI": "Trẻ em dưới 6 tuổi", "TRE DUOI 6 TUOI": "Trẻ em dưới 6 tuổi",
    "KHAC": "Khác",
}


def parse_doi_tuong(text):
    """'NCT', 'Hộ Nghèo', 'NCT, NKT' ... -> danh sách tên nhóm chuẩn (giữ nguyên nếu không nhận ra)."""
    if not has_value(text):
        return []
    whole = key_text(text)
    if whole in _DT_ALIAS:
        return [_DT_ALIAS[whole]]
    out = []
    for part in re.split(r"[,;+]", str(text)):
        if has_value(part):
            lb = _DT_ALIAS.get(key_text(part), nfc(part))
            if lb not in out:
                out.append(lb)
    return out


def _sort_groups(labels):
    return sorted(labels, key=lambda x: (GROUP_ORDER.index(x) if x in GROUP_ORDER else len(GROUP_ORDER), x))


def _find_header(rows, keys, limit=15):
    for i, r in enumerate(rows[:limit]):
        if r and any(key_text(c) in keys for c in r if c is not None):
            return i
    return None


def _list_columns(header):
    h = [key_text(c) for c in header]
    cols = {"name": None, "phieu": None, "birth": None, "groups": [], "doituong": None}
    for i, x in enumerate(h):
        if x in ("HO VA TEN", "HO TEN") and cols["name"] is None:
            cols["name"] = i
        elif x.startswith("SO PHIEU") and cols["phieu"] is None:
            cols["phieu"] = i
        elif "SINH" in x and cols["birth"] is None:
            cols["birth"] = i
        elif "(NHAP 1" in x or x == "KHAC":
            cols["groups"].append((i, _group_label(header[i])))
        elif x == "DOI TUONG":
            cols["doituong"] = i
    return cols


class DanhSach:
    """Đọc một hoặc nhiều file danh sách khám (nhiều sheet, cột có thể lệch giữa các sheet).
    Đối tượng lấy từ các cột nhóm nhập 1/0; nếu sheet không có các cột này thì lấy từ cột 'Đối tượng' có sẵn."""

    def __init__(self, paths):
        if isinstance(paths, (str, Path)):
            paths = [paths]
        self.paths = [Path(p) for p in paths]
        self.persons = []
        self.sheets = []  # (file, tên sheet, số người, header_row_index, cols)
        labels = set()
        for path in self.paths:
            self._read_file(path, labels)
        if not self.persons:
            raise ValueError("Không tìm thấy dữ liệu: cần sheet có cột 'Họ và tên' và các cột đối tượng "
                             "(nhập 1/0) hoặc cột 'Đối tượng'.")
        self.group_labels = _sort_groups(labels)
        self._build_index()

    def _read_file(self, path, labels):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            hi = _find_header(rows, ("HO VA TEN", "HO TEN"))
            if hi is None:
                continue
            cols = _list_columns(rows[hi])
            if cols["name"] is None or not (cols["groups"] or cols["doituong"] is not None):
                continue
            labels.update(lb for _, lb in cols["groups"])
            n = 0
            for ri, r in enumerate(rows[hi + 1:], start=hi + 2):
                r = list(r) + [None] * (len(rows[hi]) - len(r))
                if not has_value(r[cols["name"]]):
                    continue
                n += 1
                if cols["groups"]:
                    groups = [lb for c, lb in cols["groups"] if is_one(r[c])]
                else:
                    groups = parse_doi_tuong(r[cols["doituong"]])
                    labels.update(groups)
                self.persons.append(Person(
                    file=path.name, sheet=ws.title, row=ri, name=nfc(r[cols["name"]]),
                    phieu=parse_int(r[cols["phieu"]]) if cols["phieu"] is not None else None,
                    year=parse_year(r[cols["birth"]]) if cols["birth"] is not None else None,
                    groups=groups,
                ))
            self.sheets.append((path, ws.title, n, hi, cols))
        wb.close()

    def _build_index(self):
        self.idx_full, self.idx_np, self.idx_ny = {}, {}, {}
        for p in self.persons:
            n = key_text(p.name)
            self.idx_full.setdefault((n, p.phieu, p.year), []).append(p)
            self.idx_np.setdefault((n, p.phieu), []).append(p)
            self.idx_ny.setdefault((n, p.year), []).append(p)

    def match(self, name, phieu, year):
        """Trả về (Person|None, mức ghép). Ưu tiên khớp đủ họ tên + số phiếu + năm sinh."""
        n = key_text(name)
        for idx, key, level in (
            (self.idx_full, (n, phieu, year), "Khớp đủ"),
            (self.idx_np, (n, phieu), "Lệch năm sinh"),
            (self.idx_ny, (n, year), "Lệch số phiếu"),
        ):
            if None in key[1:]:
                continue
            found = idx.get(key)
            if found and len({tuple(p.groups) for p in found}) == 1:
                if level == "Lệch số phiếu" and found[0].phieu is None:
                    level = LEVEL_NY  # danh sách không có số phiếu: ghép theo họ tên + năm sinh là đủ
                return found[0], level
        return None, "Không tìm thấy"

    def save_with_doi_tuong(self, out_dir, header_text="Đối tượng"):
        """Thêm cột Đối tượng vào cuối mỗi sheet có các cột nhóm (nhập 1/0), giữ nguyên định dạng gốc.
        File chỉ có cột 'Đối tượng' sẵn thì không cần ghi lại. Trả về {file kết quả: {sheet: số người}}."""
        result = {}
        for path in self.paths:
            sheets = [s for s in self.sheets if s[0] == path and s[4]["groups"]]
            if sheets:
                out = Path(out_dir) / f"{path.stem} - DOI TUONG.xlsx"
                result[out] = self._save_file(path, sheets, out, header_text)
        return result

    def _save_file(self, path, sheets, out_path, header_text):
        wb = openpyxl.load_workbook(path)
        by_sheet = {}
        for p in self.persons:
            if p.file == path.name:
                by_sheet.setdefault(p.sheet, []).append(p)
        stats = {}
        for _, title, _, hi, cols in sheets:
            ws = wb[title]
            hrow = hi + 1
            col = cols["doituong"] + 1 if cols["doituong"] is not None else None
            if col is None:
                last = max(c.column for c in ws[hrow] if has_value(c.value))
                col = last + 1
            href = ws.cell(hrow, cols["name"] + 1)
            hc = ws.cell(hrow, col, header_text)
            hc.font, hc.border, hc.fill = copy(href.font), copy(href.border), copy(href.fill)
            hc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 32
            cnt = 0
            for p in by_sheet.get(title, []):
                ref = ws.cell(p.row, cols["name"] + 1)
                c = ws.cell(p.row, col, p.doi_tuong or None)
                c.font, c.border = copy(ref.font), copy(ref.border)
                c.alignment = Alignment(vertical="center", wrap_text=True)
                cnt += bool(p.groups)
            stats[title] = cnt
        wb.save(out_path)
        return stats


# ---------------------------------------------------------------- xét nghiệm

TEST_ORDER = [
    "Tổng phân tích tế bào máu",
    "Tổng phân tích nước tiểu",
    "SGOT",
    "SGPT",
    "Urê",
    "Creatinin",
    "Glucose",
]
_SINGLE = {"SGPT": "SGPT", "SGOT": "SGOT", "CREATININ": "Creatinin", "GLUCOSE": "Glucose", "URE": "Urê"}
_URINE = {"ASC", "BIL", "BLD", "LEU", "NIT", "PRO", "SG", "URO", "PH", "GLU", "KET"}


def test_of_column(header):
    k = key_text(header).replace("*", "").strip()
    if k in _SINGLE:
        return _SINGLE[k]
    if k.split(" ")[0] in _URINE:
        return "Tổng phân tích nước tiểu"
    return "Tổng phân tích tế bào máu"


def _read_sheet_values(path):
    """Đọc sheet đầu tiên thành list các dòng (giá trị thô); hỗ trợ .xls và .xlsx."""
    path = Path(path)
    if path.suffix.lower() == ".xls":
        import xlrd
        book = xlrd.open_workbook(str(path))
        sh = book.sheet_by_index(0)
        rows = []
        for i in range(sh.nrows):
            vals = []
            for j, c in enumerate(sh.row(i)):
                v = c.value
                if c.ctype == xlrd.XL_CELL_DATE:
                    v = xlrd.xldate_as_datetime(v, book.datemode)
                vals.append(v)
            rows.append(vals)
        return rows, sh.name
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    name = ws.title
    wb.close()
    return rows, name


def _parse_range(rows):
    for r in rows[:5]:
        for c in r:
            m = re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(c or ""))
            if len(m) >= 2 and "NGAY" in key_text(c):
                a, b = [dt.date(int(y), int(mo), int(d)) for d, mo, y in m[:2]]
                return a, b
    return None


def _parse_sample_date(v, rng, swapped):
    """Ngày lấy mẫu có thể là chuỗi 'dd/mm/yyyy hh:mm' hoặc ngày Excel đã bị đảo ngày/tháng
    (Excel hiểu chuỗi 09/08 thành ngày 8/9, còn 13/08 thì giữ nguyên chuỗi).
    swapped=True khi cột có lẫn chuỗi dd/mm — dấu hiệu các ô dạng ngày đã bị đảo."""
    if isinstance(v, dt.datetime):
        d = v.date()
    elif isinstance(v, dt.date):
        d = v
    elif isinstance(v, (int, float)) and v > 3000:
        d = (dt.datetime(1899, 12, 30) + dt.timedelta(days=float(v))).date()
    else:
        m = re.match(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})", str(v or ""))
        return dt.date(int(m[3]), int(m[2]), int(m[1])) if m else None
    if swapped and d.day <= 12:
        sw = dt.date(d.year, d.day, d.month)
        if not rng or rng[0] <= sw <= rng[1] or not (rng[0] <= d <= rng[1]):
            return sw
    return d


@dataclass
class XNRow:
    row: int  # chỉ số dòng 0-based trong sheet
    date: dt.date
    phieu: int
    name: str
    year: int
    tests: set
    person: Person = None
    level: str = ""


class KetQuaXN:
    def __init__(self, path):
        self.path = Path(path)
        rows, self.sheet_name = _read_sheet_values(path)
        self.title_rows = rows[:3]
        self.date_range = _parse_range(rows)
        hi = _find_header(rows, ("HO TEN", "HO VA TEN"))
        if hi is None:
            raise ValueError("File xét nghiệm: không tìm thấy dòng tiêu đề có 'Họ tên'.")
        head = [key_text(c) for c in rows[hi]]
        sub = rows[hi + 1] if hi + 1 < len(rows) else []
        c_name_head = next(i for i, x in enumerate(head) if x in ("HO TEN", "HO VA TEN"))
        self.c_birth = next((i for i, x in enumerate(head) if x == "NAM SINH"), None)
        self.c_date = next((i for i, x in enumerate(head) if x.startswith("NGAY")), None)
        c_kq = next((i for i, x in enumerate(head) if x == "KET QUA"), None)

        data_start = hi + 2 if any(has_value(c) for c in sub) else hi + 1
        sample = [r for r in rows[data_start:data_start + 30] if len(r) > c_name_head + 1]
        # Bố cục thường gặp: ô 'Họ tên' gộp E:G — E là số phiếu, F là họ tên, G trống (đối tượng)
        num_e = sum(isinstance(r[c_name_head], (int, float)) for r in sample)
        if num_e > len(sample) / 2:
            self.c_phieu, self.c_name = c_name_head, c_name_head + 1
        else:
            self.c_name = c_name_head
            self.c_phieu = next((i for i, x in enumerate(head) if x.startswith("SO PHIEU") or x == "STT"), None)
        self.c_dt = self.c_name + 1
        self.header_row = hi
        self.dt_header_row = hi + 1 if data_start == hi + 2 else hi

        self.test_cols = []
        if c_kq is not None:
            for j in range(c_kq, len(sub)):
                if has_value(sub[j]):
                    self.test_cols.append((j, test_of_column(sub[j])))

        date_re = re.compile(r"\s*\d{1,2}/\d{1,2}/\d{4}")
        swapped = self.c_date is not None and any(
            isinstance(r[self.c_date], str) and date_re.match(r[self.c_date])
            for r in rows[data_start:] if len(r) > self.c_date)
        self.rows = []
        for i in range(data_start, len(rows)):
            r = rows[i]
            if len(r) <= self.c_name or not has_value(r[self.c_name]):
                continue
            tests = {t for j, t in self.test_cols if j < len(r) and has_value(r[j])}
            self.rows.append(XNRow(
                row=i,
                date=_parse_sample_date(r[self.c_date], self.date_range, swapped) if self.c_date is not None else None,
                phieu=parse_int(r[self.c_phieu]) if self.c_phieu is not None else None,
                name=nfc(r[self.c_name]),
                year=parse_year(r[self.c_birth]) if self.c_birth is not None else None,
                tests=tests,
            ))

    def match(self, ds: DanhSach):
        for x in self.rows:
            x.person, x.level = ds.match(x.name, x.phieu, x.year)
        cnt = OrderedDict((k, 0) for k in LEVELS)
        for x in self.rows:
            cnt[x.level] += 1
        return cnt

    def save_with_doi_tuong(self, out_path):
        out_path = Path(out_path)
        if self.path.suffix.lower() == ".xls":
            self._save_xls(out_path)
        else:
            self._save_xlsx(out_path)

    def _review_rows(self):
        for x in self.rows:
            if x.level not in GOOD_LEVELS:
                p = x.person
                yield [x.row + 1, fmt_date(x.date), x.phieu, x.name, x.year, x.level,
                       p.doi_tuong if p else "",
                       f"DS: phiếu {p.phieu}, năm sinh {p.year}, {p.file} / {p.sheet} dòng {p.row}" if p else ""]

    REVIEW_HEAD = ["Dòng", "Ngày lấy mẫu", "Số phiếu", "Họ tên", "Năm sinh", "Mức ghép", "Đối tượng", "Thông tin trong danh sách"]

    def _save_xls(self, out_path):
        import xlrd
        import xlwt
        from xlutils.copy import copy as xl_copy
        rb = xlrd.open_workbook(str(self.path), formatting_info=True)
        wb = xl_copy(rb)
        ws = wb.get_sheet(0)
        base = "font: name Times New Roman, height 220; borders: left thin, right thin, top thin, bottom thin; align: vert centre, wrap on;"
        st_ok = xlwt.easyxf(base)
        st_warn = xlwt.easyxf(base + "pattern: pattern solid, fore_colour light_yellow;")
        st_miss = xlwt.easyxf(base + "pattern: pattern solid, fore_colour rose;")
        st_head = xlwt.easyxf(base.replace("height 220", "height 220, bold on") + "align: horiz centre;")
        ws.write(self.dt_header_row, self.c_dt, "Đối tượng", st_head)
        ws.col(self.c_dt).width = 256 * 30
        for x in self.rows:
            if x.person is None:
                ws.write(x.row, self.c_dt, "Không tìm thấy trong DS", st_miss)
            else:
                ws.write(x.row, self.c_dt, x.person.doi_tuong, st_ok if x.level in GOOD_LEVELS else st_warn)
        rv = wb.add_sheet("Kiem tra ghep")
        for j, h in enumerate(self.REVIEW_HEAD):
            rv.write(0, j, h, st_head)
            rv.col(j).width = 256 * (40 if j == 7 else 25 if j in (3, 6) else 13)
        for i, vals in enumerate(self._review_rows(), start=1):
            for j, v in enumerate(vals):
                rv.write(i, j, "" if v is None else v, st_miss if vals[5] == "Không tìm thấy" else st_warn)
        wb.save(str(out_path))

    def _save_xlsx(self, out_path):
        wb = openpyxl.load_workbook(self.path)
        ws = wb.worksheets[0]
        warn = PatternFill("solid", fgColor="FFF2CC")
        miss = PatternFill("solid", fgColor="F8CBAD")
        thin = Side(style="thin")
        bd = Border(left=thin, right=thin, top=thin, bottom=thin)
        h = ws.cell(self.dt_header_row + 1, self.c_dt + 1, "Đối tượng")
        h.font, h.border = Font(bold=True), bd
        for x in self.rows:
            c = ws.cell(x.row + 1, self.c_dt + 1)
            c.value = x.person.doi_tuong if x.person else "Không tìm thấy trong DS"
            c.border = bd
            if x.level not in GOOD_LEVELS:
                c.fill = miss if x.person is None else warn
        rv = wb.create_sheet("Kiem tra ghep")
        rv.append(self.REVIEW_HEAD)
        for vals in self._review_rows():
            rv.append(vals)
        wb.save(out_path)


# ---------------------------------------------------------------- tổng hợp

COL_NONE = "Không thuộc đối tượng"
COL_UNKNOWN = "Chưa xác định (không có trong DS)"
COL_TOTAL = "Tổng số người"


@dataclass
class Report:
    columns: list  # tên các cột đối tượng (kể cả 2 cột phụ)
    table: "OrderedDict[str, OrderedDict[str, int]]"  # tên XN -> {cột: số người}
    total_people: "OrderedDict[str, int]"  # số người làm XN theo đối tượng
    details: list  # [ngày, số phiếu, họ tên, năm sinh, đối tượng, các xét nghiệm]
    date_from: dt.date
    date_to: dt.date


def build_report(xn: KetQuaXN, ds: DanhSach, date_from=None, date_to=None):
    """Đếm số NGƯỜI (không đếm số mẫu) theo từng xét nghiệm và đối tượng.
    Một người thuộc nhiều đối tượng được tính ở mỗi cột đối tượng tương ứng;
    cột 'Tổng số người' đếm mỗi người một lần."""
    people = OrderedDict()
    for x in xn.rows:
        if date_from and x.date and x.date < date_from:
            continue
        if date_to and x.date and x.date > date_to:
            continue
        key = (key_text(x.name), x.phieu, x.year)
        p = people.setdefault(key, {"x": x, "tests": set(), "dates": set()})
        p["tests"] |= x.tests
        if x.date:
            p["dates"].add(x.date)
        if p["x"].person is None and x.person is not None:
            p["x"] = x

    columns = list(ds.group_labels) + [COL_NONE, COL_UNKNOWN]
    tests = [t for t in TEST_ORDER] + sorted({t for p in people.values() for t in p["tests"]} - set(TEST_ORDER))
    table = OrderedDict((t, OrderedDict((c, 0) for c in columns + [COL_TOTAL])) for t in tests)
    total = OrderedDict((c, 0) for c in columns + [COL_TOTAL])
    details = []
    for p in people.values():
        x = p["x"]
        if x.person is None:
            cats = [COL_UNKNOWN]
        else:
            cats = x.person.groups or [COL_NONE]
        if not p["tests"]:
            continue
        for c in cats:
            total[c] += 1
        total[COL_TOTAL] += 1
        for t in p["tests"]:
            for c in cats:
                table[t][c] += 1
            table[t][COL_TOTAL] += 1
        details.append([
            ", ".join(fmt_date(d) for d in sorted(p["dates"])), x.phieu, x.name, x.year,
            x.person.doi_tuong if x.person else COL_UNKNOWN, x.level,
            ", ".join(t for t in tests if t in p["tests"]),
        ])
    dates = [d for p in people.values() for d in p["dates"]]
    return Report(columns, table, total, details,
                  date_from or (min(dates) if dates else None),
                  date_to or (max(dates) if dates else None))
