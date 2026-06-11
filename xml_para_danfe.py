"""
Conversor de XML NF-e para DANFE PDF  —  v1.0.0
================================================
Converte todos os arquivos XML de NF-e de uma pasta em DANFEs no formato PDF.
Nome do PDF: AAAA-MM-DD_RAZAOSOCIAL(15)_NF_NroNFe_R$Valor.pdf

Dependencia:
    pip install brazilfiscalreport

Uso:
    python xml_para_danfe.py                  -> processa a pasta onde o script esta
    python xml_para_danfe.py C:/caminho/xmls  -> processa a pasta indicada
"""

__version__ = "1.0.0"

import sys
import io
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Garante saida UTF-8 sem erros mesmo em terminais antigos
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
NF_URI = "http://www.portalfiscal.inf.br/nfe"

ET.register_namespace("", NF_URI)  # serializa sem prefixo nfe:


def _fmt_brl(valor_str: str) -> str:
    """'12345.67' -> '12.345,67'"""
    try:
        v = float(valor_str)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor_str


def injetar_info_icmsst_xml(xml_bytes: bytes) -> bytes:
    """
    Para cada produto do XML que possua dados de ICMS ST ou CEST,
    injeta no campo infAdProd a string:
      pIcmsST=X,XX% vBcIcmsST=X.XXX,XX vIcmsST=X.XXX,XX CEST:XXXXXXX
    Retorna os bytes do XML modificado.
    """
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    modificado = False

    for det in root.findall(f".//{{{NF_URI}}}det"):
        picmsst = vbcst = vicmsst = None

        icms_el = det.find(f".//{{{NF_URI}}}ICMS")
        if icms_el is not None:
            for child in list(icms_el):
                for fname, var in [
                    ("pICMSST", "picmsst"),
                    ("vBCST",   "vbcst"),
                    ("vICMSST", "vicmsst"),
                ]:
                    el = child.find(f"{{{NF_URI}}}{fname}")
                    if el is not None and el.text:
                        if fname == "pICMSST": picmsst = el.text
                        if fname == "vBCST":   vbcst   = el.text
                        if fname == "vICMSST": vicmsst = el.text

        cest_el = det.find(f".//{{{NF_URI}}}CEST")
        cest = cest_el.text if cest_el is not None else None

        # Se não há nenhum dado, pular este det
        if not any([picmsst, vbcst, vicmsst, cest]):
            continue

        partes = []
        if picmsst:
            partes.append(f"pIcmsST={picmsst.replace('.', ',')}%")
        if vbcst:
            partes.append(f"vBcIcmsST={_fmt_brl(vbcst)}")
        if vicmsst:
            partes.append(f"vIcmsST={_fmt_brl(vicmsst)}")
        if cest:
            partes.append(f"CEST:{cest}")

        info_str = "  ".join(partes)

        prod = det.find(f"{{{NF_URI}}}prod")
        if prod is not None:
            infadprod = prod.find(f"{{{NF_URI}}}infAdProd")
            if infadprod is None:
                infadprod = ET.SubElement(prod, f"{{{NF_URI}}}infAdProd")
                infadprod.text = info_str
            else:
                existing = (infadprod.text or "").strip()
                if info_str not in existing:
                    infadprod.text = (existing + "  " + info_str).strip() if existing else info_str
            modificado = True

    if not modificado:
        return xml_bytes

    return ET.tostring(root, encoding="unicode").encode("utf-8")


def instalar_dependencia():
    try:
        import brazilfiscalreport  # noqa: F401
    except ImportError:
        print("Instalando dependencia: brazilfiscalreport...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "brazilfiscalreport"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Instalacao concluida.\n")


def formatar_valor_brl(valor_str: str) -> str:
    """Converte '25549.50' -> 'R$25.549,50'"""
    valor = float(valor_str)
    formatado = f"{valor:,.2f}"               # '25,549.50'
    formatado = formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${formatado}"


