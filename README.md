# PM-Painel

Aplicação em Kivy/KivyMD para apoiar o estudo das disciplinas do curso de Informática, mantendo os atalhos de serviços, configurações persistentes e integrações auxiliares que já existiam no painel.

## Visão geral

O projeto está organizado em camadas:

- `main.py` inicializa a aplicação e monta as telas.
- `model/` concentra as telas e widgets de comportamento.
- `service/` concentra as integrações com navegador, login, sessão, Git Bash e preferências.
- `view/` contém as regras `KV` da interface.
- `devtools/` reúne a infraestrutura do ambiente de desenvolvimento.
- `assets/` guarda imagens, ícones e fontes.

## Diagrama de classes (lista)

A estrutura do projeto pode ser entendida por camadas, com herança e composição entre telas, widgets e serviços:

### 1. Camada de aplicação

- `MeuApp` (`main.py`): aplicação principal do KivyMD; monta as telas, inicializa serviços, gerencia tema, sessão, autoatualização e recursos do Windows.
- `TelaInicial` (`main.py`): tela de boas-vindas que redireciona para a autenticação.

### 2. Camada de telas e widgets da interface

- `LayoutFundo` (`model/componentes.py`): base visual reutilizável para todas as telas; aplica fundo gradiente e adaptações de tema.
- `MenuPerfil` (`model/componentes.py`): menu suspenso com ações de perfil, logout e saída.
- `FotoPerfil` (`model/componentes.py`): botão/visualização de imagem do perfil do usuário.
- `Cabecalho` (`model/componentes.py`): cabeçalho da interface com título, perfil e ações de navegação.
- `Rodape` (`model/componentes.py`): rodapé com status de conexão e versão do app.
- `CardMenu` (`model/componentes.py`): cartão de navegação reutilizável para menus e atalhos.
- `BotaoHover` (`model/componentes.py`): botão com efeito hover.
- `BotaoAcao` (`model/componentes.py`): botão de ação especial, herdado de `BotaoHover`.
- `IconeUI` (`model/componentes.py`): ícone visual usado em componentes da interface.
- `CampoTexto` (`model/componentes.py`): campo de entrada configurado para uso no painel.
- `TelaLogin` (`model/login.py`): tela de autenticação com login local e Google.
- `TelaPrincipal` (`model/home.py`): tela principal com atalhos, navegação e integração ao navegador.
- `TelaConfiguracoes` (`model/configuracoes.py`): tela de ajustes do usuário e do sistema.
- `ConfiguracaoOpcao` (`model/configuracoes.py`): widget de opção de configuração.
- `ServicoOpcao` (`model/configuracoes.py`): widget de serviço/configuração relacionado.
- `TelaMaterias` (`model/tela_materias.py`): tela de matérias e conteúdos acadêmicos.
- `TeamCard` (`model/tela_materias.py`): card de equipe ou matéria com comportamento de botão.
- `TelaEquipe` (`model/tela_materias.py`): extensão da tela de matérias para visão de equipe.
- `TelaUsuarios` (`model/usuarios.py`): gestão de usuários e permissões locais.
- `TelaExtensoes` (`model/extensoes.py`): administração e execução de extensões.
- `TelaPerfil` (`model/perfil.py`): perfil do usuário e suas informações.
- `TelaPraticas` (`model/praticas.py`): laboratório de práticas e simuladores.
- `EditorCircuito` (`model/praticas.py`): editor de circuito para aulas práticas.
- `IndicadorSinal` (`model/praticas.py`): indicador visual de sinal/estado.
- `LaboratorioEnderecoIP` (`model/praticas_redes.py`): laboratório de redes com endereçamento IP.
- `LaboratorioDocker` (`model/praticas_redes.py`): dois terminais xterm.js ligados a shells Bash nos containers Debian.

### 3. Camada de domínio e entidades

- `Conteudo` (`model/materias.py`): conteúdo didático de uma matéria.
- `Comentario` (`model/materias.py`): comentário em publicação ou tópico.
- `Publicacao` (`model/materias.py`): publicação acadêmica ou informativa vinculada a uma matéria.
- `ArquivoCompartilhado` (`model/materias.py`): arquivo compartilhado dentro de uma disciplina.
- `Trabalho` (`model/materias.py`): tarefa ou atividade acadêmica.
- `Topico` (`model/materias.py`): tema do conteúdo pedagógico.
- `Materia` (`model/materias.py`): entidade principal que agrega tópicos, publicações, arquivos e trabalhos.
- `ResultadoCircuito` (`model/praticas.py`): resultado de execução do circuito simulado.
- `SimuladorLogico` (`model/praticas.py`): lógica de simulação do ambiente prático.

