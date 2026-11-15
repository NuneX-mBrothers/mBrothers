# -*- coding: utf-8 -*-
r"""Faz o pacote .tar.gz que a porta de publicação do servidor recebe, e escreve-o no stdout.

    python tools/empacotar.py site    o site, sem .git, ferramentas, docs/, raiz/ nem o .cmd
    python tools/empacotar.py raiz    o site da Intrepid Parallel, na raiz do domínio: a pasta raiz/ inteira, menos
                                      os dicionários (raiz/i18n/), que só servem ao gerador (15/11/2026)

O .cmd de publicação liga-o ao ssh:  python tools\empacotar.py site | ssh … publicar mbrothers

⛔ Porque não o tar do Windows (06/11/2026, a primeira publicação falhou com ele):
   - as pastas iam marcadas «só de leitura» (dr-xr-xr-x): o OneDrive põe esse atributo às pastas, e o tar do Windows
     passa-o para o pacote. O servidor criava as pastas sem poder escrever lá dentro: «Cannot open: Permission denied»
     em todos os ficheiros, e a versão falhada ficou presa no servidor;
   - juntava as marcas do Windows (SCHILY.fflags), que o tar do servidor não conhece.
   Aqui as permissões são sempre as normais (pastas 755, ficheiros 644), sem dono, e no formato GNU, sem extensões.
⛔ Sem ligações nem ficheiros especiais: a porta recusa-os, e este script não os põe.
"""
import os
import sys
import tarfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORA_NO_TOPO = {".git", ".gitignore", ".gitattributes", ".claude", "tools", "docs", "raiz"}
# A raiz do domínio (desde 15/11/2026, o site da Intrepid Parallel). A porta do servidor recusa no primeiro nível
# os nomes mbrothers, logviewer, explorerfocus, email, raiz e saude, e o que comece por um ponto (ENG_COB-000082).
FORA_DA_RAIZ = {"i18n"}
PROIBIDOS_NA_RAIZ = {"mbrothers", "logviewer", "explorerfocus", "email", "raiz", "saude"}


def normal(ti):
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = ""
    ti.mode = 0o755 if ti.isdir() else 0o644
    return ti


def juntar(tar, caminho, nome):
    ti = tar.gettarinfo(caminho, arcname=nome)
    if not (ti.isfile() or ti.isdir()):
        sys.exit("[ERRO] %s não é um ficheiro nem uma pasta normal" % caminho)
    ti = normal(ti)
    if ti.isfile():
        with open(caminho, "rb") as fh:
            tar.addfile(ti, fh)
    else:
        tar.addfile(ti)


def site(tar):
    juntar(tar, RAIZ, ".")
    for pasta, pastas, ficheiros in os.walk(RAIZ):
        rel = os.path.relpath(pasta, RAIZ)
        if rel == ".":
            pastas[:] = [p for p in pastas if p not in FORA_NO_TOPO]
            ficheiros = [f for f in ficheiros if f not in FORA_NO_TOPO and not f.lower().endswith(".cmd")]
        pastas.sort()
        for p in pastas:
            caminho = os.path.join(pasta, p)
            if os.path.islink(caminho):
                sys.exit("[ERRO] ligação: %s" % caminho)
            juntar(tar, caminho, "./" + os.path.relpath(caminho, RAIZ).replace(os.sep, "/"))
        for f in sorted(ficheiros):
            caminho = os.path.join(pasta, f)
            juntar(tar, caminho, "./" + os.path.relpath(caminho, RAIZ).replace(os.sep, "/"))


def raiz(tar):
    base = os.path.join(RAIZ, "raiz")
    if not os.path.isfile(os.path.join(base, "index.html")):
        sys.exit("[ERRO] falta o raiz/index.html")
    juntar(tar, base, ".")
    for pasta, pastas, ficheiros in os.walk(base):
        rel = os.path.relpath(pasta, base)
        if rel == ".":
            for nome in pastas + ficheiros:
                if nome.lower() in PROIBIDOS_NA_RAIZ or nome.startswith("."):
                    sys.exit("[ERRO] a raiz não pode ter «%s» no primeiro nível" % nome)
            pastas[:] = [d for d in pastas if d not in FORA_DA_RAIZ]
        pastas.sort()
        for d in pastas:
            caminho = os.path.join(pasta, d)
            if os.path.islink(caminho):
                sys.exit("[ERRO] ligação: %s" % caminho)
            juntar(tar, caminho, "./" + os.path.relpath(caminho, base).replace(os.sep, "/"))
        for f in sorted(ficheiros):
            caminho = os.path.join(pasta, f)
            juntar(tar, caminho, "./" + os.path.relpath(caminho, base).replace(os.sep, "/"))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("site", "raiz"):
        sys.exit("uso: python tools/empacotar.py site|raiz")
    if sys.stdout.isatty():
        sys.exit("[ERRO] o pacote é binário: liga-o ao ssh com |, ou manda-o para um ficheiro com >")
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz", format=tarfile.GNU_FORMAT) as tar:
        (site if sys.argv[1] == "site" else raiz)(tar)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
