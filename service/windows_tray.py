"""Ícone de bandeja do Windows para restaurar ou encerrar o painel."""

from __future__ import annotations

import os
import threading
from typing import Callable

from kivy.clock import Clock


class WindowsTrayService:
    """Cria um ícone de bandeja usando as APIs nativas do Windows."""

    _CALLBACK_MESSAGE = 0x8001
    _MENU_RESTORE = 1
    _MENU_EXIT = 2

    def __init__(self, on_restore: Callable[[], None], on_exit: Callable[[], None]) -> None:
        if os.name != "nt":
            raise OSError("A bandeja do sistema só está disponível no Windows.")
        try:
            import win32api  # noqa: F401
            import win32con  # noqa: F401
            import win32gui  # noqa: F401
        except ImportError as error:
            raise RuntimeError("O suporte nativo à bandeja do Windows não está instalado.") from error

        self._on_restore = on_restore
        self._on_exit = on_exit
        self._ready = threading.Event()
        self._stopped = threading.Event()
        self._error: Exception | None = None
        self._thread = threading.Thread(target=self._message_loop, name="PM-Painel-Tray", daemon=True)
        self._thread.start()
        if not self._ready.wait(3):
            raise RuntimeError("Não foi possível iniciar o ícone da bandeja do PM-Painel.")
        if self._error is not None:
            raise RuntimeError(f"Não foi possível iniciar a bandeja: {self._error}") from self._error

    @property
    def running(self) -> bool:
        return not self._stopped.is_set()

    def minimize(self) -> None:
        import win32con
        import win32gui

        hwnd = self._find_app_window()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

    def restore(self) -> None:
        import win32con
        import win32gui

        hwnd = self._find_app_window()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)

    def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._stopped.set()
        hwnd = getattr(self, "_hwnd", None)
        if hwnd:
            import win32gui
            win32gui.PostMessage(hwnd, 0x0010, 0, 0)

    @staticmethod
    def _find_app_window() -> int | None:
        import win32gui
        import win32process

        process_id = os.getpid()
        found: list[int] = []

        def inspect(hwnd: int, _extra: object) -> bool:
            _thread_id, owner_pid = win32process.GetWindowThreadProcessId(hwnd)
            if owner_pid == process_id and win32gui.GetWindowText(hwnd) == "PM-Painel":
                found.append(hwnd)
                return False
            return True

        win32gui.EnumWindows(inspect, None)
        return found[0] if found else None

    def _message_loop(self) -> None:
        import win32api
        import win32con
        import win32gui

        class_name = f"PMPainelTray-{os.getpid()}"
        instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = instance
        window_class.lpszClassName = class_name
        window_class.lpfnWndProc = self._window_proc
        try:
            win32gui.RegisterClass(window_class)
            self._hwnd = win32gui.CreateWindow(
                class_name, "PM-Painel Tray", 0, 0, 0, 0, 0, 0, 0, instance, None
            )
            icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            self._notify_data = (
                self._hwnd,
                0,
                win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                self._CALLBACK_MESSAGE,
                icon,
                "PM-Painel",
            )
            if not win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self._notify_data):
                raise RuntimeError("O Windows recusou o ícone da bandeja.")
            self._ready.set()
            win32gui.PumpMessages()
        except Exception as error:
            self._error = error
            self._ready.set()
        finally:
            hwnd = getattr(self, "_hwnd", None)
            if hwnd and hasattr(self, "_notify_data"):
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self._notify_data)
                    win32gui.DestroyWindow(hwnd)
                except Exception:
                    pass
            self._stopped.set()

    def _window_proc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        import win32con
        import win32gui

        if message == self._CALLBACK_MESSAGE:
            if lparam in (win32con.WM_LBUTTONUP, win32con.WM_LBUTTONDBLCLK):
                Clock.schedule_once(lambda _dt: self._on_restore(), 0)
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu(hwnd)
            return 0
        if message == win32con.WM_COMMAND:
            command = wparam & 0xFFFF
            if command == self._MENU_RESTORE:
                Clock.schedule_once(lambda _dt: self._on_restore(), 0)
            elif command == self._MENU_EXIT:
                Clock.schedule_once(lambda _dt: self._on_exit(), 0)
            return 0
        if message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def _show_menu(self, hwnd: int) -> None:
        import win32con
        import win32gui

        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, self._MENU_RESTORE, "Abrir PM-Painel")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, None)
        win32gui.AppendMenu(menu, win32con.MF_STRING, self._MENU_EXIT, "Sair")
        x, y = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_RIGHTBUTTON, x, y, 0, hwnd, None)
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
