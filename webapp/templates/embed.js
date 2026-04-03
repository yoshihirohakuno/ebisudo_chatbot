(function () {
  var script = document.currentScript;
  var baseUrl = (script && script.dataset.chatbotUrl) || script.src.replace(/\/embed\.js(\?.*)?$/, "");

  var root = document.createElement("div");
  root.id = "ebisudo-chatbot-root";

  var button = document.createElement("button");
  button.type = "button";
  button.textContent = "チャット";
  button.setAttribute("aria-label", "FAQチャットを開く");

  var frame = document.createElement("iframe");
  frame.src = baseUrl + "/widget";
  frame.title = "えびす堂 FAQチャット";
  frame.loading = "lazy";
  frame.style.display = "none";

  var style = document.createElement("style");
  style.textContent = `
    #ebisudo-chatbot-root {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 9999;
      font-family: sans-serif;
    }
    #ebisudo-chatbot-root button {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      background: #9d1f24;
      color: #fff;
      font-size: 14px;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    }
    #ebisudo-chatbot-root iframe {
      width: min(380px, calc(100vw - 32px));
      height: min(620px, calc(100vh - 90px));
      border: none;
      border-radius: 20px;
      margin-top: 12px;
      background: #fff;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
    }
  `;

  button.addEventListener("click", function () {
    frame.style.display = frame.style.display === "none" ? "block" : "none";
  });

  root.appendChild(button);
  root.appendChild(frame);
  document.head.appendChild(style);
  document.body.appendChild(root);
})();

