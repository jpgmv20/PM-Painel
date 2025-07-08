
import os
import subprocess
import requests
from kivy import *

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")#coloca no cmd um comando para limpar o terminal dependendo do sistema operacional

def pause():
    input("\nPressione Enter para continuar...")

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
        match opcao:
            case "1":
                instalar_git()
            case "2":
                instalar_node()
            case "3":
                instalar_python()
            case "4":
                instalar_vscode()
            case "5":
                instalar_git()
                instalar_node()
                instalar_python()
                instalar_vscode()
            case "6":
                desinstalar_menu()
            case "7":
                return
            case _:
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
