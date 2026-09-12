# -*- coding: utf-8 -*-
"""Gera as páginas por idioma do site do mBrothers.

    /        inglês, a raiz
    /pt/     a MESMA página com o texto já traduzido no HTML (não por
             JavaScript), com `lang`, título, descrição e canonical próprios,
             e `hreflang` recíproco entre as duas.

⛔ Isto não é conteúdo escrito à mão: é GERADO. Sempre que o texto do site
   mudar, correr outra vez — senão a página por idioma fica para trás. O
   `__publicar-site_mBrothers.cmd` já o corre antes de commitar.

📌 Só gera as línguas cujo dicionário existe em i18n/. Acrescentar o Brasil é
   escrever `i18n/br.js` e uma linha no LINGUAS — mais nada.

⚠ É irmão do `tools/gerar-linguas.py` do LogViewer e tem as mesmas três regras
  duramente aprendidas:
    · aceita a PRÓPRIA SAÍDA como entrada (corrido 2× dá o mesmo ficheiro);
    · o selector troca-se ANTES de prefixar os caminhos;
    · o `lang` do <html> é a etiqueta BCP-47, nunca o código do dicionário.

Corre-se da raiz do site:  python tools/gerar-linguas.py
"""
import datetime
import html as H
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://nunex-mbrothers.github.io/mBrothers/"

# código do dicionário → pasta, rótulo, hreflang (BCP-47), og:locale, bandeira.
# 🥇 Decisão do João a 2026-09-12: **as MESMAS 16 línguas do LogViewer**, e não
#    uma escolha pela medição — *«não faz sentido limitar a pesquisa»*. A minha
#    proposta anterior era duas (tradicional e japonês) e foi revogada: com o
#    gerador feito, cada porta nova custa um dicionário, e uma porta a menos é
#    exposição que não existe.
# ⚠ São QUINZE pastas para DEZASSEIS bandeiras: o inglês é a raiz e não tem
#   pasta, por isso o GB e o US levam os dois ao mesmo sítio.
# ⛔ O `pt` fica em `pt` GENÉRICO e o Brasil em `pt-BR`: assim o Brasil vai ao
#   /br/ e Angola, Moçambique e Portugal vão ao /pt/. Com `pt-PT` os outros
#   países lusófonos caíam no x-default, que é inglês.
# ⛔ E o `lang` do <html> leva a etiqueta BCP-47, NUNCA o código do dicionário:
#   `br` em BCP-47 é o BRETÃO.
LINGUAS = [
    ("pt",    "pt",    "Português",  "pt",      "pt_PT", "pt"),
    ("br",    "br",    "Português (BR)", "pt-BR", "pt_BR", "br"),
    ("en",    "",      "English (GB)", "en",    "en_GB", "gb"),
    ("es",    "es",    "Español",    "es",      "es_ES", "es"),
    ("fr",    "fr",    "Français",   "fr",      "fr_FR", "fr"),
    ("it",    "it",    "Italiano",   "it",      "it_IT", "it"),
    ("de",    "de",    "Deutsch",    "de",      "de_DE", "de"),
    ("pl",    "pl",    "Polski",     "pl",      "pl_PL", "pl"),
    ("ru",    "ru",    "Русский",    "ru",      "ru_RU", "ru"),
    ("ar",    "ar",    "العربية",     "ar",      "ar_AR", "sa"),
    ("hi",    "hi",    "हिन्दी",       "hi",      "hi_IN", "in"),
    ("zh",    "zh",    "中文 (简体)",  "zh-Hans", "zh_CN", "cn"),
    ("zh-TW", "zh-tw", "中文 (繁體)",  "zh-Hant", "zh_TW", "tw"),
    ("ja",    "ja",    "日本語",      "ja",      "ja_JP", "jp"),
    ("ko",    "ko",    "한국어",       "ko",      "ko_KR", "kr"),
]