### 4. Camada de serviços e integrações

- `SettingsStore` (`service/settings.py`): armazenamento persistente de preferências do usuário em JSON.
- `PermissionService` (`service/permissoes.py`): controle de papéis e permissões.
- `Papel` (`service/permissoes.py`): enumeração para perfis como aluno, professor e moderador.
- `LocalUserStore` (`service/login/users.py`): repositório local de usuários e senhas.
- `AuthSession` (`service/login/session.py`): sessão autenticada em memória.
- `SessionManager` (`service/login/session.py`): gestão de autenticação e sessão offline.
- `AuthenticationService` (`service/login/authentication.py`): caso de uso de login, logout e recuperação de sessão.
- `GoogleAuth` (`service/login/google_auth.py`): autenticação via OAuth com Google.
- `MateriasService` (`service/materias.py`): operações relacionadas às matérias e conteúdos acadêmicos.
- `ExtensionsService` (`service/extensions.py`): catálogo de extensões instaláveis.
- `InternetService` (`service/network.py`): verificação de conectividade.
- `BrowserManager` (`service/web/browser.py`): gerenciamento de navegador com perfil descartável.
- `TerminalWebServer` (`service/web_terminal.py`): servidor local protegido para a interface xterm.js e as sessões WebSocket dos terminais Docker.
- `OAuthCallbackServer` (`service/web/oauth_callback.py`): servidor local para callback do OAuth.
- `GitBashManager` (`service/git_bash.py`): abertura do terminal Git Bash com perfil temporário.
- `DockerNetworkLab` (`service/network_lab_docker.py`): criação e encerramento do laboratório Docker de Redes I.
- `UpdateService` (`service/updates.py`): atualização automática do painel.
- `WindowsStartupService` (`service/windows_startup.py`): integração com inicialização do Windows.
- `WindowsTrayService` (`service/windows_tray.py`): integração com bandeja do sistema.

### 5. Camada de desenvolvimento e infraestrutura

- `DevelopmentConfig` (`devtools/config.py`): configurações do ambiente de desenvolvimento.
- `Logger` (`devtools/logger.py`): logging do projeto.
- `EventBus` (`devtools/events.py`): sistema de eventos para execução do ambiente.
- `CommandManager` (`devtools/commands.py`): gestão de comandos do devtools.
- `PluginManager` (`devtools/plugins.py`): carregamento de plugins.
- `DevelopmentConsole` (`devtools/console.py`): console de apoio ao desenvolvimento.
- `ProjectWatcher` / `FileWatcher` (`devtools/watcher.py`): observação de alterações em arquivos.
- `ProcessManager` (`devtools/process.py`): controle de processos auxiliares.
- `HotReloadManager` (`devtools/hotreload.py`): recarga em tempo real.
- `DevelopmentRunner` (`devtools/runner.py`): orquestração do ambiente de execução.
- `Profiler` (`devtools/profiler.py`): suporte a profiling.
- `ProjectValidator` (`devtools/validator.py`): validação de entradas e ambiente.
- `DevelopmentState` (`devtools/state.py`): armazenamento do estado compartilhado.
- `WidgetManager` (`devtools/widgets.py`): gestão de widgets auxiliares.

### Estrutura de relacionamento de alto nível

- `MeuApp` compõe `SettingsStore`, `SessionManager`, `AuthenticationService`, `BrowserManager`, `GitBashManager`, `MateriasService` e `ExtensionsService`.
- `TelaLogin`, `TelaPrincipal`, `TelaMaterias`, `TelaConfiguracoes`, `TelaUsuarios`, `TelaExtensoes`, `TelaPerfil` e `TelaPraticas` herdam/consomem `LayoutFundo` e widgets reutilizáveis.
- `Materia` agrega `Topico`, `Publicacao`, `ArquivoCompartilhado` e `Trabalho`.
- `AuthSession` e `PermissionService` controlam o estado do usuário e suas permissões durante a navegação.

## Funcionalidades acadêmicas e contas

