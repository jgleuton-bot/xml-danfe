"""
patch_danfe_lib.py  —  v1.2.1
==============================
Corrige a biblioteca brazilfiscalreport (v0.7.8) com as seguintes alteracoes:

1. danfe.py — altura de DADOS ADICIONAIS dinamica: ajustada ao texto (min 20mm,
              max 90mm). O bloco fica alinhado ao rodape e a tabela de produtos
              preenche todo o espaco restante. Tipografia do campo INFORMACOES
              COMPLEMENTARES igual ao modelo da empresa: conteudo Times regular
              8pt, rotulo 6pt (demais campos continuam em negrito).
2. danfe.py — fonte da tabela de produtos: fixa em FONT_SIZE_DESC (5pt)
3. danfe.py — valores monetarios dos produtos em negrito
4. danfe.py — FATURA/DUPLICATA: titulo singular + formato compacto label+valor inline
5. danfe.py — tabela de produtos: bordas manuais (colunas + borda externa, sem linhas
              horizontais internas entre itens; colunas estendem ate DADOS ADICIONAIS)
6. danfe_basic_field.py — conteudo dos campos em negrito; campo INFORMACOES
              COMPLEMENTARES em Times regular 8pt com rotulo 6pt (modelo da empresa)

Uso:
    python patch_danfe_lib.py
"""

__version__ = "1.2.1"
import sys
import os
import re
import io
import importlib.util


# Espelha tudo o que aparece no terminal tambem para log_execucao.txt
class _Tee(io.TextIOBase):
    def __init__(self, *streams):
        self._streams = streams

    def write(self, s):
        for st in self._streams:
            try:
                st.write(s)
                st.flush()
            except Exception:
                pass
        return len(s)

    def flush(self):
        for st in self._streams:
            try:
                st.flush()
            except Exception:
                pass


try:
    _log = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_execucao.txt"),
        "a",
        encoding="utf-8",
    )
    sys.stdout = _Tee(sys.stdout, _log)
    sys.stderr = _Tee(sys.stderr, _log)
except Exception:
    pass


def encontrar_base():
    spec = importlib.util.find_spec("brazilfiscalreport")
    if spec is None:
        print("ERRO: brazilfiscalreport nao esta instalado.")
        sys.exit(1)
    return os.path.join(os.path.dirname(spec.origin), "danfe")


def patch_arquivo(caminho, patches, label):
    """patches: lista de (old_str, new_str, descricao)"""
    with open(caminho, "r", encoding="utf-8") as f:
        src = f.read()

    bak = caminho + ".bak"
    if not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"  Backup criado: {bak}")

    novo = src
    for old, new, desc in patches:
        if new in novo:
            print(f"  [{label}] {desc}: ja aplicado.")
        elif old not in novo:
            print(f"  [{label}] {desc}: padrao nao encontrado — versao incompativel.")
        else:
            novo = novo.replace(old, new, 1)
            print(f"  [{label}] {desc}: OK")

    if novo != src:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(novo)
    return novo != src


def patch_regex(caminho, pattern, new_text, desc, label):
    """Substitui usando regex (para casos onde a string exata e incerta)."""
    with open(caminho, "r", encoding="utf-8") as f:
        src = f.read()

    bak = caminho + ".bak"
    if not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"  Backup criado: {bak}")

    if new_text in src:
        print(f"  [{label}] {desc}: ja aplicado.")
        return False

    novo, n = re.subn(pattern, new_text, src, count=1, flags=re.DOTALL)
    if n == 0:
        print(f"  [{label}] {desc}: padrao nao encontrado — versao incompativel.")
        return False

    print(f"  [{label}] {desc}: OK")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(novo)
    return True


