import os
def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")#coloca no cmd um comando para limpar o terminal dependendo do sistema operacional

def pause():
    input("\nPressione Enter para continuar...")