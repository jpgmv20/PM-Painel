@echo off
setlocal

echo ========================================================
echo Instalacao automatica de Kivy para Windows
echo ========================================================

REM Verifica Python instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Python nao encontrado.
    echo Por favor instale o Python 3.8 - 3.13 pelo site https://www.python.org
    echo E marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo.
echo Python encontrado:
python --version

echo.
echo Atualizando pip, setuptools e virtualenv...
python -m pip install --upgrade pip setuptools virtualenv

echo.
echo --- Criando ambiente virtual kivy_venv ---
python -m venv kivy_venv

echo.
echo --- Ativando ambiente virtual ---
call kivy_venv\Scripts\activate

if "%VIRTUAL_ENV%"=="" (
    echo ERRO: Nao foi possivel ativar o ambiente virtual.
    pause
    exit /b 1
)

echo.
echo Ambiente virtual ativado: %VIRTUAL_ENV%

echo.
echo --- Instalando Kivy e exemplos ---
python -m pip install "kivy[full, tuio]" kivy_examples

echo.
echo Instalacao de Kivy concluida.
echo Agora voce pode testar o import do Kivy.

echo.
echo Teste rapido: import kivy
python - <<END
try:
    import kivy
    print("Kivy importado com sucesso! Versao:", kivy.__version__)
except Exception as e:
    print("Erro ao importar Kivy:", e)
END

echo.
echo ========================================================
echo Para ativar o ambiente depois:
echo    cd %cd%
echo    kivy_venv^Scripts^activate
echo ========================================================
pause