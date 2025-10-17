@echo off
REM Windows Build Script for COINjecture

echo 🪟 Building COINjecture for Windows...

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not found
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check for PyInstaller
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Create directories
echo 📁 Creating directories...
if not exist "%PROJECT_ROOT%\dist\packages" mkdir "%PROJECT_ROOT%\dist\packages"
if not exist "%PROJECT_ROOT%\packaging\assets" mkdir "%PROJECT_ROOT%\packaging\assets"

REM Create Windows icon (placeholder)
echo 🎨 Creating app icon...
echo # Placeholder for Windows app icon > "%PROJECT_ROOT%\packaging\assets\icon.ico"
echo # In production, this would be a proper .ico file >> "%PROJECT_ROOT%\packaging\assets\icon.ico"

REM Create version info
echo 📝 Creating version info...
(
echo # UTF-8
echo #
echo # For more details about fixed file info 'ffi' see:
echo # http://msdn.microsoft.com/en-us/library/ms646997.aspx
echo VSVersionInfo^(
echo   ffi=FixedFileInfo^(
echo     filevers=^(3,6,0,0^),
echo     prodvers=^(3,6,0,0^),
echo     mask=0x3f,
echo     flags=0x0,
echo     OS=0x4,
echo     fileType=0x1,
echo     subtype=0x0,
echo     date=^(0, 0^)
echo     ^),
echo   kids=[
echo     StringFileInfo^(
echo       [
echo       StringTable^(
echo         u'040904B0',
echo         [StringStruct^(u'CompanyName', u'COINjecture'^),
echo         StringStruct^(u'FileDescription', u'COINjecture - Proof-of-Work Blockchain'^),
echo         StringStruct^(u'FileVersion', u'3.6.0'^),
echo         StringStruct^(u'InternalName', u'COINjecture'^),
echo         StringStruct^(u'LegalCopyright', u'Copyright ^(C^) 2025 COINjecture'^),
echo         StringStruct^(u'OriginalFilename', u'COINjecture.exe'^),
echo         StringStruct^(u'ProductName', u'COINjecture'^),
echo         StringStruct^(u'ProductVersion', u'3.6.0'^)])
echo       ]^), 
echo     VarFileInfo^([VarStruct^(u'Translation', [1033, 1200]^)])
echo   ]
echo ^)
) > "%PROJECT_ROOT%\packaging\assets\version_info.txt"

REM Build the executable
echo 🔨 Building executable...
cd /d "%PROJECT_ROOT%"

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist\COINjecture" rmdir /s /q "dist\COINjecture"

REM Run PyInstaller
pyinstaller packaging\coinjecture.spec
if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

REM Check if build was successful
if not exist "dist\COINjecture\COINjecture.exe" (
    echo ❌ Build failed - executable not found
    pause
    exit /b 1
)

REM Copy executable to packages directory
echo 📦 Creating Windows package...
set EXE_NAME=COINjecture-3.6.0-Windows.exe
set EXE_PATH=dist\packages\%EXE_NAME%

copy "dist\COINjecture\COINjecture.exe" "%EXE_PATH%"
if errorlevel 1 (
    echo ❌ Failed to copy executable
    pause
    exit /b 1
)

echo ✅ Windows executable created: %EXE_PATH%

REM Create installer using NSIS (if available)
echo 💿 Creating Windows installer...
where makensis >nul 2>&1
if not errorlevel 1 (
    echo 📝 Creating NSIS installer script...
    
    (
    echo !define APPNAME "COINjecture"
    echo !define COMPANYNAME "COINjecture"
    echo !define DESCRIPTION "Proof-of-Work Blockchain"
    echo !define VERSIONMAJOR 3
    echo !define VERSIONMINOR 6
    echo !define VERSIONBUILD 0
    echo !define HELPURL "https://github.com/beanapologist/COINjecture"
    echo !define UPDATEURL "https://github.com/beanapologist/COINjecture"
    echo !define ABOUTURL "https://github.com/beanapologist/COINjecture"
    echo !define INSTALLSIZE 100000
    echo.
    echo RequestExecutionLevel admin
    echo InstallDir "$PROGRAMFILES\${APPNAME}"
    echo Name "${COMPANYNAME} - ${APPNAME}"
    echo outFile "dist\packages\COINjecture-3.6.0-Windows-Installer.exe"
    echo icon "packaging\assets\icon.ico"
    echo installDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" ""
    echo page directory
    echo page instfiles
    echo.
    echo section "install"
    echo     setOutPath $INSTDIR
    echo     file "%EXE_PATH%"
    echo     writeUninstaller "$INSTDIR\uninstall.exe"
    echo     createDirectory "$SMPROGRAMS\${COMPANYNAME}"
    echo     createShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\%EXE_NAME%" "" "$INSTDIR\%EXE_NAME%"
    echo     createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\%EXE_NAME%" "" "$INSTDIR\%EXE_NAME%"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${COMPANYNAME} - ${APPNAME} - ${DESCRIPTION}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\%EXE_NAME%$\""
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "${HELPURL}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    echo sectionEnd
    echo.
    echo section "uninstall"
    echo     delete "$INSTDIR\%EXE_NAME%"
    echo     delete "$INSTDIR\uninstall.exe"
    echo     rmDir $INSTDIR
    echo     delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    echo     rmDir "$SMPROGRAMS\${COMPANYNAME}"
    echo     delete "$DESKTOP\${APPNAME}.lnk"
    echo     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
    echo     DeleteRegKey /ifempty HKLM "Software\${COMPANYNAME}"
    echo sectionEnd
    ) > "packaging\installers\windows_installer.nsi"
    
    REM Create installer
    makensis "packaging\installers\windows_installer.nsi"
    if not errorlevel 1 (
        echo ✅ Windows installer created successfully
    ) else (
        echo ⚠️ Failed to create installer, but executable is ready
    )
) else (
    echo ⚠️ NSIS not found, skipping installer creation
    echo 💡 Install NSIS from https://nsis.sourceforge.io/ to create installers
)

REM Code signing (optional)
echo 🔐 Code signing...
where signtool >nul 2>&1
if not errorlevel 1 (
    if defined COINJECTURE_CERT_FILE (
        echo    Signing with certificate: %COINJECTURE_CERT_FILE%
        signtool sign /f "%COINJECTURE_CERT_FILE%" /p "%COINJECTURE_CERT_PASSWORD%" /tr "http://timestamp.digicert.com" /td sha256 "%EXE_PATH%"
        if not errorlevel 1 (
            echo ✅ Code signing completed
        ) else (
            echo ⚠️ Code signing failed
        )
    ) else (
        echo ⚠️ COINJECTURE_CERT_FILE not set, skipping code signing
    )
) else (
    echo ⚠️ signtool not found, skipping code signing
)

REM Show file size
for %%A in ("%EXE_PATH%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576
echo 📊 Executable size: %SIZE_MB% MB

echo.
echo 🎉 Windows build complete!
echo 📁 Output: %EXE_PATH%
echo.
echo 🚀 To test:
echo    1. Double-click the executable to run
echo    2. Or run from command prompt: %EXE_NAME%
echo.
pause
