from Painel.Funcoes.Funcoes import *
import subprocess
import socket
import platform
from concurrent.futures import ThreadPoolExecutor

# ============================
# MENU PRINCIPAL
# ============================

def menu_redes():
    while True:
        limpar_tela()

        print("===================")
        print(" Painel de Redes")
        print("===================\n")
        print("[1] ping")
        print("[2] Redes")
        print("[3] Voltar\n")

        opcao = input("Escolha uma opcao: ")
        match opcao:
            case "1":
                escanear_rede()
            case "3":
                return
            case _:
                print("Opcao invalida.")
                pause()


# ============================
# Funções
# ============================

def obter_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    comando = ["ping", param, "1", "-w", "500", ip]
    try:
        output = subprocess.run(comando, stdout=subprocess.DEVNULL)
        if output.returncode == 0:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Desconhecido"
            print(f"{ip} está ativo - Hostname: {hostname}")
    except:
        pass

def escanear_rede():
    ip_local = obter_ipv4()
    subnet = ".".join(ip_local.split(".")[:3]) + "."
    print(f"Escaneando rede {subnet}0/24...")

    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(1, 255):
            ip = subnet + str(i)
            executor.submit(ping, ip)
    pause()
