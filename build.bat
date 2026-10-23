@echo off
rem Build file XuLyKhamSK.exe (chay duoc tren may khong cai Python) vao thu muc dist
cd /d "%~dp0"
python -m pip install -q -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name XuLyKhamSK --workpath build --specpath build --distpath dist --collect-data docx --exclude-module numpy --exclude-module pandas --exclude-module PIL --exclude-module matplotlib --exclude-module scipy app.py
echo.
echo Xong: dist\XuLyKhamSK.exe
pause
