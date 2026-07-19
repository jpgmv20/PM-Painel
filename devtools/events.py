"""
events.py

Sistema interno de eventos.

Permite comunicação entre módulos
sem criar dependências diretas.

Exemplo:

EVENTS.on(
    "file_changed",
    minha_funcao
)


EVENTS.emit(
    "file_changed",
    arquivo
)
"""


from collections import defaultdict


from devtools.logger import Logger



class EventBus:


    def __init__(self):

        self.listeners = defaultdict(list)



    # =====================================================
    # Registrar evento
    # =====================================================


    def on(
        self,
        event,
        callback
    ):


        if callback not in self.listeners[event]:


            self.listeners[event].append(
                callback
            )


            Logger.debug(
                f"Listener registrado: {event}"
            )



    # =====================================================
    # Remover evento
    # =====================================================


    def off(
        self,
        event,
        callback
    ):


        if callback in self.listeners[event]:


            self.listeners[event].remove(
                callback
            )



    # =====================================================
    # Emitir evento
    # =====================================================


    def emit(
        self,
        event,
        *args,
        **kwargs
    ):


        Logger.debug(
            f"Evento emitido: {event}"
        )



        for callback in list(
            self.listeners[event]
        ):


            try:


                callback(
                    *args,
                    **kwargs
                )


            except Exception as error:


                Logger.error(
                    f"Erro no evento '{event}': {error}"
                )



    # =====================================================
    # Limpar tudo
    # =====================================================


    def clear(self):

        self.listeners.clear()



    # =====================================================
    # Informações
    # =====================================================


    def registered_events(self):

        return list(
            self.listeners.keys()
        )



    def listeners_count(
        self,
        event
    ):


        return len(
            self.listeners[event]
        )



# Instância global

EVENTS = EventBus()