def limpar_cache(base_dir):
    pyc_dir = os.path.join(base_dir, "__pycache__")
    if os.path.exists(pyc_dir):
        removidos = sum(
            1
            for f in os.listdir(pyc_dir)
            if f.endswith(".pyc")
            and (os.remove(os.path.join(pyc_dir, f)) or True)
        )
        if removidos:
            print(f"  Cache .pyc removido ({removidos} arquivo(s)).")


# ---------------------------------------------------------------------------
# DADOS ADICIONAIS: altura dinamica ajustada ao texto, alinhada ao rodape.
# A tabela de produtos preenche automaticamente o espaco restante, pois a
# biblioteca calcula sua altura como (pagina - blocos antes - blocos depois).
# ---------------------------------------------------------------------------
ALTURA_OLD_TMPL = (
    "        height = (\n"
    "            continuation_height - HEIGHT_FONT_BLOCK_DESC "
    "if continuation_height else {valor}\n"
    "        )"
)

ALTURA_NEW = (
    "        if continuation_height:\n"
    "            height = continuation_height - HEIGHT_FONT_BLOCK_DESC\n"
    "        else:\n"
    "            # Altura dinamica: ajustada ao numero de linhas do texto\n"
    "            from fpdf.enums import MethodReturnValue as _MRV\n"
    "\n"
    "            from .danfe_conf import DEFAULT_HEIGHT_FONT_CONTENT as _DHC\n"
    "\n"
    "            # Mede com a tipografia do modelo: Times regular 8pt\n"
    "            self.set_font(self.default_font, \"\", 8)\n"
    "            _lines_ad = self.multi_cell(\n"
    "                w=self.edw - 70,\n"
    "                h=_DHC,\n"
    "                text=additional_data or \"\",\n"
    "                dry_run=True,\n"
    "                output=_MRV.LINES,\n"
    "            )\n"
    "            height = min(90.0, max(20.0, len(_lines_ad) * _DHC + 6))"
)


# ---------------------------------------------------------------------------
# Novo formato das duplicatas: label + valor na mesma linha
# ---------------------------------------------------------------------------
# Novo formato: label + valor na mesma linha, borda externa unica por duplicata
DUP_NEW = (
    "        # Renderiza duplicatas: label + valor na mesma linha\n"
    "        _n_dup = len(dup)\n"
    "        _cols = max(4, _n_dup)\n"
    "        _w_col = block_fatura.w / _cols\n"
    "        _base_x = self.get_x()\n"
    "        _base_y = self.get_y()\n"
    "        _fsize = self.get_font_size(\"FONT_SIZE_CONT\", True)\n"
    "        _lh = 4.5\n"
    "        _w_lbl = _w_col * 0.45\n"
    "        _w_val = _w_col - _w_lbl\n"
    "        for _i, _item_dup in enumerate(dup):\n"
    "            _col_idx = _i % _cols\n"
    "            _row_idx = _i // _cols\n"
    "            _x = _base_x + _col_idx * _w_col\n"
    "            _y0 = _base_y + _row_idx * 3 * _lh\n"
    "            _num = extract_text(_item_dup, \"nDup\")\n"
    "            _venc, _ = get_date_utc(extract_text(_item_dup, \"dVenc\"))\n"
    "            _valor = \"R$ \" + format_number(extract_text(_item_dup, \"vDup\"), 2)\n"
    "            self.rect(x=_x, y=_y0, w=_w_col, h=3 * _lh)\n"
    "            for _ri, (_lbl, _val) in enumerate([\n"
    "                (\"Número\", _num),\n"
    "                (\"Vencimento:\", _venc),\n"
    "                (\"Valor:\", _valor),\n"
    "            ]):\n"
    "                _y = _y0 + _ri * _lh\n"
    "                self.set_font(self.default_font, \"\", _fsize)\n"
    "                self.set_xy(x=_x + 0.5, y=_y)\n"
    "                self.cell(w=_w_lbl - 0.5, h=_lh, text=_lbl, align=\"L\", border=0)\n"
    "                self.set_font(self.default_font, \"B\", _fsize)\n"
    "                self.cell(w=_w_val - 0.5, h=_lh, text=_val, align=\"R\", border=0)\n"
    "        _n_rows_d = (_n_dup + _cols - 1) // _cols if _n_dup > 0 else 1\n"
    "        self.set_xy(x=_base_x, y=_base_y + _n_rows_d * 3 * _lh)"
)

