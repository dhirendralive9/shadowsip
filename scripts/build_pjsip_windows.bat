@echo off
REM ============================================
REM ShadowSIP — Build PJSIP + pjsua2 Python bindings (Windows)
REM Prerequisites:
REM   - Visual Studio 2022 Build Tools (C++ workload)
REM   - Python 3.10+ (python.org installer, NOT Windows Store)
REM   - SWIG (choco install swig OR manual from swig.org)
REM   - NASM (choco install nasm — for video codecs)
REM   - Git
REM Run from VS Developer Command Prompt:
REM   scripts\build_pjsip_windows.bat
REM ============================================

setlocal enabledelayedexpansion

set PJSIP_VERSION=2.14.1
set BUILD_DIR=%CD%\build\pjsip
set PJSIP_DIR=%BUILD_DIR%\pjproject-%PJSIP_VERSION%

echo ============================================
echo  ShadowSIP — PJSIP Build Script (Windows)
echo  PJSIP Version: %PJSIP_VERSION%
echo  Python: 
python --version
echo ============================================
echo.

REM Step 1: Check prerequisites
echo [1/6] Checking prerequisites...
where cl >nul 2>&1 || (
    echo ERROR: Visual Studio C++ compiler not found.
    echo Run this script from "x64 Native Tools Command Prompt for VS 2022"
    exit /b 1
)
where swig >nul 2>&1 || (
    echo ERROR: SWIG not found. Install: choco install swig
    exit /b 1
)
where python >nul 2>&1 || (
    echo ERROR: Python not found in PATH.
    exit /b 1
)
echo   cl.exe: OK
echo   swig: OK
echo   python: OK

REM Step 2: Clone/download PJSIP
echo.
echo [2/6] Getting PJSIP source...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

if not exist "%PJSIP_DIR%" (
    cd "%BUILD_DIR%"
    git clone --depth 1 --branch %PJSIP_VERSION% https://github.com/pjsip/pjproject.git pjproject-%PJSIP_VERSION%
)
cd "%PJSIP_DIR%"

REM Step 3: Configure
echo.
echo [3/6] Configuring PJSIP...

(
echo /*
echo  * ShadowSIP — PJSIP build configuration (Windows)
echo  */
echo #define PJMEDIA_HAS_VIDEO               1
echo #define PJMEDIA_HAS_SRTP                1
echo #define PJ_HAS_SSL_SOCK                 1
echo #define PJMEDIA_HAS_OPUS_CODEC          1
echo #define PJSUA_MAX_ACC                   8
echo #define PJSUA_MAX_CALLS                 16
echo #define PJSUA_MAX_PLAYERS               16
echo #define PJ_ICE_MAX_CAND                 32
echo #define PJ_ICE_MAX_CHECKS               100
) > pjlib\include\pj\config_site.h

REM Step 4: Build with Visual Studio
echo.
echo [4/6] Building PJSIP with MSBuild...

REM Find the VS solution
if exist pjproject-vs17.sln (
    set SOLUTION=pjproject-vs17.sln
) else if exist pjproject-vs16.sln (
    set SOLUTION=pjproject-vs16.sln
) else (
    echo ERROR: No Visual Studio solution found.
    exit /b 1
)

msbuild %SOLUTION% /p:Configuration=Release /p:Platform=x64 /m /v:minimal
if errorlevel 1 (
    echo ERROR: PJSIP build failed.
    exit /b 1
)

REM Step 5: Build SWIG Python bindings
echo.
echo [5/6] Building pjsua2 Python bindings...
cd pjsip-apps\src\swig

REM Generate wrapper
swig -python -c++ -I../../../pjlib/include -I../../../pjlib-util/include -I../../../pjmedia/include -I../../../pjsip/include -I../../../pjnath/include -o python/pjsua2_wrap.cpp python/pjsua2.i

cd python
python setup.py build_ext --inplace
if errorlevel 1 (
    echo ERROR: pjsua2 Python build failed.
    exit /b 1
)

REM Step 6: Install
echo.
echo [6/6] Installing pjsua2 module...
python setup.py install

echo.
echo ============================================
echo  BUILD COMPLETE
echo ============================================
echo.
echo Verify: python -c "import pjsua2; print('OK')"
echo.

python -c "import pjsua2; print('pjsua2 installed successfully!')" 2>nul || (
    echo WARNING: pjsua2 import failed. Check build output.
)

endlocal