# A BARRA DA APP, espelhada: dezasseis bandeiras pela ordem da barra do
# programa, mesmo que o GB e o US levem à mesma página. É o mesmo desenho e a
# mesma ordem dos outros dois sites — a coerência é ordem do João.
#   (bandeira, rótulo, código do dicionário)
BARRA_DA_APP = [
    ("pt", "Português",      "pt"),
    ("br", "Português (BR)", "br"),
    ("gb", "English (GB)",   "en"),
    ("us", "English (US)",   "en"),   # a única que leva à mesma página
    ("es", "Español",        "es"),
    ("fr", "Français",       "fr"),
    ("it", "Italiano",       "it"),
    ("de", "Deutsch",        "de"),
    ("pl", "Polski",         "pl"),
    ("ru", "Русский",        "ru"),
    ("sa", "العربية",         "ar"),
    ("in", "हिन्दी",           "hi"),
    ("cn", "中文 (简体)",      "zh"),
    ("tw", "中文 (繁體)",      "zh-TW"),
    ("jp", "日本語",          "ja"),
    ("kr", "한국어",           "ko"),
]

# A única língua que se lê da direita para a esquerda.
RTL = {"ar"}

# as chaves que vão para o <head> em vez de para o corpo
CABECA = [
    (r'<title>.*?</title>', None, "meta.title"),
    (r'(<meta name="description" content=")[^"]*(")', True, "meta.desc"),
    (r'(<meta property="og:title" content=")[^"]*(")', True, "og.title"),
    (r'(<meta property="og:description" content=")[^"]*(")', True, "og.desc"),
    (r'(<meta property="og:image:alt" content=")[^"]*(")', True, "og.imgalt"),
    (r'(<meta name="twitter:title" content=")[^"]*(")', True, "tw.title"),
    (r'(<meta name="twitter:description" content=")[^"]*(")', True, "tw.desc"),
    (r'("description": ")[^"]*(",)', True, "ld.desc"),
]


def existe(cod):
    return os.path.exists(os.path.join(RAIZ, "i18n", cod + ".js"))


