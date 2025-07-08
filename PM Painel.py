import os
from kivy import *
from Painel.Painel_git import git_menu
from Painel.Program_instal import programas_menu

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")#coloca no cmd um comando para limpar o terminal dependendo do sistema operacional

def pause():
    input("\nPressione Enter para continuar...")

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
# EXECUÇÃO
# ============================

if __name__ == "__main__":
    mostrar_menu()

