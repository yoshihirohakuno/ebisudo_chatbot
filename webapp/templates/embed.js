(function () {
  function findScriptElement() {
    if (document.currentScript) {
      return document.currentScript;
    }

    var scripts = document.getElementsByTagName("script");
    for (var index = scripts.length - 1; index >= 0; index -= 1) {
      var candidate = scripts[index];
      if (candidate.src && /\/embed\.js(\?.*)?$/.test(candidate.src)) {
        return candidate;
      }
    }

    return null;
  }

  function initChatbot() {
    if (document.getElementById("ebisudo-chatbot-root")) {
      return;
    }

    var script = findScriptElement();
    if (!script || !script.src) {
      return;
    }

    var baseUrl = script.dataset.chatbotUrl || script.src.replace(/\/embed\.js(\?.*)?$/, "");

    var root = document.createElement("div");
    root.id = "ebisudo-chatbot-root";
    root.setAttribute("data-ebisudo-chatbot", "true");

    var button = document.createElement("button");
    button.type = "button";
    button.textContent = "Q";
    button.setAttribute("aria-label", "FAQチャットを開く");

    var frame = document.createElement("iframe");
    frame.title = "えびす堂 FAQチャット";
    frame.loading = "lazy";
    frame.style.display = "none";
    frame.setAttribute("aria-hidden", "true");
    frame.dataset.src = baseUrl + "/widget";

    var style = document.createElement("style");
    style.textContent = `
    #ebisudo-chatbot-root {
      position: fixed !important;
      right: 16px !important;
      bottom: 16px !important;
      top: auto !important;
      left: auto !important;
      z-index: 2147483000 !important;
      font-family: sans-serif !important;
      display: flex !important;
      flex-direction: column !important;
      align-items: flex-end !important;
      justify-content: flex-end !important;
      gap: 10px !important;
      width: auto !important;
      max-width: calc(100vw - 24px) !important;
      pointer-events: none !important;
    }
    #ebisudo-chatbot-root button {
      pointer-events: auto !important;
      border: none !important;
      position: relative !important;
      border-radius: 999px !important;
      width: 68px !important;
      height: 68px !important;
      padding: 0 !important;
      background: linear-gradient(180deg, #62a8ff 0%, #3a7bd5 100%) !important;
      color: #fff !important;
      font-family: "Hiragino Maru Gothic ProN", "Yu Gothic", sans-serif !important;
      font-size: 34px !important;
      font-weight: 800 !important;
      line-height: 1 !important;
      cursor: pointer !important;
      box-shadow: 0 12px 32px rgba(58, 123, 213, 0.32) !important;
      display: grid !important;
      place-items: center !important;
    }
    #ebisudo-chatbot-root button::after {
      content: "" !important;
      position: absolute !important;
      right: 10px !important;
      bottom: -6px !important;
      width: 18px !important;
      height: 18px !important;
      background: #3a7bd5 !important;
      border-radius: 4px 14px 14px 14px !important;
      transform: rotate(38deg) !important;
    }
    #ebisudo-chatbot-root iframe {
      pointer-events: auto !important;
      width: min(360px, calc(100vw - 24px)) !important;
      height: min(640px, calc(100vh - 90px)) !important;
      max-width: calc(100vw - 24px) !important;
      max-height: calc(100vh - 90px) !important;
      border: none !important;
      border-radius: 18px !important;
      background: #fff !important;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22) !important;
    }
    @media (max-width: 640px) {
      #ebisudo-chatbot-root {
        right: 12px !important;
        bottom: 12px !important;
      }
      #ebisudo-chatbot-root iframe {
        width: min(92vw, 360px) !important;
        height: min(84vh, 700px) !important;
        max-height: calc(100vh - 24px) !important;
      }
    }
  `;

    button.addEventListener("click", function () {
      var isHidden = frame.style.display === "none";
      if (isHidden && !frame.src) {
        frame.src = frame.dataset.src;
      }
      frame.style.display = isHidden ? "block" : "none";
      frame.setAttribute("aria-hidden", isHidden ? "false" : "true");
    });

    root.appendChild(button);
    root.appendChild(frame);
    document.head.appendChild(style);
    document.body.appendChild(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChatbot, { once: true });
  } else {
    initChatbot();
  }
})();
