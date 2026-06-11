@echo off
set PYTHONIOENCODING=utf-8
set LOG=%~dp0log_execucao.txt
set DANFE_DIR=%~dp0DANFE_PDF

echo Limpando PDFs anteriores... > "%LOG%"
if exist "%DANFE_DIR%" rd /s /q "%DANFE_DIR%"

echo Instalando dependencia... >> "%LOG%"
pip install brazilfiscalreport >> "%LOG%" 2>&1

echo Corrigindo biblioteca (height DADOS ADICIONAIS)... >> "%LOG%"
python -u "%~dp0patch_danfe_lib.py" >> "%LOG%" 2>&1

echo Convertendo XMLs... >> "%LOG%"
python -u "%~dp0xml_para_danfe.py" >> "%LOG%" 2>&1

echo Concluido. >> "%LOG%"
