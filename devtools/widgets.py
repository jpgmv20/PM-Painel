"""
widgets.py

Registro de widgets Kivy ativos.

Responsável por:

- Registrar widgets criados
- Encontrar widgets por classe
- Atualizar canvas
- Preparar reconstrução futura
"""


from weakref import WeakSet


from devtools.logger import Logger



class WidgetRegistry:


    def __init__(self):

        self.widgets = WeakSet()



    # =====================================================
    # Registrar widget
    # =====================================================


    def register(
        self,
        widget
    ):


        self.widgets.add(
            widget
        )


        Logger.debug(
            f"Widget registrado: "
            f"{widget.__class__.__name__}"
        )



    # =====================================================
    # Remover widget
    # =====================================================


    def unregister(
        self,
        widget
    ):


        if widget in self.widgets:


            self.widgets.remove(
                widget
            )



    # =====================================================
    # Todos widgets
    # =====================================================


    def all(self):

        return list(
            self.widgets
        )



    # =====================================================
    # Procurar por classe
    # =====================================================


    def find(
        self,
        class_name
    ):


        result = []


        for widget in self.widgets:


            if (
                widget.__class__.__name__
                ==
                class_name
            ):

                result.append(
                    widget
                )


        return result



    # =====================================================
    # Atualização visual
    # =====================================================


    def refresh(
        self
    ):


        updated = 0



        for widget in list(
            self.widgets
        ):


            try:


                widget.canvas.ask_update()


                updated += 1



            except Exception:


                pass



        Logger.debug(
            f"{updated} widgets atualizados."
        )



    # =====================================================
    # Chamado pelo HotReload
    # =====================================================


    def reload(
        self
    ):


        Logger.info(
            "Atualizando widgets registrados..."
        )


        self.refresh()



    # =====================================================
    # Informações
    # =====================================================


    def count(
        self
    ):


        return len(
            self.widgets
        )



# Instância global

WIDGETS = WidgetRegistry()