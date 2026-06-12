@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set LOG=%~dp0log_execucao.txt

echo Execucao iniciada em %date% %time% > "%LOG%"

echo ============================================
echo  Conversor XML NF-e para DANFE PDF
echo ============================================
echo.
echo [1/3] Instalando/verificando dependencia...
pip install brazilfiscalreport
echo.
echo [2/3] Corrigindo biblioteca (layout DANFE)...
python -u "%~dp0patch_danfe_lib.py"
echo.
echo [3/3] Convertendo XMLs (selecione as pastas nas janelas)...
python -u "%~dp0xml_para_danfe.py"
echo.
echo ============================================
echo  Concluido. Log completo em log_execucao.txt
echo ============================================
pause
