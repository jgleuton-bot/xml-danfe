# xml-danfe

Conversor de XML NF-e para DANFE PDF, com formatação personalizada para notas fiscais de combustível.

## O que faz

- Pergunta, em janelas de seleção, qual a pasta com os XMLs a converter e em qual pasta salvar os DANFEs gerados
- Lê todos os arquivos `.xml` de NF-e (v4.00) da pasta escolhida
- Gera um PDF DANFE para cada nota, nomeado automaticamente:
  `AAAA-MM-DD_RazaoSocial(15chars)_NF_NumeroNota_R$Valor.pdf`
- Injeta dados de **ICMS ST** no campo de descrição do produto (`infAdProd`)
- Aplica patches de layout na biblioteca `brazilfiscalreport`:
  - Campo **DADOS ADICIONAIS** com altura dinâmica (ajustada ao texto, mín. 20 mm / máx. 90 mm), alinhado ao rodapé da página — a tabela de produtos preenche todo o espaço restante
  - Tipografia de **INFORMAÇÕES COMPLEMENTARES** igual ao modelo da empresa: conteúdo Times regular 8 pt, rótulo 6 pt
  - Fonte da tabela de produtos reduzida e fixa (5 pt)
  - Valores monetários em **negrito**
  - Seção **FATURA / DUPLICATA** em formato compacto (número, vencimento e valor inline)
  - Tabela de produtos com bordas de coluna estendidas até DADOS ADICIONAIS, sem linhas horizontais entre itens

## Requisitos

- Windows com Python 3.x instalado
- Conexão com internet (para instalação automática da dependência)

A dependência é instalada automaticamente na primeira execução:

```
brazilfiscalreport >= 0.7.8
```

## Estrutura de arquivos

```
XMLDanfe/
├── executar.bat          # Script principal — executa tudo com duplo clique
├── xml_para_danfe.py     # Conversor XML → DANFE PDF
├── patch_danfe_lib.py    # Corrige o layout da biblioteca brazilfiscalreport
└── versionar.bat         # Commit + push da versão atual para o GitHub
```

## Como usar

1. Dê duplo clique em **`executar.bat`**
2. Na primeira janela, selecione a pasta com os arquivos `.xml` das NF-e
3. Na segunda janela, selecione a pasta onde salvar os DANFEs (PDF)
4. O andamento é exibido no terminal em tempo real e também gravado em `log_execucao.txt`

Ou execute diretamente pelo terminal:

```bat
python patch_danfe_lib.py
python xml_para_danfe.py                      :: abre as janelas de seleção
python xml_para_danfe.py C:\xmls              :: saída em C:\xmls\DANFE_PDF
python xml_para_danfe.py C:\xmls C:\pdfs      :: entrada e saída indicadas
```

## Detalhes dos patches (`patch_danfe_lib.py`)

Os patches modificam diretamente o código-fonte da biblioteca instalada, de forma idempotente (podem ser executados múltiplas vezes sem efeito colateral).

| # | Arquivo | Alteração |
|---|---------|-----------|
| 1 | `danfe.py` | Altura de DADOS ADICIONAIS dinâmica: ajustada ao texto (mín. 20 mm, máx. 90 mm), bloco alinhado ao rodapé; produtos preenchem o restante |
| 2 | `danfe.py` | Fonte da tabela de produtos: fixa em 5 pt |
| 3 | `danfe.py` | Valores monetários dos produtos em negrito |
| 4 | `danfe.py` | Seção FATURA/DUPLICATA: título singular + formato compacto |
| 5 | `danfe.py` | Tabela de produtos: bordas manuais (colunas + borda externa) |
| 6 | `danfe_basic_field.py` | Conteúdo dos campos em negrito; INFORMAÇÕES COMPLEMENTARES em Times regular 8 pt com rótulo 6 pt |

## Versão

**v1.4.0** — junho/2026

- v1.4.0: andamento exibido no terminal em tempo real (espelhado em `log_execucao.txt`)
- v1.3.0: seleção das pastas de entrada (XMLs) e saída (PDFs) por janelas de diálogo
- v1.2.0: INFORMAÇÕES COMPLEMENTARES com tipografia do modelo da empresa (Times regular 8 pt, rótulo 6 pt)
- v1.1.0: DADOS ADICIONAIS com altura dinâmica alinhado ao rodapé; produtos ocupam o espaço restante
- v1.0.0: versão inicial
