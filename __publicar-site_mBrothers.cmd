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
echo [1/5] A validar o repositorio...
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

rem -- 2. Gerar a pagina por idioma --------------------------------
rem   O site tem uma porta por lingua: a raiz em ingles e /pt/ com o texto
rem   ja traduzido DENTRO do HTML (nao por JavaScript, que nao da exposicao
rem   nenhuma nos motores de busca). A pasta /pt/ e o sitemap.xml sao
rem   GERADOS -- nunca se editam a mao.
rem
rem   Corre ANTES do `git status` de proposito: assim o que aparece na lista
rem   do que vai ser publicado ja inclui a pagina gerada. Se falhar, ABORTA:
rem   mais vale nao publicar do que publicar a pagina portuguesa a dizer o
rem   texto antigo.
rem
rem   Acrescentar uma lingua e escrever i18n\<codigo>.js e uma linha no
rem   LINGUAS do gerador. Este ficheiro nao precisa de mudar.
echo.
echo [2/5] A gerar a pagina por idioma...
python "%SITE_DIR%tools\gerar-linguas.py"
if errorlevel 1 (
    echo [ERRO] O gerador das paginas por idioma falhou.
    echo        Sem ele, as 15 paginas por idioma ficam desactualizadas. Abortado.
    pause
    exit /b 1
)
echo       OK

rem -- 3. Mostrar o que vai ser publicado ------------------------------
echo.
echo [3/5] Alteracoes por publicar:
git status --short
echo.

set "NCH=0"
for /f %%c in ('git status --porcelain ^| find /c /v ""') do set "NCH=%%c"
if "%NCH%"=="0" goto :nada

rem A mensagem do commit NAO se pergunta: o `set /p` parava aqui a pedir
rem uma resposta que era sempre a mesma. Usa-se a de omissao, e quem quiser
rem outra passa-a como argumento:
rem     __publicar-site_mBrothers.cmd "Os cartoes dos produtos"
rem
rem Os dois `set` ficam ao nivel de cima, FORA de qualquer bloco `if (...)`:
rem este ficheiro nao tem delayed expansion, e dentro de um bloco o %MSG%
rem seria expandido quando o bloco e LIDO e nao quando corre -- sairia
rem vazio. O `if` de uma linha so, sem parenteses, nao tem esse problema.
set "MSG=Site: atualizacao"
if not "%~1"=="" set "MSG=%~1"
echo       Mensagem: %MSG%

rem -- 4. Adicionar e commitar ----------------------------------------
echo.
echo [4/5] git add + commit...
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
echo [4/5] ^(sem commit^)

rem -- 5. Push --------------------------------------------------------
:push
echo.
echo [5/5] git push...
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
echo   Sem build e sem Release. A versao continua escrita a mao;
echo   as 15 paginas por idioma e o sitemap.xml foram gerados no passo [2/5].
echo ==========================================
echo.
rem O pause FINAL saiu, por pedido do Joao: nao ter de carregar nada.
rem Nao se apaga sem mais: se o script for corrido por duplo clique, a
rem janela fechava-se antes de dar tempo de ler o resultado. O timeout
rem mostra a contagem, fecha-se sozinho ao fim de 12s, e fecha logo se se
rem carregar numa tecla -- as tres coisas ao mesmo tempo.
rem Os outros cinco pause FICAM: sao caminhos de erro, e ai queremos parar.
timeout /t 12
