@echo off
chcp 65001 >nul
echo ================================================
echo   BUILD GOOGLE MAPS REVIEW BOT - EXE
echo ================================================
echo.

echo [1/3] Kiem tra PyInstaller...
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo Dang cai PyInstaller...
    pip install pyinstaller
)

echo [2/3] Dang build EXE...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "GoogleMapsReviewBot" ^
    --icon=NONE ^
    --add-data "config.json;." ^
    --hidden-import=review_bot ^
    --hidden-import=webdriver_manager ^
    --hidden-import=webdriver_manager.chrome ^
    --hidden-import=selenium ^
    --hidden-import=selenium.webdriver ^
    --hidden-import=selenium.webdriver.chrome ^
    --hidden-import=selenium.webdriver.chrome.service ^
    --hidden-import=selenium.webdriver.chrome.options ^
    --hidden-import=qrcode ^
    --hidden-import=qrcode.image ^
    --hidden-import=qrcode.image.pil ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --collect-all webdriver_manager ^
    --collect-all selenium ^
    --collect-all qrcode ^
    --collect-all PIL ^
    main.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo   BUILD THAT BAI!
    echo ================================================
    pause
    exit /b 1
)

echo.
echo [3/3] Tao thu muc output...
if not exist "dist" mkdir dist
copy /y config.json dist\config.json >nul 2>&1
if not exist "dist\images" mkdir dist\images
if not exist "dist\profiles" mkdir dist\profiles

echo.
echo ================================================
echo   BUILD THANH CONG!
echo ================================================
echo.
echo   File EXE: dist\GoogleMapsReviewBot.exe
echo.
echo   Huong dan su dung:
echo   1. Copy file EXE vao thu muc moi
echo   2. Tao folder "images" cung thu muc (de anh)
echo   3. Chay EXE
echo   4. Nhap thong tin va bat dau danh gia
echo.
echo   Profile da dang nhap se duoc luu trong
echo   folder "profiles" (khong can dang nhap lai)
echo.
pause
