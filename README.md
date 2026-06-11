# xml-danfe

Conversor de XML NF-e para DANFE PDF, com formatação personalizada para notas fiscais de combustível.

## O que faz

- Lê todos os arquivos `.xml` de NF-e (v4.00) de uma pasta
- Gera um PDF DANFE para cada nota, nomeado automaticamente:
  `AAAA-MM-DD_RazaoSocial(15chars)_NF_NumeroNota_R$Valor.pdf`
- Injeta dados de **ICMS ST** no campo de descrição do produto (`infAdProd`)
- Aplica patches de layout na biblioteca `brazilfiscalreport`:
  - Altura do campo **DADOS ADICIONAIS** ampliada (20 mm → 90 mm)
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
├── *.xml                 # Arquivos NF-e de entrada (não versionados)
└── DANFE_PDF/            # PDFs gerados (não versionados)
```

## Como usar

1. Copie os arquivos `.xml` das NF-e para a pasta do projeto
2. Dê duplo clique em **`executar.bat`**
3. Os PDFs são gerados em `DANFE_PDF/`
4. O log de execução fica em `log_execucao.txt`

Ou execute diretamente pelo terminal:

```bat
python patch_danfe_lib.py
python xml_para_danfe.py
```

## Detalhes dos patches (`patch_danfe_lib.py`)

Os patches modificam diretamente o código-fonte da biblioteca instalada, de forma idempotente (podem ser executados múltiplas vezes sem efeito colateral).

| # | Arquivo | Alteração |
|---|---------|-----------|
| 1 | `danfe.py` | Altura de DADOS ADICIONAIS: 20 mm → 90 mm |
| 2 | `danfe.py` | Fonte da tabela de produtos: fixa em 5 pt |
| 3 | `danfe.py` | Valores monetários dos produtos em negrito |
| 4 | `danfe.py` | Seção FATURA/DUPLICATA: título singular + formato compacto |
| 5 | `danfe.py` | Tabela de produtos: bordas manuais (colunas + borda externa) |
| 6 | `danfe_basic_field.py` | Conteúdo dos campos em negrito |

## Versão

**v1.0.0** — junho/2026
