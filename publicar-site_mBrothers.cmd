@echo off
setlocal EnableDelayedExpansion

:: ════════════════════════════════════════════════════════════════════
::  mBrothers  --  Publish SITE
:: ════════════════════════════════════════════════════════════════════
::  Publica o site principal (esta pasta E o repo publico) no GitHub
::  Pages. Ao contrario do ExplorerFocus e do LogViewer, aqui NAO ha
::  build nem injeccao de versao: o que esta escrito nos ficheiros e o
::  que vai para o ar.
::
::  A versao mostrada no site (ex.: "v10.12") e escrita A MAO no
::  index.html -- este script nao lhe toca.
::
::  O GitHub Pages demora ~1 min a propagar.
:: ════════════════════════════════════════════════════════════════════

set "SITE_DIR=%~dp0"
set "URL=https://nunex-mbrothers.github.io/mBrothers/"

echo.
echo ==========================================
echo   mBrothers  --  Publish SITE
echo ==========================================
echo.

cd /d "%SITE_DIR%"

:: -- 1. Confirmar que estamos no repo certo -------------------
echo [1/4] A validar o repositorio...
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Esta pasta nao e um repositorio git.
    pause & exit /b 1
)
for /f "tokens=*" %%r in ('git remote get-url origin 2^>nul') do set "REMOTE=%%r"
echo       %REMOTE%
echo %REMOTE% | findstr /i "mBrothers" >nul
if errorlevel 1 (
    echo [ERRO] O remote nao parece ser o do mBrothers. Abortado por seguranca.
    pause & exit /b 1
)
echo       OK

:: -- 2. Mostrar o que vai ser publicado -----------------------
echo.
echo [2/4] Alteracoes por publicar:
git status --short
if errorlevel 1 ( pause & exit /b 1 )
echo.
for /f %%c in ('git status --porcelain ^| find /c /v ""') do set "NCH=%%c"
if "%NCH%"=="0" (
    echo       Nada para publicar - o site ja esta sincronizado.
    echo       ^(A tentar push na mesma, caso haja commits por enviar.^)
    goto :push
)

set "MSG="
set /p MSG=      Mensagem do commit (Enter = "Site: atualizacao"):
if "!MSG!"=="" set "MSG=Site: atualizacao"

:: -- 3. Adicionar e commitar ---------------------------------
echo.
echo [3/4] git add + commit...
git add -A
if errorlevel 1 (
    echo [ERRO] git add falhou.
    pause & exit /b 1
)
echo.
echo       --- staged ---
git diff --cached --name-only
echo       --------------
echo.
git commit -m "!MSG!"
if errorlevel 1 echo       [AVISO] Nada para commit ^(pode ja estar commitado^).

:: -- 4. Push -------------------------------------------------
:push
echo.
echo [4/4] git push...
git push origin main
if errorlevel 1 (
    echo [ERRO] git push falhou. Verifica 'git status' e 'gh auth status'.
    pause & exit /b 1
)
echo       OK

echo.
echo ==========================================
echo   Site publicado!
echo.
echo   Landing:  %URL%
echo   (GitHub Pages pode demorar ~1 min)
echo.
echo   Sem build, sem Release, sem injeccao de versao.
echo ==========================================
echo.
pause
