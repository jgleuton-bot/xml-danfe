# -*- coding: utf-8 -*-
"""
Cruza as Chaves XML de um CSV com os arquivos XML de uma pasta (e subpastas).
Gera um CSV com as notas que NAO possuem XML correspondente.

Uso: python cruzar_chaves_xml.py
     (abre janelas para selecionar o CSV e a pasta; se nao houver
      interface grafica, pede os caminhos pelo teclado)
"""

import csv
import os
import re
import sys

RE_CHAVE = re.compile(r"\d{44}")


def selecionar_entradas():
    """Pede o CSV e a pasta de XMLs (janela ou teclado)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        csv_path = filedialog.askopenfilename(
            title="Selecione o CSV com a relacao de notas",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not csv_path:
            sys.exit("Nenhum CSV selecionado.")
        pasta = filedialog.askdirectory(
            title="Selecione a pasta com os XML (inclui subpastas)")
        if not pasta:
            sys.exit("Nenhuma pasta selecionada.")
        root.destroy()
    except Exception:
        csv_path = input("Caminho do CSV com a relacao: ").strip().strip('"')
        pasta = input("Pasta com os XML: ").strip().strip('"')
    return csv_path, pasta


def extrair_chave(texto):
    """Extrai a chave de 44 digitos de um texto (ex.: ="3519...")."""
    m = RE_CHAVE.search(re.sub(r"\D", "", texto or ""))
    return m.group(0) if m else None


def chaves_da_pasta(pasta):
    """Varre pasta e subpastas; coleta as chaves pelo NOME do arquivo XML
    (os arquivos sao gravados com a chave de 44 digitos no nome)."""
    chaves = set()
    total_xml = 0
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            if not nome.lower().endswith(".xml"):
                continue
            total_xml += 1
            m = RE_CHAVE.search(nome)
            if m:
                chaves.add(m.group(0))
    return chaves, total_xml


def main():
    csv_path, pasta = selecionar_entradas()

    print(f"\nLendo CSV: {csv_path}")
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        cabecalho = next(leitor)
        try:
            idx_chave = next(i for i, c in enumerate(cabecalho)
                             if "chave" in c.lower())
        except StopIteration:
            sys.exit("Coluna 'Chave XML' nao encontrada no CSV.")
        linhas = [l for l in leitor if l]
    print(f"  {len(linhas)} notas no CSV.")

    print(f"Varrendo XMLs em: {pasta} (e subpastas)...")
    chaves_xml, total_xml = chaves_da_pasta(pasta)
    print(f"  {total_xml} arquivos XML, {len(chaves_xml)} chaves identificadas.")

    faltantes = []
    sem_chave = 0
    for linha in linhas:
        chave = extrair_chave(linha[idx_chave]) if len(linha) > idx_chave else None
        if chave is None:
            sem_chave += 1
            continue
        if chave not in chaves_xml:
            faltantes.append(linha)

    saida = os.path.join(os.path.dirname(os.path.abspath(csv_path)),
                         "chaves_sem_xml.csv")
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(cabecalho)
        escritor.writerows(faltantes)

    print(f"\nResultado:")
    print(f"  Notas com XML encontrado : {len(linhas) - len(faltantes) - sem_chave}")
    print(f"  Notas SEM XML            : {len(faltantes)}")
    if sem_chave:
        print(f"  Linhas sem chave valida  : {sem_chave}")
    print(f"\nArquivo gerado: {saida}")
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
