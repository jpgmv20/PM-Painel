from devtools.events import EVENTS


def log_reload(file):

    print(
        "[PLUGIN]",
        file
    )


EVENTS.on(
    "file_changed",
    log_reload
)