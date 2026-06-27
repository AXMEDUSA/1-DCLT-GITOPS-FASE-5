#!/usr/bin/env python3
import markdown
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
MD_FILE = BASE_DIR / "documentacao-solidarytech.md"
HTML_FILE = BASE_DIR / "documentacao-solidarytech.html"
PDF_FILE = BASE_DIR / "SolidaryTech-Relatorio-Entrega.pdf"

CSS = """
@page {
    size: A4;
    margin: 2cm 2cm 2.2cm 2cm;
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #6b7280;
    }
    @bottom-left {
        content: "SolidaryTech — Relatório de Entrega | FIAP Fase 5";
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #6b7280;
    }
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.55;
    color: #1f2937;
    background: #ffffff;
}

/* ── TÍTULOS ─────────────────────────────────── */
h1 {
    font-size: 18pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-bottom: 6pt;
    padding-bottom: 6pt;
    border-bottom: 3px solid #1d4ed8;
    page-break-after: avoid;
}

h2 {
    font-size: 12pt;
    font-weight: bold;
    color: #ffffff;
    background-color: #1d4ed8;
    margin-top: 16pt;
    margin-bottom: 8pt;
    padding: 5pt 9pt;
    page-break-after: avoid;
    /* SEM page-break-before: always — fluxo contínuo */
}

h3 {
    font-size: 10.5pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-top: 12pt;
    margin-bottom: 5pt;
    border-bottom: 1px solid #dbeafe;
    padding-bottom: 2pt;
    page-break-after: avoid;
}

h4 {
    font-size: 10pt;
    font-weight: bold;
    color: #374151;
    margin-top: 9pt;
    margin-bottom: 3pt;
    page-break-after: avoid;
}

/* ── PARÁGRAFOS ───────────────────────────────── */
p {
    margin-bottom: 6pt;
    orphans: 2;
    widows: 2;
}

/* ── BLOCKQUOTE ───────────────────────────────── */
blockquote {
    margin: 6pt 0;
    padding: 6pt 10pt;
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    color: #166534;
    font-size: 9.5pt;
}
blockquote p { margin: 0; }

/* ── CÓDIGO INLINE ────────────────────────────── */
code {
    font-family: "Courier New", monospace;
    font-size: 8.5pt;
    background: #f3f4f6;
    color: #111827;
    padding: 0 3pt;
    border-radius: 2px;
    border: 1px solid #d1d5db;
}

/* ── BLOCOS DE CÓDIGO ─────────────────────────── */
pre {
    font-family: "Courier New", monospace;
    font-size: 7.5pt;
    background: #1e293b;
    color: #e2e8f0;
    padding: 8pt 10pt;
    border-radius: 4px;
    margin: 6pt 0;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.4;
    /* sem page-break-inside: avoid em blocos grandes — deixa quebrar naturalmente */
}
pre code {
    background: none; color: inherit;
    padding: 0; border: none; font-size: inherit;
}

/* ── TABELAS ──────────────────────────────────── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 6pt 0 10pt 0;
    font-size: 9pt;
}
thead tr { background-color: #1e3a5f; color: #ffffff; }
thead th {
    padding: 5pt 7pt;
    text-align: left;
    font-weight: bold;
    font-size: 8.5pt;
}
tbody tr:nth-child(even) { background-color: #f8fafc; }
tbody tr:nth-child(odd)  { background-color: #ffffff; }
tbody td {
    padding: 4pt 7pt;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
}

/* ── LISTAS ───────────────────────────────────── */
ul, ol { margin: 3pt 0 6pt 18pt; }
li { margin-bottom: 2pt; }
li p { margin: 0; }

/* ── IMAGENS ──────────────────────────────────── */
img {
    max-width: 100%;
    max-height: 16cm;   /* limita altura — evita imagem sozinha numa página */
    height: auto;
    display: block;
    margin: 6pt 0;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
}

/* legenda */
p > em:only-child {
    display: block;
    font-size: 8pt;
    color: #6b7280;
    margin-top: 1pt;
    margin-bottom: 7pt;
    font-style: italic;
}

/* ── LINKS ────────────────────────────────────── */
a { color: #1d4ed8; text-decoration: none; word-break: break-all; }

/* ── SEPARADORES ──────────────────────────────── */
hr { border: none; border-top: 1px solid #e5e7eb; margin: 10pt 0; }

strong { color: #111827; font-weight: bold; }
"""

