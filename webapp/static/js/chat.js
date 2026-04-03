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

function wait(ms) {
  return new Promise(function (resolve) {
    window.setTimeout(resolve, ms);
  });
}

function easeOutCubic(value) {
  return 1 - Math.pow(1 - value, 3);
}

function revealTextSmoothly(paragraph, text, messages) {
  const characters = Array.from(text);
  const totalChars = characters.length;
  const punctuationCount = (text.match(/[。、！？]/g) || []).length;
  const duration = Math.min(Math.max(totalChars * 16 + punctuationCount * 40, 650), 2800);
  const start = performance.now();

  return new Promise(function (resolve) {
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = easeOutCubic(progress);
      const visibleCount = Math.max(1, Math.floor(totalChars * eased));

      paragraph.textContent = characters.slice(0, visibleCount).join("");
      messages.scrollTop = messages.scrollHeight;

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        paragraph.textContent = text;
        messages.scrollTop = messages.scrollHeight;
        resolve();
      }
    }

    window.requestAnimationFrame(step);
  });
}

function appendThinkingMessage() {
  const messages = document.getElementById("messages");
  const article = document.createElement("article");
  article.className = "message bot thinking";

  const bubble = document.createElement("div");
  bubble.className = "thinking-bubble";
  bubble.setAttribute("aria-label", "回答を考えています");

  for (let index = 0; index < 3; index += 1) {
    const dot = document.createElement("span");
    dot.className = "thinking-dot";
    bubble.appendChild(dot);
  }

  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
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

async function appendBotMessage(text, sources = []) {
  const messages = document.getElementById("messages");
  const article = document.createElement("article");
  article.className = "message bot";

  const body = document.createElement("div");
  const paragraph = document.createElement("p");
  paragraph.className = "typing-text";
  body.appendChild(paragraph);
  article.appendChild(body);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;

  const cursor = document.createElement("span");
  cursor.className = "typing-cursor";
  cursor.textContent = " ";
  paragraph.appendChild(cursor);
  await revealTextSmoothly(paragraph, text, messages);
  paragraph.appendChild(cursor);
  await wait(120);
  cursor.remove();

  if (sources.length > 0) {
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
    messages.scrollTop = messages.scrollHeight;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("chat-form");
  const textarea = document.getElementById("message");
  let isComposing = false;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = textarea.value.trim();
    if (!message) {
      return;
    }

    appendMessage("user", message);
    textarea.value = "";

    try {
      const thinkingMessage = appendThinkingMessage();
      const result = await sendMessage(message);
      thinkingMessage.remove();
      await appendBotMessage(result.answer, result.sources || []);
    } catch (error) {
      const messages = document.getElementById("messages");
      const thinkingMessage = messages.querySelector(".message.thinking:last-child");
      if (thinkingMessage) {
        thinkingMessage.remove();
      }
      await appendBotMessage(error.message || "エラーが発生しました。");
    }
  });

  textarea.addEventListener("compositionstart", function () {
    isComposing = true;
  });

  textarea.addEventListener("compositionend", function () {
    isComposing = false;
  });

  textarea.addEventListener("keydown", function (event) {
    if (event.isComposing || isComposing || event.keyCode === 229) {
      return;
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
});
