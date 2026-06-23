@echo off
setlocal

echo ============================================
echo Abrindo ambiente virtual Kivy
echo ============================================

REM Nome da pasta do ambiente virtual
set VENV_NAME=kivy_venv
set VENV_PATH=%cd%\%VENV_NAME%
set ACTIVATE_PATH=%VENV_PATH%\Scripts\activate.bat

REM Verifica se o Python existe
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Python nao encontrado no PATH.
    echo Instale o Python e marque "Add to PATH".
    pause
    exit /b 1
)

REM Verifica se a pasta do ambiente virtual existe
IF NOT EXIST "%VENV_PATH%" (
    echo.
    echo ERRO: O ambiente virtual "%VENV_NAME%" nao existe.
    echo Certifique-se de estar na pasta correta do projeto.
    pause
    exit /b 1
)

REM Verifica se o script de ativacao existe
IF NOT EXIST "%ACTIVATE_PATH%" (
    echo.
    echo ERRO: Arquivo de ativacao nao encontrado.
    echo Caminho esperado:
    echo %ACTIVATE_PATH%
    pause
    exit /b 1
)

echo.
echo Ambiente encontrado. Ativando...

call "%ACTIVATE_PATH%"

IF "%VIRTUAL_ENV%"=="" (
    echo.
    echo ERRO: Falha ao ativar o ambiente virtual.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Ambiente ativado com sucesso!
echo VIRTUAL_ENV = %VIRTUAL_ENV%
echo ============================================
echo.

REM Mantem o CMD aberto dentro do ambiente
cmd /k

endlocal