- O acesso pode ser feito por conta local de aluno ou pela autenticação Google já existente. O cadastro livre cria apenas contas de aluno.
- Professores e moderadores são cadastrados pelo moderador. O moderador associa professores às matérias e pode suspender ou reativar contas.
- Um professor edita conteúdo apenas nas matérias associadas à sua conta. O moderador administra matérias e conteúdos de todo o painel.
- Matérias, tópicos, publicações, arquivos, trabalhos, extensões e preferências ficam armazenados localmente. O último perfil autenticado pode ser restaurado offline por até sete dias; sair da conta apaga esse passe.
- O modo offline bloqueia login/cadastro, gestão de usuários, alteração de matérias e instalação das extensões marcadas como dependentes de rede. O conteúdo já salvo localmente continua disponível.
- Extensões Python podem ser enviadas para revisão. Professores e moderadores aprovam; depois da instalação, o usuário confirma antes de executar o arquivo.

### Limites atuais de sincronização e distribuição

O repositório não contém serviço ou endpoint de servidor. Por isso, contas, matérias e extensões criadas no painel ficam neste computador e não são compartilhadas automaticamente entre dispositivos; as ações que exigem internet são sinalizadas e bloqueadas sem conexão, mas uma camada de sincronização ainda depende de um backend. A integração de compiladores citada no relatório permanece uma possibilidade futura.

O projeto e os dados foram preparados para usar o diretório de dados fornecido pelo Kivy em sistemas que não sejam Windows. A distribuição existente está configurada para Windows; não há neste repositório um fluxo validado para gerar APK ou pacote iOS, e as integrações de Chrome e Git Bash são específicas do desktop.

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

### Laboratório de Redes I com Docker

A atividade inicia PC-A e PC-B em containers Debian Trixie slim, cada um com Bash, na mesma rede bridge Docker interna. Depois de iniciar a rede, **Abrir terminais interativos** abre uma janela de aplicativo do Chrome ou Edge com dois painéis xterm.js. Cada painel mantém um shell TTY próprio, com entrada, saída e redimensionamento em tempo real; os containers compartilham a sub-rede e se encontram pelos nomes `pc-a` e `pc-b`. A sessão TTY usa o mesmo contexto Docker selecionado pelo CLI. A rede Docker não publica portas nem encaminha tráfego para outras redes. A interface web e a ponte WebSocket ficam vinculadas a `127.0.0.1` e usam um token aleatório por execução.

O terminal usa os arquivos locais do xterm.js empacotados em `assets/web-terminal`, sem baixar scripts ao abrir a atividade. A janela Chromium é separada da janela Kivy porque este projeto ainda não incorpora um WebView dentro da interface principal.

Requisitos e uso:

- Docker Desktop instalado e iniciado, usando containers Linux.
- Google Chrome ou Microsoft Edge instalado para mostrar a interface xterm.js.
- Dependências Python `docker` e `websockets` instaladas; `installKivy.bat` instala essas dependências junto ao Kivy.
- Na primeira execução, é necessário acesso à internet para baixar Debian Trixie slim e instalar Bash, `iproute2`, `iputils-ping`, `dnsutils`, `traceroute`, `netcat`, `nmap`, `tcpdump`, `curl` e `mtr`.
- Os dois endereços precisam usar a mesma sub-rede IPv4. Exemplo: `192.168.10.10/24` e `192.168.10.20/24`.
- Use `ping -c 4 pc-b` no PC-A ou `ping -c 4 pc-a` no PC-B para confirmar a comunicação.
- Cada console mantém um Bash interativo até fechar a janela, encerrar o laboratório ou sair do aplicativo. O diretório inicial é `/tmp`.
- Para ver tráfego, use `timeout 10 tcpdump -ni eth0 icmp`; para sondar portas, use `nmap -sT pc-b`.
- Os containers têm limites de CPU, memória e processos, usam filesystem somente leitura e não compartilham pastas com o computador. Arquivos em `/tmp` existem apenas durante a sessão.
- Clique em **Encerrar laboratório** antes de sair da atividade para remover os containers e a rede. A imagem preparada permanece no Docker para o próximo uso.

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
- `model/login.py`: tela de login Google, login local e cadastro de aluno.
- `model/perfil.py`: visualização e edição do perfil.
- `model/usuarios.py`: gestão local de contas e atribuição de matérias.
- `model/extensoes.py`: envio, aprovação, instalação e execução de extensões locais.

### `service/`

Camada de serviços e integrações.

- `service/__init__.py`: marca o pacote.
- `service/READ.md`: nota geral da camada de serviços.
- `service/settings.py`: armazenamento persistente das preferências em JSON fora da pasta do projeto.
- `service/login/users.py`: contas locais com hash de senha e papéis de acesso.
- `service/login/session.py`: sessão em memória e passe de acesso offline com validade limitada.
- `service/network.py`: verificação de conectividade para ações que dependem da internet.
- `service/extensions.py`: catálogo local de extensões.
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
