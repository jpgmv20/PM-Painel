from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import NumericProperty

class PersonagemCard(BoxLayout):

    current_hp = NumericProperty(0)

    def __init__(self, nome, classe, nivel, hp, **kwargs):
        
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'

        self.nome_label = Label(text=f'Nome: {nome}')
        self.add_widget(self.nome_label)

        self.classe_label = Label(text=f'Classe: {classe}')
        self.add_widget(self.classe_label)

        self.nivel_label = Label(text=f'Nível: {nivel}')
        self.add_widget(self.nivel_label)

        self.hp_label = Label(text=f'HP: {hp}')
        self.add_widget(self.hp_label)
        
        self.current_hp = hp

        self.botao = Button(text='Clique Aqui')
        self.botao.bind(on_press=self.on_button_click)
        self.add_widget(self.botao)

    def on_button_click(self, instance):
        if self.current_hp > 0:
            self.current_hp = max(0, self.current_hp - 10)
        
    def on_current_hp(self, instance, value):
        self.hp_label.text = f'HP: {value}'

class MeuApp(App):

    def build(self):

        return PersonagemCard(nome="Arthur", classe="Guerreiro", nivel=5, hp=100)


MeuApp().run()