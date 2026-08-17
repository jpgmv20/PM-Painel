; ============================================================
; PM-Painel - Instalador
; ============================================================

#define MyAppName "PM-Painel"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PM-Painel"
#define MyAppExeName "PM-Painel.exe"

[Setup]

; ------------------------------------------------------------
; Informações do aplicativo
; ------------------------------------------------------------

AppId={{PM-PAINEL-2026-001}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; ------------------------------------------------------------
; Pasta de instalação
; ------------------------------------------------------------

DefaultDirName={autopf}\PM-Painel

DefaultGroupName={#MyAppName}

; ------------------------------------------------------------
; Arquivo final do instalador
; ------------------------------------------------------------

OutputDir=installer
OutputBaseFilename=PM-Painel-Setup

; ------------------------------------------------------------
; Compactação
; ------------------------------------------------------------

Compression=lzma
SolidCompression=yes

; ------------------------------------------------------------
; Arquitetura
; ------------------------------------------------------------

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ------------------------------------------------------------
; Interface
; ------------------------------------------------------------

WizardStyle=modern

; ------------------------------------------------------------
; Desinstalador
; ------------------------------------------------------------

UninstallDisplayName={#MyAppName}
Uninstallable=yes

; ------------------------------------------------------------
; Privacidade / permissões
; ------------------------------------------------------------

PrivilegesRequired=admin

; ------------------------------------------------------------
; Ícone do instalador
; ------------------------------------------------------------

; Se você tiver um .ico do PM-Painel,
; descomente a linha abaixo:

; SetupIconFile=assets\icon\pm_painel.ico


[Languages]

Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"


[Tasks]

; Atalho na área de trabalho
Name: "desktopicon"; \
    Description: "Criar um atalho na Área de Trabalho"; \
    GroupDescription: "Atalhos:"; \
    Flags: unchecked


[Files]

; ============================================================
; COPIA TODA A PASTA GERADA PELO PYINSTALLER
; ============================================================

Source: "dist\PM-Painel\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]

; ============================================================
; MENU INICIAR
; ============================================================

Name: "{group}\PM-Painel"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"


; ============================================================
; ÁREA DE TRABALHO
; ============================================================

Name: "{autodesktop}\PM-Painel"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon


[Run]

; ============================================================
; EXECUTAR PM-PAINEL AO TERMINAR A INSTALAÇÃO
; ============================================================

Filename: "{app}\{#MyAppExeName}"; \
    Description: "Executar o PM-Painel"; \
    Flags: nowait postinstall skipifsilent