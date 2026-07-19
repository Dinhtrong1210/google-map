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
    --icon=icon.ico ^
    --add-data "config.json;." ^
    --hidden-import=review_bot ^
    --hidden-import=webdriver_manager ^
    --hidden-import=webdriver_manager.chrome ^
    --hidden-import=selenium ^
    --hidden-import=selenium.webdriver ^
    --hidden-import=selenium.webdriver.chrome ^
    --hidden-import=selenium.webdriver.chrome.service ^
    --hidden-import=selenium.webdriver.chrome.options ^
    --collect-all webdriver_manager ^
    --collect-all selenium ^
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
echo   BUILD EXE THANH CONG!
echo ================================================
echo.
echo   File EXE: dist\GoogleMapsReviewBot.exe
echo.

echo [3/3] Dang tao installer (setup.exe co hoi tao icon Desktop)...
set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    %ISCC% installer.iss
    echo.
    echo   Installer: installer_output\GoogleMapsReviewBot_Setup.exe
) else (
    echo   Khong tim thay Inno Setup, bo qua buoc tao installer.
    echo   Cai Inno Setup ^(winget install JRSoftware.InnoSetup^) roi chay lai de co setup.exe.
)

echo.
echo ================================================
echo   XONG!
echo ================================================
echo.
echo   Dua cho nguoi dung: installer_output\GoogleMapsReviewBot_Setup.exe
echo   ^(cai nhu app binh thuong, co hoi tao icon Desktop, tu tao Start Menu^)
echo.
pause