md_text = MD_FILE.read_text(encoding="utf-8")

# Converte caminhos relativos de imagem para absolutos
def fix_image_paths(text, base):
    def replacer(m):
        alt = m.group(1)
        path = m.group(2)
        if not path.startswith(("http://", "https://", "/")):
            abs_path = (base / path).resolve()
            return f"![{alt}]({abs_path})"
        return m.group(0)
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replacer, text)

md_text = fix_image_paths(md_text, BASE_DIR)

extensions = ["tables", "fenced_code", "nl2br", "attr_list"]
html_body = markdown.markdown(md_text, extensions=extensions)

# Converte URLs brutas em âncoras clicáveis (linkify manual)
def linkify(html):
    # Evita substituir URLs que já estão dentro de href= ou src=
    url_re = re.compile(
        r'(?<!["\'=>])(https?://[^\s<>"\')\],]+)',
    )
    def make_link(m):
        url = m.group(1)
        return f'<a href="{url}">{url}</a>'
    # Aplica apenas fora de tags HTML (entre >...<)
    result = []
    last = 0
    for tag_match in re.finditer(r'<[^>]+>', html):
        # texto entre tags — aplica linkify
        text_chunk = html[last:tag_match.start()]
        result.append(url_re.sub(make_link, text_chunk))
        # a tag em si — não mexe
        result.append(tag_match.group(0))
        last = tag_match.end()
    result.append(url_re.sub(make_link, html[last:]))
    return ''.join(result)

html_body = linkify(html_body)

# Remove atributo align que o markdown gera às vezes
html_body = re.sub(r' align="[^"]*"', '', html_body)

# Adiciona id nos h2 para âncoras internas
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[áàãâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòõôö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def add_heading_ids(html):
    def replacer(m):
        tag = m.group(1)   # h2, h3, etc
        content = m.group(2)
        # texto limpo sem tags internas
        clean = re.sub(r'<[^>]+>', '', content)
        slug = slugify(clean)
        return f'<{tag} id="{slug}">{content}</{tag}>'
    return re.sub(r'<(h[23])>(.*?)</\1>', replacer, html, flags=re.DOTALL)

html_body = add_heading_ids(html_body)

# Converte itens do sumário em links internos
# O sumário está dentro do primeiro <ol> após o <h2 id="sumario">
def linkify_toc(html):
    # Monta mapa: slug do h2 -> id real
    h2_ids = re.findall(r'<h2 id="([^"]+)">[^<]*</h2>', html)

    def replace_toc_li(m):
        text = m.group(1).strip()
        slug = slugify(text)
        match_id = None
        for hid in h2_ids:
            # IDs dos h2 têm prefixo "N-" (ex: "1-visao-geral") — remove para comparar
            hid_sem_numero = re.sub(r'^\d+-', '', hid)
            if hid_sem_numero == slug or hid_sem_numero.startswith(slug[:12]):
                match_id = hid
                break
        if match_id:
            return f'<li><a href="#{match_id}">{text}</a></li>'
        return m.group(0)

    # Localiza o bloco <ol>...</ol> que é o sumário (logo após h2#sumario)
    toc_pattern = re.compile(
        r'(<h2 id="sumario">.*?</h2>\s*<ol>)(.*?)(</ol>)',
        re.DOTALL
    )
    def replace_toc_block(m):
        before = m.group(1)
        items = m.group(2)
        after = m.group(3)
        items = re.sub(r'<li>(.*?)</li>', replace_toc_li, items, flags=re.DOTALL)
        return before + items + after

    return toc_pattern.sub(replace_toc_block, html)

html_body = linkify_toc(html_body)

html_full = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>SolidaryTech — Relatório de Entrega</title>
<style>
{CSS}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

HTML_FILE.write_text(html_full, encoding="utf-8")
print(f"HTML gerado: {HTML_FILE}")

from weasyprint import HTML
HTML(filename=str(HTML_FILE), base_url=str(BASE_DIR)).write_pdf(str(PDF_FILE))
size = PDF_FILE.stat().st_size / 1024
print(f"PDF gerado: {PDF_FILE} ({size:.0f} KB)")
