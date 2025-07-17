import os
from Painel.Técnico.Painel_git import git_menu
from Painel.Program_instal import programas_menu
from Painel.Técnico.redes import menu_redes
from Painel.Funcoes.Funcoes import *



# ============================
# MENU PRINCIPAL
# ============================

def mostrar_menu():
    while True:
        limpar_tela()
        print("==========================")
        print(" Painel de Controle Pessoal")
        print("==========================")
        print("[1] Matérias do Técnico")
        print("[2] Programas")
        print("[3] Sair\n")

        opcao = input("Escolha uma opcao: ")
        match opcao:
            case "1":
                menu_tecnico()
            case "2":
                programas_menu()
            case "3":
                print("Saindo...")
                limpar_tela()
                break
            case _:
                print("Opcao invalida.")
                pause()

# ============================
# Menus
# ============================

def menu_tecnico():
    while True:
        limpar_tela()

        print("=============================")
        print(" Painel de Controle do Técnico")
        print("=============================\n")
        print("[1] Git")
        print("[2] Redes")
        print("[3] Voltar\n")

        opcao = input("Escolha uma opcao: ")
        match opcao:
            case "1":
                git_menu()
            case "2":
                menu_redes()
            case "3":
                return
            case _:
                print("Opcao invalida.")
                pause()


