@echo off
cd /d "%~dp0"

echo ============================================
echo  Versionando v1.4.0 e push para o GitHub
echo ============================================
echo.

git add README.md .gitignore executar.bat xml_para_danfe.py patch_danfe_lib.py git_init_push.bat versionar.bat

git commit -m "v1.4.0 - log em tempo real no terminal; selecao de pastas; DADOS ADICIONAIS dinamico no rodape; tipografia do modelo"

git tag v1.4.0 2>nul

git push origin main --tags

echo.
if %ERRORLEVEL% EQU 0 (
    echo [OK] Versao publicada com sucesso!
) else (
    echo [ERRO] Verifique autenticacao ou status do repositorio.
)
echo.
pause
