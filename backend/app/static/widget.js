/**
 * Widget de Assistente RAG — Disruptive Architectures (FIAP)
 * 100% Imune a trocas de páginas SPA e navegação instantânea do MkDocs Material.
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
      position: fixed !important;
      bottom: 24px !important;
      right: 24px !important;
      z-index: 999999 !important;
      width: 58px !important;
      height: 58px !important;
      border-radius: 50% !important;
      background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%) !important;
      color: white !important;
      border: none !important;
      cursor: pointer !important;
      font-size: 26px !important;
      box-shadow: 0 4px 20px rgba(121, 40, 202, 0.45) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s !important;
      margin: 0 !important;
      padding: 0 !important;
      outline: none !important;
    }
    #da-bubble-btn:hover {
      transform: scale(1.08) translateY(-2px) !important;
      box-shadow: 0 6px 24px rgba(121, 40, 202, 0.6) !important;
    }
    #da-widget-root {
      position: fixed !important;
      bottom: 94px !important;
      right: 24px !important;
      z-index: 999999 !important;
      width: 380px !important;
      max-width: calc(100vw - 32px) !important;
      height: 520px !important;
      max-height: 75vh !important;
      background: rgba(22, 27, 34, 0.96) !important;
      backdrop-filter: blur(18px) !important;
      -webkit-backdrop-filter: blur(18px) !important;
      border: 1px solid rgba(255, 255, 255, 0.15) !important;
      border-radius: 18px !important;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5) !important;
      display: none;
      flex-direction: column !important;
      overflow: hidden !important;
      font-family: var(--md-text-font, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif) !important;
      color: #f0f6fc !important;
      box-sizing: border-box !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    #da-widget-root.open {
      display: flex !important;
      animation: daFadeIn 0.25s ease !important;
    }
    @keyframes daFadeIn {
      from { opacity: 0; transform: translateY(12px) scale(0.97); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    #da-widget-header {
      background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%) !important;
      padding: 12px 16px !important;
      color: white !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
      flex-shrink: 0 !important;
      border-top-left-radius: 17px !important;
      border-top-right-radius: 17px !important;
    }
    .da-header-title { display: flex !important; align-items: center !important; gap: 8px !important; font-weight: 600 !important; font-size: 14px !important; color: white !important; }
    .da-header-actions { display: flex !important; align-items: center !important; gap: 6px !important; }
    .da-icon-btn {
      background: rgba(255,255,255,0.18) !important;
      border: none !important;
      color: white !important;
      width: 28px !important;
      height: 28px !important;
      border-radius: 50% !important;
      cursor: pointer !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 14px !important;
      transition: background 0.2s !important;
      padding: 0 !important;
    }
    .da-icon-btn:hover { background: rgba(255,255,255,0.35) !important; }
    #da-messages-container {
      flex: 1 !important;
      overflow-y: auto !important;
      padding: 14px !important;
      display: flex !important;
      flex-direction: column !important;
      gap: 12px !important;
      font-size: 13.5px !important;
      line-height: 1.5 !important;
      background: transparent !important;
    }
    .da-msg { display: flex !important; flex-direction: column !important; max-width: 86% !important; }
    .da-msg.user { align-self: flex-end !important; }
    .da-msg.bot { align-self: flex-start !important; }
    .da-bubble {
      padding: 10px 14px !important;
      border-radius: 12px !important;
      word-break: break-word !important;
      font-size: 13px !important;
      line-height: 1.45 !important;
    }
    .da-msg.user .da-bubble {
      background: linear-gradient(135deg, #7928ca, #ff0080) !important;
      color: white !important;
      border-bottom-right-radius: 3px !important;
    }
    .da-msg.bot .da-bubble {
      background: rgba(255, 255, 255, 0.08) !important;
      border: 1px solid rgba(255, 255, 255, 0.1) !important;
      color: #e6edf3 !important;
      border-bottom-left-radius: 3px !important;
    }
    .da-bubble pre {
      background: #090d13 !important;
      border: 1px solid rgba(255, 255, 255, 0.1) !important;
      padding: 8px 10px !important;
      border-radius: 6px !important;
      overflow-x: auto !important;
      margin: 6px 0 !important;
      font-family: monospace !important;
      font-size: 12px !important;
      color: #79c0ff !important;
    }
    .da-bubble code {
      background: rgba(255, 255, 255, 0.1) !important;
      padding: 2px 4px !important;
      border-radius: 4px !important;
      font-size: 12px !important;
      color: #e6edf3 !important;
    }
    .da-sources {
      margin-top: 8px !important;
      font-size: 11px !important;
      opacity: 0.85 !important;
      border-top: 1px dashed rgba(255,255,255,0.15) !important;
      padding-top: 6px !important;
      display: flex !important;
      flex-wrap: wrap !important;
      gap: 4px !important;
    }
    .da-source-link {
      background: rgba(0, 112, 243, 0.2) !important;
      border: 1px solid rgba(0, 112, 243, 0.4) !important;
      color: #79c0ff !important;
      text-decoration: none !important;
      padding: 2px 6px !important;
      border-radius: 4px !important;
    }
    .da-source-link:hover { text-decoration: underline !important; }
    #da-input-area {
      display: flex !important;
      gap: 8px !important;
      padding: 10px 14px !important;
      border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
      background: rgba(13, 17, 23, 0.6) !important;
      flex-shrink: 0 !important;
    }
    #da-input {
      flex: 1 !important;
      border: 1px solid rgba(255, 255, 255, 0.15) !important;
      border-radius: 20px !important;
      background: rgba(255, 255, 255, 0.06) !important;
      color: white !important;
      padding: 8px 14px !important;
      font-size: 13.5px !important;
      outline: none !important;
      transition: border-color 0.2s !important;
      box-sizing: border-box !important;
    }
    #da-input:focus { border-color: #7928ca !important; }
    #da-send-btn {
      width: 36px !important;
      height: 36px !important;
      border-radius: 50% !important;
      border: none !important;
      background: linear-gradient(135deg, #7928ca, #ff0080) !important;
      color: white !important;
      cursor: pointer !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 14px !important;
      flex-shrink: 0 !important;
      padding: 0 !important;
    }
    #da-send-btn:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }
    @media (max-width: 480px) {
      #da-widget-root {
        bottom: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        height: 85vh !important;
        max-height: 85vh !important;
        border-radius: 18px 18px 0 0 !important;
      }
    }
  `;

  function aplicarEstilosCriticos(widget, bubble, aberto) {
    if (bubble) {
      bubble.style.cssText = `
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 999999 !important;
        width: 58px !important;
        height: 58px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%) !important;
        color: white !important;
        border: none !important;
        cursor: pointer !important;
        font-size: 26px !important;
        box-shadow: 0 4px 20px rgba(121, 40, 202, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        outline: none !important;
      `;
    }
    if (widget) {
      const isMobile = window.innerWidth <= 480;
      const displayVal = aberto ? "flex" : "none";
      const bottomVal = isMobile ? "0px" : "94px";
      const rightVal = isMobile ? "0px" : "24px";
      const widthVal = isMobile ? "100vw" : "380px";
      const maxWVal = isMobile ? "100vw" : "calc(100vw - 32px)";
      const heightVal = isMobile ? "85vh" : "520px";
      const maxHVal = isMobile ? "85vh" : "75vh";
      const radiusVal = isMobile ? "18px 18px 0 0" : "18px";

      widget.style.cssText = `
        position: fixed !important;
        bottom: ${bottomVal} !important;
        right: ${rightVal} !important;
        z-index: 999999 !important;
        width: ${widthVal} !important;
        max-width: ${maxWVal} !important;
        height: ${heightVal} !important;
        max-height: ${maxHVal} !important;
        border-radius: ${radiusVal} !important;
        background: rgba(22, 27, 34, 0.96) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5) !important;
        display: ${displayVal} !important;
        flex-direction: column !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
        color: #f0f6fc !important;
        margin: 0 !important;
        padding: 0 !important;
        font-family: var(--md-text-font, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif) !important;
      `;

      // Garante folha interna de estilos dentro do próprio widget (à prova de limpeza do head pelo MkDocs)
      if (!widget.querySelector("#da-widget-scoped-styles")) {
        const sc = document.createElement("style");
        sc.id = "da-widget-scoped-styles";
        sc.textContent = CSS_STYLES;
        widget.insertBefore(sc, widget.firstChild);
      }
    }
  }

  function garantirEstilosHead() {
    if (!document.getElementById("da-widget-styles")) {
      const style = document.createElement("style");
      style.id = "da-widget-styles";
      style.textContent = CSS_STYLES;
      if (document.head) {
        document.head.appendChild(style);
      }
    }
  }

  function montarWidget() {
    garantirEstilosHead();

    let bubble = document.getElementById("da-bubble-btn");
    let widget = document.getElementById("da-widget-root");

    // Se já existem e estão acoplados ao document.body ativo, apenas sincroniza
    if (bubble && widget && document.body && document.body.contains(bubble) && document.body.contains(widget)) {
      aplicarEstilosCriticos(widget, bubble, estado.aberto);
      if (estado.aberto) {
        widget.classList.add("open");
      } else {
        widget.classList.remove("open");
      }
      return;
    }

    // Se existiam referências desconectadas ou órfãs pelo swap do MkDocs, limpa
    if (bubble && (!document.body || !document.body.contains(bubble))) bubble.remove();
    if (widget && (!document.body || !document.body.contains(widget))) widget.remove();

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

    aplicarEstilosCriticos(widget, bubble, estado.aberto);

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
      estado.aberto = !estado.aberto;
      aplicarEstilosCriticos(widget, bubble, estado.aberto);
      if (estado.aberto) {
        widget.classList.add("open");
        input.focus();
      } else {
        widget.classList.remove("open");
      }
    });

    closeBtn.addEventListener("click", () => {
      estado.aberto = false;
      aplicarEstilosCriticos(widget, bubble, false);
      widget.classList.remove("open");
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
  function assinarDocumentObservable() {
    if (typeof window.document$ !== "undefined" && typeof window.document$.subscribe === "function") {
      window.document$.subscribe(() => {
        montarWidget();
      });
      return true;
    }
    return false;
  }

  // Tenta assinar imediatamente
  const assinado = assinarDocumentObservable();

  // Escutas de ciclo de vida do navegador e MkDocs SPA
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", montarWidget);
  } else {
    montarWidget();
  }

  window.addEventListener("load", () => {
    assinarDocumentObservable();
    montarWidget();
  });
  window.addEventListener("popstate", montarWidget);
  window.addEventListener("hashchange", montarWidget);
  window.addEventListener("pageshow", montarWidget);
  window.addEventListener("resize", () => {
    const bubble = document.getElementById("da-bubble-btn");
    const widget = document.getElementById("da-widget-root");
    if (widget && bubble) aplicarEstilosCriticos(widget, bubble, estado.aberto);
  });

  // Polling resiliente nos primeiros 3 segundos para garantir conexão ao document$ do MkDocs
  if (!assinado) {
    let tentativas = 0;
    const pollId = setInterval(() => {
      tentativas++;
      if (assinarDocumentObservable() || tentativas > 30) {
        clearInterval(pollId);
      }
    }, 100);
  }

  // MutationObserver como rede de proteção contra substituição de nós pelo MkDocs
  try {
    if (document.body) {
      new MutationObserver(() => {
        const b = document.getElementById("da-bubble-btn");
        const w = document.getElementById("da-widget-root");
        if (!b || !w || !document.body.contains(b) || !document.body.contains(w)) {
          montarWidget();
        } else {
          aplicarEstilosCriticos(w, b, estado.aberto);
          garantirEstilosHead();
        }
      }).observe(document.body, { childList: true, subtree: false });
    }
  } catch (e) {}
})();
