async function sendMessage(message) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "エラーが発生しました。");
  }
  return data;
}

function appendMessage(role, text, sources = []) {
  const messages = document.getElementById("messages");
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const body = document.createElement("div");
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  body.appendChild(paragraph);

  if (role === "bot" && sources.length > 0) {
    const sourceBox = document.createElement("div");
    sourceBox.className = "sources";

    const label = document.createElement("strong");
    label.textContent = "参考ページ: ";
    sourceBox.appendChild(label);

    sources.forEach((source, index) => {
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = source.title || source.url;
      sourceBox.appendChild(link);

      if (index < sources.length - 1) {
        sourceBox.appendChild(document.createTextNode(" / "));
      }
    });

    body.appendChild(sourceBox);
  }

  article.appendChild(body);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("chat-form");
  const textarea = document.getElementById("message");

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = textarea.value.trim();
    if (!message) {
      return;
    }

    appendMessage("user", message);
    textarea.value = "";

    try {
      appendMessage("bot", "確認中です...");
      const messages = document.getElementById("messages");
      messages.lastElementChild.remove();

      const result = await sendMessage(message);
      appendMessage("bot", result.answer, result.sources || []);
    } catch (error) {
      appendMessage("bot", error.message || "エラーが発生しました。");
    }
  });
});

