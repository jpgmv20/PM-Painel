"""
validator.py

Validador do projeto.

Responsável por:

- Verificar arquivos Python
- Detectar erros de sintaxe
- Validar estrutura básica
- Evitar reload com código quebrado
"""


import ast
from pathlib import Path


from devtools.logger import Logger



class ProjectValidator:


    def __init__(
        self,
        project_root: Path
    ):


        self.project_root = project_root



    # =====================================================
    # Validação principal
    # =====================================================


    def validate(self):


        errors = []



        python_files = (
            self.project_root.rglob(
                "*.py"
            )
        )



        for file in python_files:


            if self.should_ignore(file):

                continue



            error = self.validate_python(
                file
            )



            if error:


                errors.append(
                    error
                )



        if errors:


            return (
                False,
                "\n".join(errors)
            )



        return (
            True,
            None
        )



    # =====================================================
    # Validar Python
    # =====================================================


    def validate_python(
        self,
        file: Path
    ):


        try:


            source = file.read_text(
                encoding="utf-8"
            )


            ast.parse(
                source
            )



        except SyntaxError as error:


            return (
                f"{file.name}: "
                f"linha {error.lineno}: "
                f"{error.msg}"
            )



        except Exception as error:


            return (
                f"{file.name}: "
                f"erro lendo arquivo: {error}"
            )



        return None



    # =====================================================
    # Ignorar arquivos
    # =====================================================


    def should_ignore(
        self,
        file: Path
    ):


        ignored = (

            "__pycache__",

            ".git",

            ".venv",

            "venv",

            "kivy_venv",

            "site-packages",

        )



        return any(

            folder in file.parts

            for folder in ignored

        )



    # =====================================================
    # Validar arquivo específico
    # =====================================================


    def validate_file(
        self,
        file: Path
    ):


        if file.suffix != ".py":

            return True, None



        error = self.validate_python(
            file
        )


        if error:


            Logger.error(
                error
            )


            return (
                False,
                error
            )



        return (
            True,
            None
        )