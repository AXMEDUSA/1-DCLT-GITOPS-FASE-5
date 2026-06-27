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
    margin: 2.5cm 2.2cm 2.5cm 2.2cm;
    @bottom-right {
        content: "Página " counter(page) " de " counter(pages);
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #9ca3af;
    }
    @bottom-left {
        content: "SolidaryTech — Relatório de Entrega Técnica | Hackathon FIAP Fase 5";
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #9ca3af;
    }
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1f2937;
    background: #ffffff;
    text-align: left;
}

/* TÍTULO PRINCIPAL */
h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-top: 0;
    margin-bottom: 4pt;
    padding-bottom: 8pt;
    border-bottom: 3px solid #1d4ed8;
    page-break-before: avoid;
    page-break-after: avoid;
    text-align: left;
}

/* SEÇÕES PRINCIPAIS — nova página antes */
h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #ffffff;
    background-color: #1d4ed8;
    margin-top: 0;
    margin-bottom: 12pt;
    padding: 6pt 10pt;
    page-break-before: always;
    page-break-after: avoid;
    text-align: left;
}

/* primeira seção não força nova página */
body > h2:first-of-type,
h1 + h2,
h1 + p + h2,
h1 + p + p + h2 {
    page-break-before: avoid;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-top: 14pt;
    margin-bottom: 6pt;
    border-bottom: 1px solid #dbeafe;
    padding-bottom: 3pt;
    page-break-after: avoid;
    text-align: left;
}

h4 {
    font-size: 10pt;
    font-weight: bold;
    color: #374151;
    margin-top: 10pt;
    margin-bottom: 4pt;
    page-break-after: avoid;
    text-align: left;
}

p {
    margin-bottom: 7pt;
    text-align: left;
    orphans: 3;
    widows: 3;
}

/* BLOCKQUOTE */
blockquote {
    margin: 10pt 0;
    padding: 8pt 12pt;
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    color: #166534;
    font-size: 9.5pt;
    text-align: left;
}

blockquote p { margin: 0; }

/* CÓDIGO INLINE — sem cor, só fundo neutro */
code {
    font-family: "Courier New", Courier, monospace;
    font-size: 8.5pt;
    background: #f3f4f6;
    color: #111827;
    padding: 1pt 3pt;
    border-radius: 2px;
    border: 1px solid #d1d5db;
}

/* BLOCOS DE CÓDIGO */
pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
    background: #1e293b;
    color: #e2e8f0;
    padding: 10pt 12pt;
    border-radius: 4px;
    margin: 8pt 0;
    white-space: pre-wrap;
    word-break: break-all;
    page-break-inside: avoid;
    line-height: 1.45;
    text-align: left;
}

pre code {
    background: none;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
    border-radius: 0;
}

/* TABELAS */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0 12pt 0;
    font-size: 9pt;
    page-break-inside: avoid;
    text-align: left;
}

thead tr {
    background-color: #1e3a5f;
    color: #ffffff;
}

thead th {
    padding: 6pt 8pt;
    text-align: left;
    font-weight: bold;
    font-size: 8.5pt;
}

tbody tr:nth-child(even) { background-color: #f8fafc; }
tbody tr:nth-child(odd)  { background-color: #ffffff; }

tbody td {
    padding: 5pt 8pt;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    color: #1f2937;
    text-align: left;
}

/* LISTAS */
ul, ol {
    margin: 4pt 0 8pt 20pt;
    text-align: left;
}

li { margin-bottom: 3pt; }
li p { margin: 0; }

/* IMAGENS */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 8pt 0;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    page-break-inside: avoid;
}

/* legenda (itálico sozinho num parágrafo após imagem) */
p > em:only-child {
    display: block;
    font-size: 8.5pt;
    color: #6b7280;
    margin-top: 2pt;
    margin-bottom: 8pt;
    font-style: italic;
    text-align: left;
}

/* LINKS — texto azul legível, sem sublinhado colorido */
a {
    color: #1d4ed8;
    text-decoration: none;
    word-break: break-all;
}

/* SEPARADORES */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 14pt 0;
}

strong { color: #111827; font-weight: bold; }

/* Evitar órfão: conteúdo logo após cabeçalho não quebra página */
h2 + *, h3 + *, h4 + * { page-break-before: avoid; }
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

# Remove atributo align que o markdown gera às vezes
html_body = re.sub(r' align="[^"]*"', '', html_body)

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