def nome_arquivo_pdf(xml_bytes: bytes) -> str:
    """Extrai dados do XML e monta o nome do PDF."""
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))

    def get(xpath):
        el = root.find(xpath, NS)
        return el.text.strip() if el is not None and el.text else ""

    data = get(".//nfe:infNFe/nfe:ide/nfe:dhEmi")[:10]
    razao = get(".//nfe:emit/nfe:xNome")[:15].strip()
    numero = get(".//nfe:infNFe/nfe:ide/nfe:nNF")
    valor = formatar_valor_brl(get(".//nfe:total/nfe:ICMSTot/nfe:vNF"))

    razao = re.sub(r'[<>:"/\\|?*\r\n]', "", razao)

    nome = f"{data}_{razao}_NF_{numero}_{valor}.pdf"
    return nome


def converter_xml_para_danfe(pasta_xml: Path, pasta_saida: Path):
    from brazilfiscalreport.danfe import (
        Danfe, DanfeConfig, FontType, FontSize, ReceiptPosition,
        TaxConfiguration, InvoiceDisplay, Margins, DecimalConfig,
        ProductDescriptionConfig,
    )

    config = DanfeConfig(
        margins=Margins(top=2, right=2, bottom=2, left=2),
        receipt_pos=ReceiptPosition.TOP,
        font_type=FontType.TIMES,
        font_size=FontSize.BIG,
        display_pis_cofins=True,
        tax_configuration=TaxConfiguration.ICMS_ST,
        invoice_display=InvoiceDisplay.DUPLICATES_ONLY,
        infcpl_semicolon_newline=False,
        product_description_config=ProductDescriptionConfig(
            display_anp=False,
            display_branch=False,
            display_additional_info=True,
        ),
        decimal_config=DecimalConfig(
            price_precision=4,
            quantity_precision=4,
        ),
    )

    pasta_saida.mkdir(exist_ok=True)

    xmls = sorted(pasta_xml.glob("*.xml"))
    if not xmls:
        print("Nenhum arquivo XML encontrado na pasta.")
        return 0, 0

    print(f"Encontrados {len(xmls)} arquivos XML.\n")
    sucesso = 0
    erro = 0

    for i, xml_path in enumerate(xmls, start=1):
        try:
            with open(xml_path, "rb") as f:
                xml_bytes = f.read()

            nome_pdf = nome_arquivo_pdf(xml_bytes)
            pdf_path = pasta_saida / nome_pdf

            print(f"[{i:>3}/{len(xmls)}] {xml_path.name}")

            xml_bytes = injetar_info_icmsst_xml(xml_bytes)
            danfe = Danfe(xml=xml_bytes, config=config)
            danfe.output(str(pdf_path))
            print(f"          OK -> {nome_pdf}")
            sucesso += 1

        except Exception as e:
            print(f"[{i:>3}/{len(xmls)}] {xml_path.name}")
            print(f"          ERRO: {e}")
            erro += 1

    return sucesso, erro


def main():
    if len(sys.argv) > 1:
        pasta_xml = Path(sys.argv[1])
    else:
        pasta_xml = Path(__file__).parent

    if not pasta_xml.exists():
        print(f"Pasta nao encontrada: {pasta_xml}")
        sys.exit(1)

    pasta_saida = pasta_xml / "DANFE_PDF"

    print("=" * 60)
    print("  Conversor XML NF-e -> DANFE PDF")
    print("=" * 60)
    print(f"  Entrada : {pasta_xml}")
    print(f"  Saida   : {pasta_saida}")
    print("=" * 60 + "\n")

    instalar_dependencia()

    sucesso, erro = converter_xml_para_danfe(pasta_xml, pasta_saida)

    print("\n" + "=" * 60)
    print(f"  Concluido!  OK: {sucesso}   ERROS: {erro}")
    print(f"  PDFs salvos em: {pasta_saida}")
    print("=" * 60)


if __name__ == "__main__":
    main()
