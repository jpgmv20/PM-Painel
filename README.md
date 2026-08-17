# PM-Painel

Aplicação desktop em Kivy/KivyMD para organizar login, atalhos de serviços, configurações persistentes e integrações auxiliares como navegador temporário e Git Bash isolado.

## Visão geral

O projeto está organizado em camadas:

- `main.py` inicializa a aplicação e monta as telas.
- `model/` concentra as telas e widgets de comportamento.
- `service/` concentra as integrações com navegador, login, sessão, Git Bash e preferências.
- `view/` contém as regras `KV` da interface.
- `devtools/` reúne a infraestrutura do ambiente de desenvolvimento.
- `assets/` guarda imagens, ícones e fontes.

## Como executar

### Aplicação principal

Executa o painel completo:

```bash
python main.py
```

### Ambiente de desenvolvimento

Executa o runner de desenvolvimento:

```bash
python dev.py
```

### Scripts auxiliares no Windows

- `activateKivy.bat`: ativa o ambiente virtual `kivy_venv`.
- `installKivy.bat`: cria o ambiente virtual e instala Kivy.
- `painel.ps1`: menu em PowerShell para rotinas relacionadas ao painel e ao Git.

## Estrutura do projeto

### Arquivos da raiz

- `main.py`: ponto de entrada da aplicação. Carrega os arquivos KV, cria a janela, inicializa serviços e monta as telas.
- `dev.py`: ponto de entrada do ambiente de desenvolvimento.
- `painel.ps1`: script de automação em PowerShell com menus para tarefas relacionadas ao projeto.
- `activateKivy.bat`: script para ativar o ambiente virtual local.
- `installKivy.bat`: script para criar o ambiente virtual e instalar Kivy.
- `LICENSE`: licença do projeto.
- `README.md`: documentação principal do repositório.

### `assets/`

- `assets/fonts/`: fontes usadas pela interface.
- `assets/icon/`: ícones e imagens pequenas usados nos cards, botões e perfis.
	- `README.md`: observações específicas da pasta de ícones.
	- `classroom.png`: ícone do Classroom.
	- `classroom.svg`: versão vetorial do ícone do Classroom.
	- `discord.png`: ícone do Discord.
	- `excel.png`: ícone do Excel.
	- `git.png`: ícone usado para Git Bash.
	- `github.png`: ícone do GitHub.
	- `github.svg`: versão vetorial do ícone do GitHub.
	- `google.png`: ícone do Google.
	- `google.svg`: versão vetorial do ícone do Google.
	- `google_drive.png`: ícone do Google Drive.
	- `onedrive.png`: ícone do OneDrive.
	- `outlook.png`: ícone do Outlook.
	- `teams.png`: ícone do Teams.
	- `user_icon.png`: imagem padrão de perfil do usuário.
	- `word.png`: ícone do Word.
	- `youtube.png`: ícone do YouTube.
	- `youtube.svg`: versão vetorial do ícone do YouTube.
- `assets/img/`: imagens de apoio e ilustrações da interface.
	- `book.png`: imagem auxiliar.
	- `config.jpg`: imagem usada como cartão/ilustração de configuração.
	- `config.png`: versão em PNG da imagem de configuração.
	- `Main_screan.png`: captura da tela principal.
	- `pratic.png`: imagem auxiliar.

### `core/`

- `core/__init__.py`: marca o pacote Python.
- `core/READ.md`: nota/documentação auxiliar da camada central.

### `data/`

- `data/READ.md`: documentação auxiliar para dados do projeto.

### `database/`

- `database/READ.md`: documentação auxiliar para a camada de banco de dados.

### `docs/`

- `docs/client_google_desktop.json`: credencial OAuth do Google usada no login desktop.

### `model/`

Camada de telas e widgets de comportamento.

- `model/__init__.py`: marca o pacote.
- `model/componentes.py`: widgets reutilizáveis da interface, como cabeçalho, rodapé, layout base, menu de perfil e cartão de menu.
- `model/configuracoes.py`: tela de configurações e widgets de opções reutilizáveis.
- `model/home.py`: tela principal, atalhos de serviços e área do navegador temporário.
- `model/login.py`: tela de login e fluxo visual da autenticação Google.

### `service/`

Camada de serviços e integrações.

- `service/__init__.py`: marca o pacote.
- `service/READ.md`: nota geral da camada de serviços.
- `service/settings.py`: armazenamento persistente das preferências em JSON fora da pasta do projeto.
- `service/git_bash.py`: abre o Git Bash em um perfil temporário e descarta dados ao encerrar.

#### `service/login/`

- `service/login/__init__.py`: marca o pacote.
- `service/login/authentication.py`: caso de uso que coordena login e logout sem acoplar a interface.
- `service/login/google_auth.py`: fluxo OAuth com Google e consulta de perfil do usuário.
- `service/login/session.py`: sessão autenticada mantida somente em memória.

#### `service/web/`

- `service/web/__init__.py`: marca o pacote.
- `service/web/browser.py`: navegador Chromium temporário com perfil descartável.
- `service/web/oauth_callback.py`: servidor local que recebe o retorno do OAuth.

### `devtools/`

Infraestrutura do ambiente de desenvolvimento.

- `devtools/__init__.py`: marca o pacote.
- `devtools/commands.py`: comandos disponíveis no ambiente de desenvolvimento.
- `devtools/config.py`: configuração do ambiente de desenvolvimento.
- `devtools/console.py`: suporte a console e saída de texto.
- `devtools/events.py`: sistema de eventos do runner.
- `devtools/hotreload.py`: suporte a recarregamento em desenvolvimento.
- `devtools/logger.py`: logging do ambiente.
- `devtools/plugins.py`: carregamento e gestão de plugins de devtools.
- `devtools/process.py`: controle de processos auxiliares.
- `devtools/profiler.py`: suporte a profiling.
- `devtools/runner.py`: orquestra o ambiente de desenvolvimento.
- `devtools/state.py`: estado compartilhado do ambiente.
- `devtools/validator.py`: validação de entradas e configuração.
- `devtools/watcher.py`: observação de arquivos para atualização automática.
- `devtools/widgets.py`: widgets auxiliares do ambiente.

### `plugins/`

- `plugins/logger_plugin.py`: plugin de logging.
- `plugins/teste.py`: plugin de teste ou exemplo.

### `view/`

Arquivos `KV` da interface.

- `view/componentes.kv`: regras visuais dos componentes reutilizáveis.
- `view/configuracoes.kv`: layout da tela de configurações.
- `view/home.kv`: layout da tela principal.
- `view/login.kv`: layout da tela de login.
- `view/main.kv`: estrutura visual principal da aplicação.

## Pastas de apoio e ambiente

Essas pastas normalmente não precisam de edição direta no fluxo comum de desenvolvimento, mas fazem parte do projeto no workspace.

- `kivy_venv/`: ambiente virtual local com dependências do projeto.
- `logs/`: registros de execução.
- `.pm-logs/` e `.pm_logs/`: diretórios de log auxiliares.
- `.git/`: controle de versão Git.
- `.gitignore`: regras de arquivos ignorados.
- `.idea/`: configurações de IDE.
- `.vscode/`: configurações do VS Code.
- `__pycache__/`: arquivos gerados automaticamente pelo Python.

## Observações

- O projeto usa arquivos `KV` carregados manualmente em `main.py`.
- O login Google depende do arquivo `docs/client_google_desktop.json`.
- O navegador e o Git Bash são abertos com perfis temporários para evitar reaproveitar dados do usuário.