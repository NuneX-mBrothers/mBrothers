@echo off
setlocal

rem ====================================================================
rem   mBrothers  --  Publish SITE
rem ====================================================================
rem   Publica o site principal (esta pasta E o repo publico) no GitHub
rem   Pages.
rem
rem   Ao contrario do ExplorerFocus e do LogViewer, aqui NAO ha build nem
rem   injeccao de versao: o que esta escrito nos ficheiros e o que vai
rem   para o ar. A versao mostrada no site (ex.: v10.12) e escrita a mao
rem   no index.html - este script nao lhe toca.
rem
rem   O GitHub Pages demora cerca de 1 minuto a propagar.
rem ====================================================================

set "SITE_DIR=%~dp0"
set "URL=https://nunex-mbrothers.github.io/mBrothers/"

echo.
echo ==========================================
echo   mBrothers  --  Publish SITE
echo ==========================================
echo.

cd /d "%SITE_DIR%"

rem -- 1. Confirmar que estamos no repo certo --------------------------
echo [1/4] A validar o repositorio...
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Esta pasta nao e um repositorio git.
    pause
    exit /b 1
)
set "REMOTE="
for /f "tokens=*" %%r in ('git remote get-url origin 2^>nul') do set "REMOTE=%%r"
echo       %REMOTE%
echo %REMOTE% | findstr /i "mBrothers" >nul
if errorlevel 1 (
    echo [ERRO] O remote nao parece ser o do mBrothers. Abortado por seguranca.
    pause
    exit /b 1
)
echo       OK

rem -- 2. Mostrar o que vai ser publicado ------------------------------
echo.
echo [2/4] Alteracoes por publicar:
git status --short
echo.

set "NCH=0"
for /f %%c in ('git status --porcelain ^| find /c /v ""') do set "NCH=%%c"
if "%NCH%"=="0" goto :nada

set "MSG="
set /p "MSG=      Mensagem do commit (Enter = Site: atualizacao): "
if not defined MSG set "MSG=Site: atualizacao"

rem -- 3. Adicionar e commitar ----------------------------------------
echo.
echo [3/4] git add + commit...
git add -A
if errorlevel 1 (
    echo [ERRO] git add falhou.
    pause
    exit /b 1
)
echo.
echo       --- staged ---
git diff --cached --name-only
echo       --------------
echo.
git commit -m "%MSG%"
if errorlevel 1 echo       [AVISO] Nada para commit.
goto :push

:nada
echo       Nada para publicar - o site ja esta sincronizado.
echo       A tentar push na mesma, caso haja commits por enviar.
echo.
echo [3/4] ^(sem commit^)

rem -- 4. Push --------------------------------------------------------
:push
echo.
echo [4/4] git push...
git push origin main
if errorlevel 1 (
    echo [ERRO] git push falhou. Verifica 'git status' e 'gh auth status'.
    pause
    exit /b 1
)
echo       OK

echo.
echo ==========================================
echo   Site publicado!
echo.
echo   Landing:  %URL%
echo   (GitHub Pages pode demorar cerca de 1 min)
echo.
echo   Sem build, sem Release, sem injeccao de versao.
echo ==========================================
echo.
pause
