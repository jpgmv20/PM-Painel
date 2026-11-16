(() => {
  "use strict";

  const token = window.location.pathname.split("/").filter(Boolean)[0];
  const websocketPort = new URLSearchParams(window.location.search).get("ws_port");
  const states = {};

  function updateStatus(key, text, className) {
    const status = document.querySelector(`[data-status="${key}"]`);
    if (!status) return;
    status.textContent = text;
    status.classList.remove("connecting", "connected", "error");
    status.classList.add(className);
  }

  function makeTerminal(key, hostId, defaultDirectory) {
    const terminal = new Terminal({
      allowProposedApi: false,
      convertEol: true,
      cursorBlink: true,
      cursorStyle: "bar",
      fontFamily: "'Cascadia Code', Consolas, 'Courier New', monospace",
      fontSize: 13,
      lineHeight: 1.15,
      scrollback: 5000,
      theme: {
        background: "#080e18",
        foreground: "#dce8f7",
        cursor: "#86c8ff",
        cursorAccent: "#080e18",
        selectionBackground: "#34557988",
        black: "#111722",
        red: "#ff747b",
        green: "#48d597",
        yellow: "#f0c674",
        blue: "#70b7ff",
        magenta: "#c19aff",
        cyan: "#63d4d5",
        white: "#dce8f7",
        brightBlack: "#66778d",
        brightRed: "#ff8e93",
        brightGreen: "#68e5ab",
        brightYellow: "#f5d58c",
        brightBlue: "#91c8ff",
        brightMagenta: "#d3b4ff",
        brightCyan: "#8ae5e5",
        brightWhite: "#ffffff"
      }
    });
    const fit = new FitAddon.FitAddon();
    terminal.loadAddon(fit);
    terminal.open(document.getElementById(hostId));

    const state = { key, terminal, fit, socket: null, ready: false, retry: 900, retryTimer: null, disposed: false };
    states[key] = state;

    function send(payload) {
      if (state.socket && state.socket.readyState === WebSocket.OPEN) {
        state.socket.send(JSON.stringify(payload));
      }
    }

    function fitAndResize() {
      try {
        fit.fit();
        if (state.ready) send({ type: "resize", cols: terminal.cols, rows: terminal.rows });
      } catch (_error) {
        // O WebView pode ainda estar calculando o tamanho inicial do painel.
      }
    }

    function connect() {
      if (state.disposed || !token || !websocketPort) {
        updateStatus(key, "Sem conexão", "error");
        return;
      }
      updateStatus(key, "Conectando", "connecting");
      const socket = new WebSocket(`ws://127.0.0.1:${websocketPort}/?token=${encodeURIComponent(token)}`);
      state.socket = socket;
      state.ready = false;

      socket.addEventListener("open", () => {
        fitAndResize();
        socket.send(JSON.stringify({ type: "open", terminal: key, cols: terminal.cols, rows: terminal.rows }));
      });

      socket.addEventListener("message", (event) => {
        let message;
        try { message = JSON.parse(event.data); } catch (_error) { return; }
        if (message.type === "ready") {
          state.ready = true;
          state.retry = 900;
          updateStatus(key, "Conectado", "connected");
          fitAndResize();
          terminal.focus();
        } else if (message.type === "output") {
          terminal.write(message.data || "");
        } else if (message.type === "error") {
          updateStatus(key, "Aguardando container", "error");
          terminal.writeln(`\r\n\x1b[33m${message.message || "Não foi possível conectar."}\x1b[0m`);
        }
      });

      socket.addEventListener("close", () => {
        state.ready = false;
        if (state.disposed) return;
        updateStatus(key, "Reconectando", "connecting");
        state.retryTimer = window.setTimeout(connect, state.retry);
        state.retry = Math.min(Math.round(state.retry * 1.6), 5000);
      });

      socket.addEventListener("error", () => {
        updateStatus(key, "Reconectando", "connecting");
      });
    }

    terminal.onData((data) => send({ type: "input", data }));
    terminal.onResize(({ cols, rows }) => {
      if (state.ready) send({ type: "resize", cols, rows });
    });
    document.querySelector(`[data-clear="${key}"]`).addEventListener("click", () => terminal.clear());
    window.addEventListener("resize", fitAndResize);
    window.setTimeout(fitAndResize, 50);
    window.setTimeout(fitAndResize, 350);
    connect();
    return state;
  }

  if (!window.Terminal || !window.FitAddon) {
    document.body.innerHTML = "<main style='padding:32px;color:#fff;font:16px Segoe UI'>Os arquivos do xterm.js não foram carregados.</main>";
    return;
  }

  makeTerminal("A", "terminal-a", "/tmp");
  makeTerminal("B", "terminal-b", "/tmp");
})();
