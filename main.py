import os
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from devtools.widgets import WIDGETS

# Carrega o arquivo da subpasta
caminho_kv = os.path.join(os.path.dirname(__file__), 'view', 'main.kv')
Builder.load_file(caminho_kv)

class TelaPrincipal(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        WIDGETS.register(self)
        
    def executar_login(self):
        usuario = self.ids.login_usuario.text
        senha = self.ids.login_senha.text
        print(f"[LOGIN] Usuário: {usuario} | Senha: {senha}")

    def executar_cadastro(self):
        nome = self.ids.cad_nome.text
        email = self.ids.cad_email.text
        senha = self.ids.cad_senha.text
        print(f"[CADASTRO] Nome: {nome} | Email: {email} | Senha: {senha}")

class MeuApp(MDApp):
    def build(self):
        return TelaPrincipal()

if __name__ == "__main__":
    MeuApp().run()