# Regex: estado atual — "label+valor" COM rect (ultima versao aplicada)
DUP_PATTERN_CURRENT = (
    r"        # Renderiza duplicatas: label \+ valor na mesma linha.*?"
    r"self\.set_xy\(x=_base_x, y=_base_y \+ _n_rows_d \* 3 \* _lh\)"
)

# Regex: estado intermediario — DanfeBasicField
DUP_PATTERN = (
    r"        # Renderiza duplicatas como campos rotulados.*?"
    r"self\.set_xy\(x=_base_x, y=_base_y \+ _n_rows \* 3 \* DEFAULT_FIELD_HEIGHT\)"
)

# Regex: versao original da biblioteca (celulas horizontais)
DUP_PATTERN_ORIG = (
    r"        self\.set_font\(\s*\n\s*self\.default_font.*?FONT_DUPLICATES.*?\n        \)\n"
    r"        dups_text.*?"
    r"            self\.x = old_x  # fix start left position"
)


def main():
    print("Aplicando patches na biblioteca brazilfiscalreport...\n")
    base = encontrar_base()

    danfe_py = os.path.join(base, "danfe.py")

    # ------------------------------------------------------------------
    # Patches simples (substituicao exata)
    # ------------------------------------------------------------------
    patches_danfe = [
        # Patch 1: altura DADOS ADICIONAIS dinamica (a partir de 20, 65 ou 90mm fixos)
        (
            ALTURA_OLD_TMPL.format(valor=20),
            ALTURA_NEW,
            "Altura DADOS ADICIONAIS dinamica (era 20mm)",
        ),
        (
            ALTURA_OLD_TMPL.format(valor=65),
            ALTURA_NEW,
            "Altura DADOS ADICIONAIS dinamica (era 65mm)",
        ),
        (
            ALTURA_OLD_TMPL.format(valor=90),
            ALTURA_NEW,
            "Altura DADOS ADICIONAIS dinamica (era 90mm)",
        ),
        # Patch 1-mig: migra medicao da altura (v1.1.0) p/ Times regular 8pt
        (
            "            self.set_font(\n"
            "                self.default_font, \"B\", self.get_font_size(\"FONT_SIZE_CONT\", True)\n"
            "            )\n"
            "            _lines_ad = self.multi_cell(\n",
            "            # Mede com a tipografia do modelo: Times regular 8pt\n"
            "            self.set_font(self.default_font, \"\", 8)\n"
            "            _lines_ad = self.multi_cell(\n",
            "Medicao altura DADOS ADICIONAIS: Times regular 8pt",
        ),
        # Patch 1-cont-a: continuacao nas areas de produtos com mesma tipografia
        (
            '                description="CONTINUAÇÃO DAS INFORMAÇÕES COMPLEMENTARES",\n'
            "                content=additional_data,\n"
            "                h=h,\n",
            '                description="CONTINUAÇÃO DAS INFORMAÇÕES COMPLEMENTARES",\n'
            "                content=additional_data,\n"
            '                type="info_complementares",\n'
            "                h=h,\n",
            "Continuacao (produtos): tipografia info_complementares",
        ),
        # Patch 1-cont-b: continuacao em paginas seguintes com mesma tipografia
        (
            '                    description="CONTINUAÇÃO INFORMAÇÕES COMPLEMENTARES",\n'
            "                    content=additional_data,\n"
            "                ),\n",
            '                    description="CONTINUAÇÃO INFORMAÇÕES COMPLEMENTARES",\n'
            "                    content=additional_data,\n"
            '                    type="info_complementares",\n'
            "                ),\n",
            "Continuacao (pag. seguintes): tipografia info_complementares",
        ),
        # Patch 2: fonte tabela de produtos
        (
            'self.default_font, "", self.get_font_size("PRODUCT_DESCRIPTION", True)',
            'self.default_font, "", self.get_font_size("FONT_SIZE_DESC")',
            "Fonte produtos: PRODUCT_DESCRIPTION -> FONT_SIZE_DESC (5pt fixo)",
        ),
        # Patch 3: valores monetarios dos produtos em negrito
        (
            "                    row.cell(text=value, align=align, v_align=VAlign.T)",
            '                    _bold = FontFace(emphasis="BOLD") if i in monetary_fields_index else None\n'
            "                    row.cell(text=value, align=align, v_align=VAlign.T, style=_bold)",
            "Valores monetarios dos produtos em negrito",
        ),
        # Patch 4a: titulo "FATURA / DUPLICATAS" -> "FATURA / DUPLICATA"
        (
            'description="FATURA / DUPLICATAS"',
            'description="FATURA / DUPLICATA"',
            "Titulo: DUPLICATAS -> DUPLICATA",
        ),
        # Patch 5a: tabela de produtos — sem bordas automaticas (desenhadas manualmente)
        (
            "        with self.table(\n"
            '            col_widths=fixed_col_widths, line_height=3, width=self.edw, align="R"\n'
            "        ) as table:",
            "        from fpdf.enums import TableBordersLayout as _TBL\n"
            "        _y_tbl_top = self.get_y()\n"
            "        with self.table(\n"
            '            col_widths=fixed_col_widths, line_height=3, width=self.edw, align="R",\n'
            "            borders_layout=_TBL.NONE,\n"
            "        ) as table:",
            "Tabela produtos: bordas desativadas (manuais)",
        ),
        # Patch 5a-fix: atualiza NO_HORIZONTAL_LINES -> NONE (arquivo ja parcialmente corrigido)
        (
            "        from fpdf.enums import TableBordersLayout as _TBL\n"
            "        with self.table(\n"
            '            col_widths=fixed_col_widths, line_height=3, width=self.edw, align="R",\n'
            "            borders_layout=_TBL.NO_HORIZONTAL_LINES,\n"
            "        ) as table:",
            "        from fpdf.enums import TableBordersLayout as _TBL\n"
            "        _y_tbl_top = self.get_y()\n"
            "        with self.table(\n"
            '            col_widths=fixed_col_widths, line_height=3, width=self.edw, align="R",\n'
            "            borders_layout=_TBL.NONE,\n"
            "        ) as table:",
            "Tabela produtos: NO_HORIZONTAL_LINES -> NONE",
        ),
        # Patch 5b: area vazia apos produtos — linhas de coluna ate o final do quadro
        (
            "            self.rect(x=self.x, y=self.y, w=self.edw, h=h)",
            "            _px = self.x\n"
            "            _py = self.y\n"
            "            self.line(x1=_px, y1=_py, x2=_px, y2=_py + h)\n"
            "            self.line(x1=_px + self.edw, y1=_py, x2=_px + self.edw, y2=_py + h)\n"
            "            self.line(x1=_px, y1=_py + h, x2=_px + self.edw, y2=_py + h)\n"
            "            _xc = _px\n"
            "            for _cw in fixed_col_widths[:-1]:\n"
            "                _xc += _cw\n"
            "                self.line(x1=_xc, y1=_py, x2=_xc, y2=_py + h)",
            "Area vazia: linhas de coluna ate final do quadro",
        ),
        # Patch 5c: apos tabela, desenha bordas externas + separador do cabecalho manualmente
        (
            "        # restore x position\n"
            "        self.x = x_before\n",
            "        _y_tbl_bot = self.get_y()\n"
            "        # restore x position\n"
            "        self.x = x_before\n"
            "        self.line(x1=x_before, y1=_y_tbl_top, x2=x_before + self.edw, y2=_y_tbl_top)\n"
            "        self.line(x1=x_before, y1=_y_tbl_top + 3, x2=x_before + self.edw, y2=_y_tbl_top + 3)\n"
            "        self.line(x1=x_before, y1=_y_tbl_top, x2=x_before, y2=_y_tbl_bot)\n"
            "        self.line(x1=x_before + self.edw, y1=_y_tbl_top, x2=x_before + self.edw, y2=_y_tbl_bot)\n"
            "        _cx = x_before\n"
            "        for _cw in fixed_col_widths[:-1]:\n"
            "            _cx += _cw\n"
            "            self.line(x1=_cx, y1=_y_tbl_top, x2=_cx, y2=_y_tbl_bot)\n",
            "Bordas externas + separador cabecalho da tabela de produtos",
        ),
    ]

    patch_arquivo(danfe_py, patches_danfe, "danfe.py")

    # Patches 4b/c/d: formato duplicatas — tenta em cascata (mais recente primeiro)
    for _pat, _desc in [
        (DUP_PATTERN_CURRENT, "Duplicatas: remove bordas internas"),
        (DUP_PATTERN,         "Duplicatas: formato compacto (a partir de DanfeBasicField)"),
        (DUP_PATTERN_ORIG,    "Duplicatas: formato compacto (a partir do original)"),
    ]:
        if patch_regex(danfe_py, _pat, DUP_NEW, _desc, "danfe.py"):
            break

    # ------------------------------------------------------------------
    # danfe_basic_field.py — conteudo em negrito + info_complementares
    # ------------------------------------------------------------------
    basic_py = os.path.join(base, "danfe_basic_field.py")

    # Novo bloco de selecao de fonte do conteudo:
    # - info_complementares: Times regular 8pt (tipografia do modelo da empresa)
    # - demais campos: negrito (como antes)
    _CONT_NEW = (
        '        elif self.type == "info_complementares":\n'
        "            # Tipografia do modelo da empresa: Times regular 8pt\n"
        '            pdf.set_font(pdf.default_font, "", 8)\n'
        '            align = "L"\n'
        "        else:\n"
        '            pdf.set_font(pdf.default_font, "B", font_size_cont)\n'
        '            align = "R" if self.type == "number" else "L"'
    )

    patches_basic = [
        # a partir do original (conteudo regular)
        (
            "        else:\n"
            '            pdf.set_font(pdf.default_font, "", font_size_cont)\n'
            '            align = "R" if self.type == "number" else "L"',
            _CONT_NEW,
            "Conteudo: negrito + info_complementares regular 8pt (do original)",
        ),
        # a partir do estado ja patcheado (conteudo em negrito)
        (
            "        else:\n"
            '            pdf.set_font(pdf.default_font, "B", font_size_cont)\n'
            '            align = "R" if self.type == "number" else "L"',
            _CONT_NEW,
            "Conteudo: info_complementares regular 8pt (do estado negrito)",
        ),
        # rotulo do campo info_complementares: 6pt (como o modelo)
        (
            "        # Description Cell\n"
            '        pdf.set_font(pdf.default_font, "", font_size_desc)',
            "        # Description Cell (info_complementares: rotulo 6pt como o modelo)\n"
            '        if self.type == "info_complementares":\n'
            "            font_size_desc = 6\n"
            '        pdf.set_font(pdf.default_font, "", font_size_desc)',
            "Rotulo info_complementares: 6pt",
        ),
    ]

    patch_arquivo(basic_py, patches_basic, "danfe_basic_field.py")

    # ------------------------------------------------------------------
    # Limpar cache .pyc
    # ------------------------------------------------------------------
    limpar_cache(base)
    print("\nPronto.")


if __name__ == "__main__":
    main()
