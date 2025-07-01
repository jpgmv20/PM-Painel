import os
import subprocess
import requests

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nPressione Enter para continuar...")

def get_git_config(key):
    result = subprocess.getoutput(f"git config --global {key}")
    return result.strip()

# ============================
# MENU PRINCIPAL
# ============================

def mostrar_menu():
    while True:
        limpar_tela()
        print("==========================")
        print(" Painel de Controle Pessoal")
        print("==========================")
        print("[1] Git")
        print("[2] Programas")
        print("[3] Sair\n")

        opcao = input("Escolha uma opcao: ")
        match opcao:
            case "1":
                git_menu()
            case "2":
                programas_menu()
            case "3":
                print("Saindo...")
                break
            case _:
                print("Opcao invalida.")
                pause()

# ============================
# MENU GIT
# ============================

def git_menu():
    while True:
        limpar_tela()
        nome = get_git_config("user.name") or "(nao configurado)"
        email = get_git_config("user.email") or "(nao configurado)"

        print("===========================")
        print(" Painel de Controle do Git")
        print("===========================\n")
        print(f"Usuario Git atual: {nome}")
        print(f"Email Git atual: {email}\n")
        print("[1] Download Git")
        print("[2] Login")
        print("[3] Logout")
        print("[4] Ver repositorios")
        print("[5] Clonar repositorio")
        print("[6] Enviar projeto local para o GitHub")
        print("[7] Voltar\n")

        opcao = input("Escolha uma opcao: ")
        if opcao == "1":
            instalar_git()
        elif opcao == "2":
            logar_git()
        elif opcao == "3":
            logout_git()
        elif opcao == "4":
            mostrar_repositorios()
        elif opcao == "5":
            clonar_repositorio()
        elif opcao == "6":
            enviar_projeto()
        elif opcao == "7":
            return
        else:
            print("Opcao invalida.")
            pause()

# ============================
# FUNÇÕES DO GIT
# ============================

def instalar_git():
    print("Baixando e instalando Git...")
    url = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
    destino = os.path.join(os.getenv("TEMP"), "git-installer.exe")
    r = requests.get(url)
    with open(destino, "wb") as f:
        f.write(r.content)
    subprocess.run([destino, "/VERYSILENT"], check=True)
    print("Git instalado com sucesso!")
    pause()

def logar_git():
    nome = input("Digite seu nome de usuario do GitHub: ")
    email = input("Digite seu e-mail para o Git: ")
    token = input("Cole seu token de acesso pessoal (PAT): ")
    subprocess.run(["git", "config", "--global", "user.name", nome])
    subprocess.run(["git", "config", "--global", "user.email", email])
    subprocess.run(["git", "config", "--global", "github.token", token])
    print("\nLogin configurado com sucesso!")
    pause()

def logout_git():
    subprocess.run(["git", "config", "--global", "--unset", "user.name"])
    subprocess.run(["git", "config", "--global", "--unset", "user.email"])
    subprocess.run(["git", "config", "--global", "--unset", "github.token"])
    print("Logout concluido!")
    pause()

def contar_conteudo(url, headers):
    arquivos = 0
    pastas = 0
    try:
        resposta = requests.get(url, headers=headers)
        itens = resposta.json()
        for item in itens:
            if item["type"] == "file":
                arquivos += 1
            elif item["type"] == "dir":
                pastas += 1
                sub_resultado = contar_conteudo(item["url"], headers)
                arquivos += sub_resultado["arquivos"]
                pastas += sub_resultado["pastas"]
    except:
        pass
    return {"arquivos": arquivos, "pastas": pastas}

def mostrar_repositorios():
    usuario = get_git_config("user.name")
    token = get_git_config("github.token")

    if not usuario or not token:
        print("Usuario ou token nao configurado. Faca login primeiro.")
        pause()
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": usuario
    }

    url = "https://api.github.com/user/repos?per_page=100"
    try:
        resposta = requests.get(url, headers=headers)
        repos = resposta.json()
        if not repos:
            print("Nenhum repositorio encontrado.")
        else:
            for repo in repos:
                visibilidade = "[Privado]" if repo["private"] else "[Publico]"
                nome = repo["name"]
                url_conteudo = f"https://api.github.com/repos/{usuario}/{nome}/contents"
                res = contar_conteudo(url_conteudo, headers)
                print(f"\n {nome} {visibilidade} - Arquivos: {res['arquivos']}, Pastas: {res['pastas']}")
    except:
        print("Erro ao acessar repositorios.")
    pause()

def clonar_repositorio():
    usuario = get_git_config("user.name")
    token = get_git_config("github.token")

    if not usuario or not token:
        print("Faca login primeiro.")
        pause()
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": usuario
    }

    url = "https://api.github.com/user/repos?per_page=100"
    resposta = requests.get(url, headers=headers)
    repos = resposta.json()

    if repos:
        print("\nEscolha um repositorio para clonar:")
        for i, repo in enumerate(repos):
            print(f"[{i}] {repo['name']}")
        escolha = input("Numero: ")
        try:
            escolha = int(escolha)
            repo = repos[escolha]["clone_url"]
            destino = input("Caminho da pasta: ")
            subprocess.run(["git", "clone", repo, destino])
            print("Repositorio clonado com sucesso!")
        except:
            print("Erro ao clonar repositório.")
    else:
        print("Nenhum repositorio encontrado.")
    pause()

