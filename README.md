# KhamSKBvVietHan

App xử lý danh sách khám sức khỏe (Python + tkinter).

## Chạy
Nhấp đúp `Chay app.bat` (tự cài thư viện trong `requirements.txt`), hoặc:

    pip install -r requirements.txt
    python app.py

## Chức năng
1. **Danh sách – thêm cột Đối tượng** (chọn được nhiều file; file đã có sẵn cột “Đối tượng” ghi tắt NCT/NKT/CC… chỉ được đọc để ghép): các cột nhóm (Người cao tuổi … Khác) có giá trị 1 được ghi vào cột mới
   “Đối tượng” ở cuối mỗi sheet → lưu `<tên file> - DOI TUONG.xlsx`.
2. **Kết quả XN – điền Đối tượng**: ghép theo Họ tên + Số phiếu + Năm sinh (dự phòng: Họ tên + Số phiếu,
   Họ tên + Năm sinh; danh sách không có số phiếu thì ghép theo Họ tên + Năm sinh), ghi vào cột G → lưu `<tên file> - DOI TUONG.xls`, kèm sheet “Kiem tra ghep”.
3. **Báo cáo tổng hợp**: số người làm từng xét nghiệm theo đối tượng, lọc theo ngày, xuất Excel / Word.

## File mã nguồn
- `core.py` – đọc dữ liệu, ghép, tổng hợp
- `report_export.py` – xuất báo cáo Excel / Word
- `app.py` – giao diện
