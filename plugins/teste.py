def on_start(runner):

    print(
        "[PLUGIN] Aplicação iniciou!"
    )


def on_reload(file):

    print(
        f"[PLUGIN] Reload: {file}"
    )


def on_shutdown():

    print(
        "[PLUGIN] Encerrando..."
    )