def enviar_projeto():
    usuario = get_git_config("user.name")
    token = get_git_config("github.token")

    if not usuario or not token:
        print("Faca login primeiro.")
        pause()
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": usuario
    }

    url = "https://api.github.com/user/repos?per_page=100"
    resposta = requests.get(url, headers=headers)
    repos = resposta.json()

    if repos:
        print("\nEscolha o repositorio:")
        for i, repo in enumerate(repos):
            print(f"[{i}] {repo['name']}")
        escolha = input("Numero: ")
        try:
            escolha = int(escolha)
            repo = repos[escolha]
            url_remoto = repo["clone_url"].replace("https://", f"https://{token}@")
            caminho = input("Caminho da pasta local: ")
            os.chdir(caminho)
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"])
                subprocess.run(["git", "remote", "add", "origin", url_remoto])
            else:
                subprocess.run(["git", "remote", "set-url", "origin", url_remoto])
            subprocess.run(["git", "add", "."])
            mensagem = input("Mensagem do commit: ")
            subprocess.run(["git", "commit", "-m", mensagem])
            branch = input("Nome do branch para envio (ex: main ou master): ")
            subprocess.run(["git", "branch", "-M", branch])
            subprocess.run(["git", "push", "-u", "origin", branch])
            print("Projeto enviado!")
        except:
            print("Erro ao enviar projeto.")
    else:
        print("Nenhum repositorio encontrado.")
    pause()

# ============================
# MENU PROGRAMAS
# ============================

def programas_menu():
    while True:
        limpar_tela()
        print("==============================")
        print(" Painel de Programas")
        print("==============================")
        print("[1] Instalar Git")
        print("[2] Instalar Node.js")
        print("[3] Instalar Python")
        print("[4] Instalar VS Code")
        print("[5] Instalar tudo")
        print("[6] Desinstalar programas")
        print("[7] Voltar\n")

        opcao = input("Escolha uma opcao: ")
        if opcao == "1":
            instalar_git()
        elif opcao == "2":
            instalar_node()
        elif opcao == "3":
            instalar_python()
        elif opcao == "4":
            instalar_vscode()
        elif opcao == "5":
            instalar_git()
            instalar_node()
            instalar_python()
            instalar_vscode()
        elif opcao == "6":
            desinstalar_menu()
        elif opcao == "7":
            return
        else:
            print("Opcao invalida.")
            pause()

def instalar_node():
    print("Instalando Node.js...")
    url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    destino = os.path.join(os.getenv("TEMP"), "node.msi")
    r = requests.get(url)
    with open(destino, "wb") as f:
        f.write(r.content)
    subprocess.run(["msiexec.exe", "/i", destino, "/quiet", "/norestart"])
    print("Node.js instalado!")
    pause()

def instalar_python():
    print("Instalando Python...")
    url = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
    destino = os.path.join(os.getenv("TEMP"), "python-installer.exe")
    r = requests.get(url)
    with open(destino, "wb") as f:
        f.write(r.content)
    subprocess.run([destino, "/quiet", "InstallAllUsers=1", "PrependPath=1"])
    print("Python instalado!")
    pause()

def instalar_vscode():
    print("Instalando VS Code...")
    url = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
    destino = os.path.join(os.getenv("TEMP"), "vscode-installer.exe")
    r = requests.get(url)
    with open(destino, "wb") as f:
        f.write(r.content)
    subprocess.run([destino, "/silent", "/mergetasks=!runcode"])
    print("VS Code instalado!")
    pause()

# ============================
# MENU DESINSTALAR
# ============================

def desinstalar_menu():
    while True:
        limpar_tela()
        print("==============================")
        print(" Painel de Desinstalacao")
        print("==============================")
        print("[1] Desinstalar Git")
        print("[2] Desinstalar Node.js")
        print("[3] Desinstalar Python")
        print("[4] Desinstalar VS Code")
        print("[5] Desinstalar tudo")
        print("[6] Voltar\n")
        opcao = input("Escolha uma opcao: ")
        if opcao == "1":
            subprocess.run(["winget", "uninstall", "--id", "Git.Git", "-e", "--silent"])
        elif opcao == "2":
            subprocess.run(["winget", "uninstall", "Node.js", "--silent"])
        elif opcao == "3":
            subprocess.run(["winget", "uninstall", "Python", "--silent"])
        elif opcao == "4":
            subprocess.run(["winget", "uninstall", "Microsoft Visual Studio Code", "--silent"])
        elif opcao == "5":
            subprocess.run(["winget", "uninstall", "--id", "Git.Git", "-e", "--silent"])
            subprocess.run(["winget", "uninstall", "Node.js", "--silent"])
            subprocess.run(["winget", "uninstall", "Python", "--silent"])
            subprocess.run(["winget", "uninstall", "Microsoft Visual Studio Code", "--silent"])
        elif opcao == "6":
            return
        else:
            print("Opcao invalida.")
        pause()

# ============================
# EXECUÇÃO
# ============================

if __name__ == "__main__":
    mostrar_menu()