def dicionario(cod):
    """O dicionário vem do próprio ficheiro .js, lido pelo node — assim não há
    um segundo parser a inventar o que está escrito no ficheiro."""
    js = ("global.window={I18N:{}};require(%s);"
          "process.stdout.write(JSON.stringify(window.I18N[%s]||null));"
          % (json.dumps(os.path.join(RAIZ, "i18n", cod + ".js").replace("\\", "/")),
             json.dumps(cod)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0 or not r.stdout or r.stdout.strip() == "null":
        sys.exit("⛔ não consegui ler o dicionário %s: %s" % (cod, (r.stderr or r.stdout).strip()[:200]))
    return json.loads(r.stdout)


def traduzir(pagina, d, cod):
    """Três marcas, e a terceira é nova em relação ao LogViewer:
         data-i18n       → o texto do elemento, escapado
         data-i18n-html  → o texto do elemento, com HTML lá dentro
         data-i18n-attr  → ATRIBUTOS, no formato «attr:chave;attr:chave»
    ⛔ O site do ExplorerFocus não tem a terceira, e por isso o `aria-label` do
       botão do tema ficava sempre em inglês — num leitor de ecrã, a única
       palavra que aquele botão tem."""
    faltas, feitas = [], 0

    def troca(m, escapar):
        nonlocal feitas
        abre, chave, fecha = m.group(1), m.group(3), m.group(5)
        v = d.get(chave)
        if v is None:
            faltas.append(chave)
            return m.group(0)
        feitas += 1
        return abre + (H.escape(v, quote=False) if escapar else v) + fecha

    p_txt = re.compile(r'(<([a-zA-Z][\w-]*)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>)(.*?)(</\2>)', re.S)
    p_htm = re.compile(r'(<([a-zA-Z][\w-]*)\b[^>]*\bdata-i18n-html="([^"]+)"[^>]*>)(.*?)(</\2>)', re.S)
    pagina = p_htm.sub(lambda m: troca(m, False), pagina)
    pagina = p_txt.sub(lambda m: troca(m, True), pagina)

    # os atributos: uma passagem por elemento que declare data-i18n-attr
    def troca_attr(m):
        nonlocal feitas
        tag = m.group(0)
        for par in m.group(1).split(";"):
            if ":" not in par:
                continue
            attr, chave = par.split(":", 1)
            v = d.get(chave.strip())
            if v is None:
                faltas.append(chave.strip())
                continue
            novo, n = re.subn(r'\b%s="[^"]*"' % re.escape(attr.strip()),
                              '%s="%s"' % (attr.strip(), H.escape(v, quote=True)), tag, count=1)
            if n:
                tag = novo
                feitas += 1
        return tag

    pagina = re.sub(r'<[a-zA-Z][^>]*\bdata-i18n-attr="([^"]+)"[^>]*>', troca_attr, pagina)

    if faltas:
        sys.exit("⛔ [%s] chaves sem tradução: %s" % (cod, sorted(set(faltas))[:8]))
    return pagina, feitas


def prefixar(pagina):
    """Numa subpasta, os caminhos relativos passam a ../ — menos as âncoras, o
    mailto: e tudo o que já é absoluto.
    ⛔ `../` e `./` ficam como estão: são os do selector, que já vem escrito
       relativo à pasta certa."""
    def f(m):
        v = m.group(2)
        if re.match(r'^(https?:|//|#|mailto:|data:|/|\.\./|\./)', v):
            return m.group(0)
        return m.group(1) + "../" + v + m.group(3)
    return re.sub(r'(\s(?:src|href)=")([^"]+)(")', f, pagina)


def url_de(pasta):
    return BASE + (pasta + "/" if pasta else "")


def bandeira(fl):
    return ('<svg class="lang-fl" viewBox="0 0 20 14" aria-hidden="true">'
            '<use href="#fl-%s"/></svg>' % fl)


def selector(activas, pasta_actual, rotulo):
    """<details> porque abre sem JavaScript nenhum, e as ligações ficam no HTML
    — que é o que os motores de busca leem. A língua actual marca-se com
    `aria-current` (são ligações, não botões).
    ⚠ Sem `hreflang` nas ligações: quem fala aos motores é o bloco
      <link rel="alternate"> do cabeçalho. Aqui há duas entradas que levam à
      mesma página (GB e US) e um hreflang errado seria um sinal errado.
    ⛔ Os itens saem do BARRA_DA_APP e o rótulo do botão fechado sai da MESMA
       lista: no site do LogViewer saíam de listas diferentes, e a página /br/
       abria a dizer «Português» com «Português (BR)» logo por baixo."""
    pasta_de = {c: p for c, p, *_ in activas}
    etiqueta_de = {c: h for c, _p, _r, h, _l, _f in activas}
    para = lambda p: (("../" + p + "/") if p else "../") if pasta_actual else ((p + "/") if p else "./")
    cod_actual = next(c for c, p, *_ in activas if p == pasta_actual)
    fl_actual, rot_actual = next(((fl, r) for fl, r, c in BARRA_DA_APP if c == cod_actual),
                                 ("gb", "English (GB)"))
    itens = []
    for fl, rot, cod in BARRA_DA_APP:
        if cod not in pasta_de:          # língua sem dicionário → o inglês
            cod = "en"
        marca = ' aria-current="true"' if cod == cod_actual and fl == fl_actual else ""
        itens.append('          <a class="lang-btn" href="%s" lang="%s"%s>%s<span>%s</span></a>'
                     % (para(pasta_de[cod]), etiqueta_de[cod], marca, bandeira(fl), rot))
    return ('      <details class="lang-picker">\n'
            '        <summary class="lang-cur" title="%s">%s<span>%s</span></summary>\n'
            '        <div class="lang-list">\n%s\n        </div>\n'
            '      </details>\n' % (H.escape(rotulo, quote=True), bandeira(fl_actual),
                                    rot_actual, "\n".join(itens)))


def uma_vez(pagina, velho, novo, rot):
    n = pagina.count(velho)
    if n != 1:
        sys.exit("⛔ [%s] «%s…» aparece %d vezes" % (rot, velho[:50], n))
    return pagina.replace(velho, novo)


# ── a página de origem ──────────────────────────────────────────────────────
origem = io.open(os.path.join(RAIZ, "index.html"), encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in origem else "\n"
base_lf = origem.replace("\r\n", "\n")

activas = [l for l in LINGUAS if existe(l[0])]
if not activas:
    sys.exit("⛔ não há um único dicionário em i18n/")
print("línguas com dicionário: %s" % ", ".join(c for c, *_ in activas))

m_sel = re.search(r' *<details class="lang-picker"[^>]*>\n(?:.*?\n)*? *</details>\n', base_lf)
if not m_sel:
    sys.exit("⛔ não achei o bloco do selector de línguas")
SEL_ANTIGO = m_sel.group(0)

# ⚠ O padrão apanha a PRÓPRIA SAÍDA do gerador: à segunda corrida o cabeçalho
#   já é o novo, com o comentário à frente. Sem isto não era idempotente.
m_hl = re.search(r'(?:<!--(?:(?!-->).)*?-->\n)? *<link rel="alternate" hreflang="x-default"[^>]*/>\n'
                 r'(?: *<link rel="alternate" hreflang="[a-zA-Z-]+"[^>]*/>\n)*', base_lf, re.S)
if not m_hl:
    sys.exit("⛔ não achei o bloco hreflang")
HL_ANTIGO = m_hl.group(0)

COMENTARIO = (
    "<!-- Uma porta por lingua. Cada pagina tem canonical propria e hreflang\n"
    "     reciproco; o texto vai JA TRADUZIDO no HTML, sem JavaScript.\n"
    "     A pasta /pt/ e GERADA por tools/gerar-linguas.py -- mexer no texto do\n"
    "     site obriga a correr o gerador outra vez, e o .cmd de publicar ja o\n"
    "     faz antes de commitar. -->\n")


def bloco_hreflang(activas):
    l = ['<link rel="alternate" hreflang="x-default" href="%s" />' % BASE]
    for cod, pasta, _rot, hl, _loc, _fl in activas:
        l.append('<link rel="alternate" hreflang="%s" href="%s" />' % (hl, url_de(pasta)))
    return "\n".join(l)


for cod, pasta, rot, hl, loc, fl in activas:
    d = dicionario(cod)
    pag = base_lf
    url = url_de(pasta)

    if pasta:
        # ⛔ o `lang` leva a etiqueta BCP-47, nunca o código do dicionário
        direccao = ' dir="rtl"' if cod in RTL else ""
        pag = uma_vez(pag, '<html lang="en">',
                      '<html lang="%s"%s data-lang-fixa="%s">' % (hl, direccao, cod), cod)
    pag = uma_vez(pag, HL_ANTIGO, COMENTARIO + bloco_hreflang(activas) + "\n", cod)
    pag = uma_vez(pag, '<link rel="canonical" href="%s" />' % BASE,
                  '<link rel="canonical" href="%s" />' % url, cod)
    pag = uma_vez(pag, '<meta property="og:url" content="%s" />' % BASE,
                  '<meta property="og:url" content="%s" />' % url, cod)
    pag = uma_vez(pag, '<meta property="og:locale" content="en_GB" />',
                  '<meta property="og:locale" content="%s" />' % loc, cod)
    pag = uma_vez(pag, '"url": "%s",' % BASE, '"url": "%s",' % url, cod)

    feitas = 0
    if pasta:
        pag, feitas = traduzir(pag, d, cod)

    # o <head> é sempre reescrito, mesmo na raiz: é dali que sai o que aparece
    # nos resultados de pesquisa e nas pré-visualizações das redes sociais.
    for padrao, com_grupos, chave in CABECA:
        if com_grupos:
            pag = re.sub(padrao, lambda m: m.group(1) + H.escape(d[chave], quote=True) + m.group(2),
                         pag, count=1)
        else:
            pag = re.sub(padrao, lambda _m: "<title>%s</title>" % H.escape(d[chave], quote=False),
                         pag, count=1, flags=re.S)

    # ⛔ O selector troca-se ANTES do prefixar. Ao contrário, o prefixar mexia
    #    nos href do selector antigo e o bloco deixava de casar à segunda
    #    corrida -- foi o que aconteceu no site do LogViewer.
    pag = uma_vez(pag, SEL_ANTIGO, selector(activas, pasta, d["lang.label"]), cod)
    if pasta:
        pag = prefixar(pag)

    destino = os.path.join(RAIZ, pasta, "index.html") if pasta else os.path.join(RAIZ, "index.html")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    io.open(destino, "w", encoding="utf-8", newline="").write(pag.replace("\n", nl))
    print("✅ %-6s %s" % (pasta + "/" if pasta else "raiz",
                         ("%d textos" % feitas) if pasta else "inglês, só o cabeçalho"))

# ── sitemap ─────────────────────────────────────────────────────────────────
hoje = datetime.date.today().isoformat()
linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for cod, pasta, *_ in sorted(activas, key=lambda l: l[1]):
    linhas.append('  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq>'
                  '<priority>%s</priority></url>' % (url_de(pasta), hoje, "1.0" if not pasta else "0.8"))
linhas.append("</urlset>")
io.open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8", newline="").write(nl.join(linhas) + nl)
print("✅ sitemap.xml · %d endereços · lastmod %s" % (len(activas), hoje))
