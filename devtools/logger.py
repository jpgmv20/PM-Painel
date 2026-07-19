"""
logger.py

Sistema de logs do framework.

Responsável por:

- Logs no terminal
- Arquivo de histórico
- Níveis de mensagem
- Histórico em memória
"""


from datetime import datetime
from pathlib import Path


from devtools.config import CONFIG



class Logger:


    history = []


    log_directory = (
        Path.cwd()
        /
        ".pm_logs"
    )


    log_file = (
        log_directory
        /
        "development.log"
    )



    # =====================================================
    # Inicialização
    # =====================================================


    @classmethod
    def setup(cls):

        cls.log_directory.mkdir(
            exist_ok=True
        )



    # =====================================================
    # Escrita principal
    # =====================================================


    @classmethod
    def write(
        cls,
        level,
        message
    ):


        cls.setup()


        now = datetime.now()


        text = (
            f"[{now:%d/%m/%Y %H:%M:%S}] "
            f"[{level}] "
            f"{message}"
        )


        cls.history.append(
            text
        )


        try:


            with open(
                cls.log_file,
                "a",
                encoding="utf-8"
            ) as file:


                file.write(
                    text + "\n"
                )


        except Exception:


            pass



        print(
            text
        )



    # =====================================================
    # Níveis
    # =====================================================


    @classmethod
    def debug(
        cls,
        message
    ):


        if CONFIG.debug:


            cls.write(
                "DEBUG",
                message
            )



    @classmethod
    def info(
        cls,
        message
    ):


        cls.write(
            "INFO",
            message
        )



    @classmethod
    def success(
        cls,
        message
    ):


        cls.write(
            "SUCCESS",
            message
        )



    @classmethod
    def warning(
        cls,
        message
    ):


        cls.write(
            "WARNING",
            message
        )



    @classmethod
    def error(
        cls,
        message
    ):


        cls.write(
            "ERROR",
            message
        )



    # =====================================================
    # Interface
    # =====================================================


    @classmethod
    def separator(cls):

        print(
            "-" * 60
        )



    @classmethod
    def banner(cls):

        print(
            """
============================================================

                    PM-PAINEL DEV

             Kivy Development Environment

============================================================
"""
        )



    @classmethod
    def box(
        cls,
        title,
        *lines
    ):


        cls.separator()


        print(
            f"| {title}"
        )


        cls.separator()


        for line in lines:

            print(
                f"| {line}"
            )


        cls.separator()



    # =====================================================
    # Histórico
    # =====================================================


    @classmethod
    def last(
        cls,
        amount=10
    ):


        return cls.history[-amount:]



    @classmethod
    def clear_history(cls):

        cls.history.clear()