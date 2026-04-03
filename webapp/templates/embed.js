(function () {
  var script = document.currentScript;
  var baseUrl = (script && script.dataset.chatbotUrl) || script.src.replace(/\/embed\.js(\?.*)?$/, "");

  var root = document.createElement("div");
  root.id = "ebisudo-chatbot-root";
  root.setAttribute("data-ebisudo-chatbot", "true");

  var button = document.createElement("button");
  button.type = "button";
  button.textContent = "チャット";
  button.setAttribute("aria-label", "FAQチャットを開く");

  var frame = document.createElement("iframe");
  frame.src = baseUrl + "/widget";
  frame.title = "えびす堂 FAQチャット";
  frame.loading = "lazy";
  frame.style.display = "none";
  frame.setAttribute("aria-hidden", "true");

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
      border-radius: 999px !important;
      padding: 12px 18px !important;
      background: #9d1f24 !important;
      color: #fff !important;
      font-size: 14px !important;
      line-height: 1 !important;
      cursor: pointer !important;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18) !important;
    }
    #ebisudo-chatbot-root iframe {
      pointer-events: auto !important;
      width: min(360px, calc(100vw - 24px)) !important;
      height: min(540px, calc(100vh - 110px)) !important;
      max-width: calc(100vw - 24px) !important;
      max-height: calc(100vh - 110px) !important;
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
        height: min(70vh, 520px) !important;
      }
    }
  `;

  button.addEventListener("click", function () {
    var isHidden = frame.style.display === "none";
    frame.style.display = isHidden ? "block" : "none";
    frame.setAttribute("aria-hidden", isHidden ? "false" : "true");
  });

  root.appendChild(button);
  root.appendChild(frame);
  document.head.appendChild(style);
  document.body.appendChild(root);
})();
