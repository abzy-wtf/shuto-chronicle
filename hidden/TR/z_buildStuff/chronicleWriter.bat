@echo off
setlocal

set "PY_SCRIPT=P:\PROJECTS_ROOT\WIKI\TXR_Archive\scratch\build_chronicle_multilingual.py"
set "SRC_HTML=P:\PROJECTS_ROOT\WIKI\TXR_Archive\zextras\Shutoko Chronicle.html"
set "WEB_DIR=P:\PROJECTS_ROOT\WIKI\TXR_Archive\zz_00_WIKI\website"

python "%PY_SCRIPT%"
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

if not exist "%WEB_DIR%" mkdir "%WEB_DIR%"

copy /Y "%SRC_HTML%" "%WEB_DIR%\index.html" >nul
copy /Y "%SRC_HTML%" "%WEB_DIR%\Shutoko Chronicle.html" >nul

type nul > "%WEB_DIR%\.nojekyll"

(
echo pages:
echo   stage: deploy
echo   script:
echo     - mkdir -p .public
echo     - cp -r * .public
echo     - mv .public public
echo   artifacts:
echo     paths:
echo       - public
echo   rules:
echo     - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
) > "%WEB_DIR%\.gitlab-ci.yml"

endlocal