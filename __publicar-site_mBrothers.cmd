@echo off
setlocal enableextensions disabledelayedexpansion

rem ====================================================================
rem   mBrothers  --  Publish SITE
rem ====================================================================
rem   Desde 06/11/2026 o site vive no NOSSO servidor, em
rem   https://intrepidparallel.com/mbrothers/ (decisao de 06/11/2026). O GitHub
rem   fica so com as paginas que reencaminham para la (a pasta docs/, que o
rem   GitHub Pages serve) e com o codigo.
rem
rem   Este script:
rem     1. confere que esta no repositorio e no ramo certos;
rem     2. gera as 15 paginas por idioma e o sitemap.xml;
rem     3. gera as paginas de reencaminhar do GitHub (docs/);
rem     4. publica o site no servidor (a porta de publicacao da Cobleza);
rem     5. publica os ficheiros da raiz do dominio (robots.txt, favicon.ico,
rem        llms.txt, na pasta raiz/);
rem     6. faz o commit e o push para o GitHub;
rem     7. confere que o site responde.
rem
rem   Sem build e sem Release. A versao mostrada no site e escrita a mao.
rem
rem   A chave SSH de publicacao fica so no PC de quem publica, em
rem   %USERPROFILE%\.ssh\sites-publicar-intrepidparallel. No servidor ela so
rem   consegue publicar, voltar a versao anterior e listar as versoes:
rem     ssh -i <chave> sites@136.144.201.147 voltar mbrothers
rem     ssh -i <chave> sites@136.144.201.147 versoes mbrothers
rem
rem   O pacote faz-se com o tools\empacotar.py, e NAO com o tar do Windows:
rem   esse marcava as pastas como so de leitura (o OneDrive poe-lhes esse
rem   atributo) e o servidor nao conseguia escrever nelas (06/11/2026).
rem   O ssh vai pelo caminho inteiro. E corre-se no cmd, nao no PowerShell
rem   antigo, que estraga os bytes do pacote no "|".
rem ====================================================================

set "SITE_DIR=%~dp0"
set "URL=https://intrepidparallel.com/mbrothers/"
set "SERVIDOR=sites@136.144.201.147"
set "CHAVE=%USERPROFILE%\.ssh\sites-publicar-intrepidparallel"
set "SSH=%SystemRoot%\System32\OpenSSH\ssh.exe"
set "CURL=%SystemRoot%\System32\curl.exe"

echo.
echo ==========================================
echo   mBrothers  --  Publish SITE
echo ==========================================
echo.

cd /d "%SITE_DIR%"

rem -- 1. Repositorio, ramo e ferramentas -----------------------------
echo [1/7] A validar o repositorio...
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
set "RAMO="
for /f "tokens=*" %%b in ('git branch --show-current 2^>nul') do set "RAMO=%%b"
if /i not "%RAMO%"=="main" (
    echo [ERRO] O ramo actual e "%RAMO%", e so se publica do main. Abortado.
    pause
    exit /b 1
)
if not exist "%CHAVE%" (
    echo [ERRO] Nao encontro a chave de publicacao em %CHAVE%.
    pause
    exit /b 1
)
if not exist "%SSH%" (
    echo [ERRO] Nao encontro o ssh do Windows em %SSH%.
    pause
    exit /b 1
)
echo       OK

rem -- 2. As paginas por idioma ---------------------------------------
rem   As 15 pastas de lingua e o sitemap.xml sao GERADOS: nunca se editam a
rem   mao. Se o gerador falhar, nao se publica.
echo.
echo [2/7] A gerar as paginas por idioma...
python "%SITE_DIR%tools\gerar-linguas.py"
if errorlevel 1 (
    echo [ERRO] O gerador das paginas por idioma falhou. Abortado.
    pause
    exit /b 1
)
echo       OK

rem -- 3. As paginas de reencaminhar do GitHub (docs/) -----------------
echo.
echo [3/7] A gerar as paginas de reencaminhar do GitHub...
python "%SITE_DIR%tools\gerar-reencaminhamentos.py"
if errorlevel 1 (
    echo [ERRO] O gerador dos reencaminhamentos falhou. Abortado.
    pause
    exit /b 1
)
echo       OK

rem -- 4. O site no servidor ------------------------------------------
rem   O pacote leva o site e mais nada: fora ficam o .git, as ferramentas,
rem   as paginas do GitHub (docs/), os ficheiros da raiz (raiz/) e este
rem   .cmd. As pastas vao com 755 e os ficheiros com 644.
echo.
echo [4/7] A publicar o site no servidor...
python "%SITE_DIR%tools\empacotar.py" site | "%SSH%" -i "%CHAVE%" -o IdentitiesOnly=yes -o BatchMode=yes %SERVIDOR% publicar mbrothers
if errorlevel 1 (
    echo [ERRO] A publicacao no servidor falhou. Nada foi para o GitHub.
    pause
    exit /b 1
)
echo       OK

rem -- 5. A raiz do dominio -------------------------------------------
echo.
echo [5/7] A publicar a raiz do dominio (robots.txt, favicon.ico, llms.txt)...
python "%SITE_DIR%tools\empacotar.py" raiz | "%SSH%" -i "%CHAVE%" -o IdentitiesOnly=yes -o BatchMode=yes %SERVIDOR% publicar raiz
if errorlevel 1 (
    echo [ERRO] A publicacao da raiz falhou. O site ja esta no servidor; nada foi para o GitHub.
    pause
    exit /b 1
)
echo       OK

rem -- 6. Commit e push para o GitHub ---------------------------------
rem   A mensagem do commit nao se pergunta. Quem quiser outra passa-a como
rem   argumento:  __publicar-site_mBrothers.cmd "Os cartoes dos produtos"
rem   Os dois "set" ficam fora de qualquer bloco (sem delayed expansion).
set "MSG=Site: atualizacao"
if not "%~1"=="" set "MSG=%~1"
echo.
echo [6/7] GitHub: commit e push...
git status --short
git add -A
if errorlevel 1 (
    echo [ERRO] git add falhou. O site ja esta no servidor.
    pause
    exit /b 1
)
git commit -m "%MSG%"
if errorlevel 1 echo       (nada para commit)
git push origin main
if errorlevel 1 (
    echo [ERRO] git push falhou. O site ja esta no servidor. Verifica 'git status' e 'gh auth status'.
    pause
    exit /b 1
)
echo       OK

rem -- 7. Conferir ----------------------------------------------------
echo.
echo [7/7] A conferir o site...
rem   O curl vai sem aspas a volta do caminho: o caminho do System32 nao tem
rem   espacos, e um "for /f" com varias aspas perde a primeira e a ultima.
set "ESTADO="
for /f %%s in ('%CURL% -s -o NUL -w "%%{http_code}" %URL%') do set "ESTADO=%%s"
echo       %URL% respondeu %ESTADO%
if not "%ESTADO%"=="200" (
    echo [AVISO] Esperava 200. Para voltar a versao anterior:
    echo         "%SSH%" -i "%CHAVE%" %SERVIDOR% voltar mbrothers
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Site publicado!
echo.
echo   %URL%
echo.
echo   O servidor guarda as tres ultimas versoes.
echo ==========================================
echo.
rem No fim, a janela fica aberta ate se carregar numa tecla, para se ver
rem se correu tudo bem (06/11/2026).
pause
