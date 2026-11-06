# -*- coding: utf-8 -*-
"""Gera, em docs/, as páginas que o GitHub Pages passa a servir depois da mudança do site.

O site da mBrothers mudou-se para https://intrepidparallel.com/mbrothers/ (decisão de 06/11/2026). O GitHub
deixa de ter o site e fica só a reencaminhar quem chegar pelos endereços antigos
(https://nunex-mbrothers.github.io/mBrothers/…), cada página para a sua equivalente no endereço novo: a portuguesa
para a portuguesa, a alemã para a alemã, e não tudo para a entrada.

    docs/index.html, docs/<língua>/index.html, docs/legal.html
            reencaminham já (meta refresh + location.replace) e dizem ao Google qual é a página verdadeira (canonical).
    docs/404.html
            qualquer outro endereço antigo: troca /mBrothers/ por /mbrothers/ no domínio novo.
    docs/sw.js
            ⛔ o service worker antigo ficou registado nos navegadores de quem já visitou o GitHub Pages. Este
            substitui-o: apaga as caches DA mBrothers (as do EF e do LogViewer estão na mesma origem e não se tocam),
            desregista-se e recarrega as páginas abertas, que então reencaminham.
    docs/googlee….html
            o ficheiro de verificação da Search Console, para continuarmos a ver o endereço antigo durante a mudança.

⛔ Sem GoatCounter nem nada de terceiros nestas páginas: só reencaminham.
⚠ Para o GitHub servir isto, a fonte do Pages passa de «main, /» para «main, /docs». Faz-se NO DIA em que o site novo
  estiver no ar; antes disso, os endereços antigos reencaminhariam para um site que ainda não existe.
⚠ O envio para o servidor não leva a pasta docs/.

Corre-se da raiz do site:  python tools/gerar-reencaminhamentos.py
"""
import glob
import html as H
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVO = "https://intrepidparallel.com/mbrothers/"
DOCS = os.path.join(RAIZ, "docs")
NAO_SAO_LINGUAS = {"docs", "tools", "fonts", "i18n"}

MODELO = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>mBrothers</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace({url_js} + location.search + location.hash);</script>
<style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#e9dfc4;color:#14130f;font-family:Georgia,serif;padding:0 16px}}a{{color:#a86b2c}}</style>
</head>
<body>
<p>mBrothers has moved to <a href="{url}">{mostrar}</a>.</p>
</body>
</html>
"""

PAGINA_404 = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>mBrothers</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={novo}">
<script>
  /* /mBrothers/qualquer/coisa -> https://intrepidparallel.com/mbrothers/qualquer/coisa */
  var resto = location.pathname.replace(/^\\/mBrothers\\/?/i, "");
  location.replace({novo_js} + resto + location.search + location.hash);
</script>
<style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#e9dfc4;color:#14130f;font-family:Georgia,serif;padding:0 16px}}a{{color:#a86b2c}}</style>
</head>
<body>
<p>mBrothers has moved to <a href="{novo}">{mostrar}</a>.</p>
</body>
</html>
"""

SW = """/* O site da mBrothers mudou-se para https://intrepidparallel.com/mbrothers/ (06/11/2026).
   Este worker substitui o antigo nos navegadores que ja tinham visitado o GitHub Pages: apaga as caches da mBrothers
   (so as que comecam por "mbrothers-": as do EF e do LogViewer estao na mesma origem e nao se tocam), desregista-se e
   recarrega as paginas abertas, que entao reencaminham para o endereco novo. */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k.indexOf('mbrothers-') === 0; })
                               .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.registration.unregister(); })
      .then(function () { return self.clients.matchAll({ type: 'window' }); })
      .then(function (clients) { clients.forEach(function (c) { c.navigate(c.url); }); })
  );
});
"""


FEITOS = set()


def escrever(rel, texto):
    f = os.path.join(DOCS, rel)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    FEITOS.add(os.path.normcase(os.path.abspath(f)))


def pagina(url):
    return MODELO.format(url=H.escape(url, quote=True), url_js='"%s"' % url,
                         mostrar=H.escape(url.replace("https://", "").rstrip("/")))


def main():
    # ⛔ Não se apaga a pasta docs/ para a refazer: o OneDrive segura as pastas e o rmtree falha a meio (06/11, na
    #    primeira publicação: «Access is denied» em docs\ar). Escreve-se por cima, e no fim apagam-se só os FICHEIROS
    #    que já não fazem parte (uma língua que saísse, por exemplo). As pastas vazias ficam: o git ignora-as.
    linguas = sorted(d for d in os.listdir(RAIZ)
                     if d not in NAO_SAO_LINGUAS and not d.startswith(".")
                     and os.path.isfile(os.path.join(RAIZ, d, "index.html")))
    escrever("index.html", pagina(NOVO))
    for d in linguas:
        escrever(os.path.join(d, "index.html"), pagina(NOVO + d + "/"))
    escrever("legal.html", pagina(NOVO + "legal.html"))
    escrever("404.html", PAGINA_404.format(novo=H.escape(NOVO, quote=True), novo_js='"%s"' % NOVO,
                                           mostrar=H.escape(NOVO.replace("https://", "").rstrip("/"))))
    escrever("sw.js", SW)
    escrever(".nojekyll", "")
    for g in glob.glob(os.path.join(RAIZ, "google*.html")):
        destino = os.path.join(DOCS, os.path.basename(g))
        shutil.copyfile(g, destino)
        FEITOS.add(os.path.normcase(os.path.abspath(destino)))
    sobras = []
    for pasta, _, ficheiros in os.walk(DOCS):
        for nome in ficheiros:
            f = os.path.join(pasta, nome)
            if os.path.normcase(os.path.abspath(f)) not in FEITOS:
                os.remove(f)
                sobras.append(os.path.relpath(f, DOCS))
    if sobras:
        print("   apagados de docs/ (já não fazem parte):", " ".join(sobras))
    print("✅ docs/: entrada, %d línguas (%s), legal, 404, sw.js, verificação da Search Console"
          % (len(linguas), " ".join(linguas)))


if __name__ == "__main__":
    main()
