/**
 * Widget de Assistente RAG — Disruptive Architectures (FIAP)
 * Integrado perfeitamente ao tema MkDocs Material com navegação instantânea.
 */

(function () {
  // URL base da API FastAPI (ajuste para a URL do Render em produção)
  const API_URL = window.DA_RAG_API_URL || (
    window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
      ? "http://localhost:8000/api/chat"
      : "https://disruptive-architectures-backend.onrender.com/api/chat"
  );

  // Estado que sobrevive à recriação do DOM entre navegações instantâneas do MkDocs
  const estado = {
    aberto: false,
    mensagens: [],
    enviando: false,
    sessionId: localStorage.getItem("da_rag_widget_session") || ""
  };

  const CSS_STYLES = `
    #da-bubble-btn {
      position: fixed !important; bottom: 24px !important; right: 24px !important; z-index: 99999 !important;
      width: 58px; height: 58px; border-radius: 50%;
      background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%);
      color: white; border: none; cursor: pointer;
      font-size: 26px; box-shadow: 0 4px 20px rgba(121, 40, 202, 0.4);
      display: flex !important; align-items: center; justify-content: center;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s;
    }
    #da-bubble-btn:hover {
      transform: scale(1.08) translateY(-2px);
      box-shadow: 0 6px 24px rgba(121, 40, 202, 0.55);
    }
    #da-widget-root {
      position: fixed !important; bottom: 94px !important; right: 24px !important; z-index: 99999 !important;
      width: 380px; max-width: calc(100vw - 32px); height: 520px; max-height: 75vh;
      background: rgba(22, 27, 34, 0.94);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
      display: none !important; flex-direction: column; overflow: hidden;
      font-family: var(--md-text-font, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
      color: #f0f6fc;
    }
    #da-widget-root.open { display: flex !important; animation: daFadeIn 0.25s ease; }
    @keyframes daFadeIn {
      from { opacity: 0; transform: translateY(12px) scale(0.97); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    #da-widget-header {
      background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%);
      padding: 12px 16px; color: white;
      display: flex; justify-content: space-between; align-items: center;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .da-header-title { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 14px; }
    .da-header-actions { display: flex; align-items: center; gap: 6px; }
    .da-icon-btn {
      background: rgba(255,255,255,0.15); border: none; color: white;
      width: 28px; height: 28px; border-radius: 50%;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      font-size: 14px; transition: background 0.2s;
    }
    .da-icon-btn:hover { background: rgba(255,255,255,0.3); }
    #da-messages-container {
      flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px;
      font-size: 13.5px; line-height: 1.5;
    }
    .da-msg { display: flex; flex-direction: column; max-width: 86%; }
    .da-msg.user { align-self: flex-end; }
    .da-msg.bot { align-self: flex-start; }
    .da-bubble {
      padding: 10px 14px; border-radius: 12px; word-break: break-word;
    }
    .da-msg.user .da-bubble {
      background: linear-gradient(135deg, #7928ca, #ff0080);
      color: white; border-bottom-right-radius: 3px;
    }
    .da-msg.bot .da-bubble {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #e6edf3; border-bottom-left-radius: 3px;
    }
    .da-bubble pre {
      background: #090d13; border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 8px 10px; border-radius: 6px; overflow-x: auto; margin: 6px 0;
      font-family: monospace; font-size: 12px;
    }
    .da-bubble code {
      background: rgba(255, 255, 255, 0.1); padding: 2px 4px; border-radius: 4px; font-size: 12px;
    }
    .da-sources {
      margin-top: 8px; font-size: 11px; opacity: 0.85; border-top: 1px dashed rgba(255,255,255,0.15);
      padding-top: 6px; display: flex; flex-wrap: wrap; gap: 4px;
    }
    .da-source-link {
      background: rgba(0, 112, 243, 0.2); border: 1px solid rgba(0, 112, 243, 0.4);
      color: #79c0ff; text-decoration: none; padding: 2px 6px; border-radius: 4px;
    }
    .da-source-link:hover { text-decoration: underline; }
    #da-input-area {
      display: flex; gap: 8px; padding: 10px 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(13, 17, 23, 0.6);
    }
    #da-input {
      flex: 1; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 20px;
      background: rgba(255, 255, 255, 0.06); color: white; padding: 8px 14px;
      font-size: 13.5px; outline: none; transition: border-color 0.2s;
    }
    #da-input:focus { border-color: #7928ca; }
    #da-send-btn {
      width: 36px; height: 36px; border-radius: 50%; border: none;
      background: linear-gradient(135deg, #7928ca, #ff0080); color: white;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      font-size: 14px; flex-shrink: 0;
    }
    #da-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    @media (max-width: 480px) {
      #da-widget-root {
        bottom: 0 !important; right: 0 !important; width: 100vw !important; max-width: 100vw !important;
        height: 85vh !important; max-height: 85vh !important; border-radius: 18px 18px 0 0 !important;
      }
    }
  `;

  function garantirEstilos() {
    if (!document.getElementById("da-widget-styles")) {
      const style = document.createElement("style");
      style.id = "da-widget-styles";
      style.textContent = CSS_STYLES;
      document.head.appendChild(style);
    }
  }

  function montarWidget() {
    garantirEstilos();

    let bubble = document.getElementById("da-bubble-btn");
    let widget = document.getElementById("da-widget-root");

    // Se já existem e estão acoplados ao document.body ativo, apenas sincroniza
    if (bubble && widget && document.body && document.body.contains(bubble) && document.body.contains(widget)) {
      if (estado.aberto) {
        widget.classList.add("open");
      } else {
        widget.classList.remove("open");
      }
      return;
    }

    // Se existiam referências desconectadas ou órfãs pelo swap do MkDocs, limpa
    if (bubble) bubble.remove();
    if (widget) widget.remove();

    if (!document.body) return;

    bubble = document.createElement("button");
    bubble.id = "da-bubble-btn";
    bubble.title = "Assistente Virtual da Disciplina";
    bubble.setAttribute("aria-label", "Abrir assistente virtual");
    bubble.textContent = "🤖";
    document.body.appendChild(bubble);

    widget = document.createElement("div");
    widget.id = "da-widget-root";
    widget.innerHTML = `
      <div id="da-widget-header">
        <div class="da-header-title">
          <span>🤖</span>
          <span>Assistente Disruptive Architectures</span>
        </div>
        <div class="da-header-actions">
          <button class="da-icon-btn" id="da-reset-btn" title="Nova Conversa">🔄</button>
          <button class="da-icon-btn" id="da-close-btn" title="Fechar">✕</button>
        </div>
      </div>
      <div id="da-messages-container"></div>
      <div id="da-input-area">
        <input id="da-input" type="text" placeholder="Pergunte sobre aulas, ESP32, GenAI..." />
        <button id="da-send-btn" title="Enviar">➤</button>
      </div>
    `;
    document.body.appendChild(widget);

    const input = widget.querySelector("#da-input");
    const sendBtn = widget.querySelector("#da-send-btn");
    const closeBtn = widget.querySelector("#da-close-btn");
    const resetBtn = widget.querySelector("#da-reset-btn");
    const messagesEl = widget.querySelector("#da-messages-container");

    // Renderiza mensagens acumuladas no estado
    if (estado.mensagens.length === 0) {
      adicionarMensagemUI(messagesEl, {
        who: "bot",
        texto: "Olá! Sou seu assistente de Disruptive Architectures. Pergunte sobre aulas de IoT (Arduino, ESP32, MQTT) ou GenAI (Prompts, Assistentes, RAG)."
      });
    } else {
      estado.mensagens.forEach((m) => adicionarMensagemUI(messagesEl, m));
    }

    if (estado.aberto) {
      widget.classList.add("open");
    }

    bubble.addEventListener("click", () => {
      widget.classList.toggle("open");
      estado.aberto = widget.classList.contains("open");
      if (estado.aberto) input.focus();
    });

    closeBtn.addEventListener("click", () => {
      widget.classList.remove("open");
      estado.aberto = false;
    });

    resetBtn.addEventListener("click", async () => {
      if (estado.sessionId) {
        try {
          const baseUrl = API_URL.replace("/api/chat", "");
          await fetch(`${baseUrl}/api/chat/session/${estado.sessionId}`, { method: "DELETE" });
        } catch (e) {}
      }
      estado.sessionId = "";
      estado.mensagens = [];
      localStorage.removeItem("da_rag_widget_session");
      messagesEl.innerHTML = "";
      adicionarMensagemUI(messagesEl, {
        who: "bot",
        texto: "Conversa reiniciada. Como posso te ajudar?"
      });
    });

    async function enviar() {
      const texto = input.value.trim();
      if (!texto || estado.enviando) return;

      estado.enviando = true;
      input.disabled = true;
      sendBtn.disabled = true;
      input.value = "";

      const msgUser = { who: "user", texto };
      estado.mensagens.push(msgUser);
      adicionarMensagemUI(messagesEl, msgUser);

      const loadingMsg = { who: "bot", texto: "Consultando o material da disciplina...", loading: true };
      const loadingEl = adicionarMensagemUI(messagesEl, loadingMsg);

      try {
        const resp = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: texto, session_id: estado.sessionId })
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        estado.sessionId = data.session_id;
        localStorage.setItem("da_rag_widget_session", estado.sessionId);

        loadingEl.remove();

        const msgBot = { who: "bot", texto: data.answer, fontes: data.sources };
        estado.mensagens.push(msgBot);
        adicionarMensagemUI(messagesEl, msgBot);
      } catch (err) {
        loadingEl.remove();
        adicionarMensagemUI(messagesEl, {
          who: "bot",
          texto: "⚠️ Não foi possível conectar ao assistente no momento. Verifique se o backend está em execução."
        });
      } finally {
        estado.enviando = false;
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
      }
    }

    sendBtn.addEventListener("click", enviar);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") enviar();
    });
  }

  function normalizarUrl(url) {
    if (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")) {
      return url.replace(/https:\/\/[^/]+\.github\.io\/[^/]+\//, "/DisruptiveArchitectures/");
    }
    return url;
  }

  function converterMarkdownBasico(texto) {
    if (!texto) return "";
    let normalizado = texto
      .replace(/([^\n])\s*(#{1,6}\s+)/g, "$1\n\n$2")
      .replace(/(#{1,6}\s+[^\n]+?[?!:])([A-ZÀ-Ú])/g, "$1\n\n$2")
      .replace(/:\s*(\d+\.\s+)/g, ":\n\n$1")
      .replace(/([.!?])\s*(\d+\.\s+)/g, "$1\n\n$2")
      .replace(/([.!?])([A-ZÀ-Ú])/g, "$1\n\n$2");

    let seguro = normalizado.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const codigos = [];
    seguro = seguro.replace(/```[a-zA-Z]*\n?([\s\S]*?)```/g, (_, c) => {
      const idx = codigos.length;
      codigos.push(c.trim());
      return `%%CODEBLOCK_${idx}%%`;
    });
    // Links em Markdown [texto](url)
    seguro = seguro.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_, t, u) => {
      const href = normalizarUrl(u);
      return `<a href="${href}" target="_blank" style="color: #79c0ff; text-decoration: underline; font-weight: 500;">${t}</a>`;
    });
    // Títulos Markdown
    seguro = seguro.replace(/^###\s+(.+)$/gm, '<h3 style="margin: 10px 0 4px 0; color: #fff; font-size: 14px; font-weight: 700;">$1</h3>');
    seguro = seguro.replace(/^##\s+(.+)$/gm, '<h2 style="margin: 12px 0 6px 0; color: #fff; font-size: 15px; font-weight: 700;">$1</h2>');
    seguro = seguro.replace(/^#\s+(.+)$/gm, '<h1 style="margin: 14px 0 8px 0; color: #fff; font-size: 16px; font-weight: 700;">$1</h1>');

    seguro = seguro.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    seguro = seguro.replace(/\*(.+?)\*/g, "<em>$1</em>");
    seguro = seguro.replace(/`([^`]+)`/g, "<code>$1</code>");
    seguro = seguro.replace(/\n\n+/g, "<br><br>");
    seguro = seguro.replace(/\n/g, "<br>");
    seguro = seguro.replace(/%%CODEBLOCK_(\d+)%%/g, (_, idx) => {
      return `<pre><code>${codigos[Number(idx)]}</code></pre>`;
    });
    return seguro;
  }

  function adicionarMensagemUI(container, m) {
    const wrap = document.createElement("div");
    wrap.className = `da-msg ${m.who}`;
    const bubble = document.createElement("div");
    bubble.className = "da-bubble";

    if (m.who === "bot") {
      bubble.innerHTML = converterMarkdownBasico(m.texto);
      if (m.fontes && m.fontes.length > 0) {
        const srcDiv = document.createElement("div");
        srcDiv.className = "da-sources";
        srcDiv.innerHTML = "<span>Fontes: </span>";
        m.fontes.forEach((f) => {
          const a = document.createElement("a");
          a.className = "da-source-link";
          a.href = normalizarUrl(f.url);
          a.target = "_blank";
          a.textContent = f.title || f.url;
          srcDiv.appendChild(a);
        });
        bubble.appendChild(srcDiv);
      }
    } else {
      bubble.textContent = m.texto;
    }

    wrap.appendChild(bubble);
    container.appendChild(wrap);
    container.scrollTop = container.scrollHeight;
    return wrap;
  }

  // Suporte à navegação instantânea do MkDocs Material e ciclo de vida SPA
  let subscritoInstant = false;
  try {
    if (typeof document$ !== "undefined" && typeof document$.subscribe === "function") {
      document$.subscribe(() => {
        montarWidget();
      });
      subscritoInstant = true;
    }
  } catch (e) {}

  if (!subscritoInstant) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", montarWidget);
    } else {
      montarWidget();
    }
  }

  // MutationObserver como rede de proteção contra substituição de nós pelo MkDocs
  try {
    if (document.body) {
      new MutationObserver(() => {
        const b = document.getElementById("da-bubble-btn");
        const w = document.getElementById("da-widget-root");
        if (!b || !w || !document.body.contains(b) || !document.body.contains(w)) {
          montarWidget();
        }
      }).observe(document.body, { childList: true, subtree: false });
    }
  } catch (e) {}
})();
