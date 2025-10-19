// Основной объект приложения
const chatApp = {
  // Элементы DOM
  elements: {
    chatDiv: null,
    inputBox: null,
    sendBtn: null,
  },

  // URL API - используем proxy через Vite
  API_URL: "/api/tickets/",
  HEALTH_URL: "/api/health",

  // Инициализация приложения
  init() {
    this.elements.chatDiv = document.getElementById("chat");
    this.elements.inputBox = document.getElementById("inputBox");
    this.elements.sendBtn = document.getElementById("sendBtn");

    if (
      !this.elements.chatDiv ||
      !this.elements.inputBox ||
      !this.elements.sendBtn
    ) {
      console.error("❌ Ошибка инициализации: DOM элементы не найдены");
      return;
    }

    this.bindEvents();
    this.elements.inputBox.focus();
    console.log("✅ AI TechSupport App инициализирован с Vite");
    this.checkBackendStatus();
  },

  // Проверка состояния бэкенда
  async checkBackendStatus() {
    try {
      console.log("🔍 Проверка состояния бэкенда...");
      const response = await fetch(this.HEALTH_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log("✅ Бэкенд работает:", data);
      this.appendMessage(
        "bot",
        `Система готова к работе! База данных: ${data.database}, AI: ${data.ollama}`
      );
    } catch (error) {
      console.error("❌ Ошибка проверки бэкенда:", error);
      this.appendMessage(
        "bot",
        "❌ Не удалось подключиться к бэкенду. Запустите сервер на localhost:8000"
      );
    }
  },

  // Привязка событий
  bindEvents() {
    this.elements.sendBtn.addEventListener("click", () => {
      console.log("🖱️ Клик по кнопке отправки");
      this.sendMessage();
    });

    this.elements.inputBox.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        console.log("⌨️ Нажата клавиша Enter");
        this.sendMessage();
      }
    });
  },

  // Добавление сообщения в чат
  appendMessage(sender, message, metadata = {}) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;

    let messageHTML = this.escapeHtml(message).replace(/\n/g, "<br>");

    if (metadata.needsHuman) {
      msgDiv.classList.add("human-escalation");
      messageHTML = messageHTML;
      console.log("⚠️ Требуется вмешательство человека");
    }

    msgDiv.innerHTML = messageHTML;
    this.elements.chatDiv.appendChild(msgDiv);
    this.elements.chatDiv.scrollTop = this.elements.chatDiv.scrollHeight;
  },

  // Экранирование HTML
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  },

  // Показать индикатор набора
  showTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "message bot typing-indicator";
    typingDiv.id = "typingIndicator";
    typingDiv.textContent = "AI думает...";
    this.elements.chatDiv.appendChild(typingDiv);
    this.elements.chatDiv.scrollTop = this.elements.chatDiv.scrollHeight;
  },

  // Скрыть индикатор набора
  hideTypingIndicator() {
    const typingIndicator = document.getElementById("typingIndicator");
    if (typingIndicator) {
      typingIndicator.remove();
    }
  },

  // Отправка сообщения
  async sendMessage() {
    const text = this.elements.inputBox.value.trim();
    if (!text) {
      console.warn("⚠️ Пустое сообщение, отправка отменена");
      return;
    }

    console.log("📤 Отправка сообщения:", text);
    this.appendMessage("user", text);
    this.elements.inputBox.value = "";
    this.elements.sendBtn.disabled = true;

    this.showTypingIndicator();

    try {
      const response = await fetch(this.API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "user_" + Date.now(),
          message: text,
        }),
      });

      console.log("📥 Получен ответ, статус:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("📊 Данные ответа:", data);

      this.hideTypingIndicator();
      this.appendMessage("bot", data.response, {
        needsHuman: data.needs_human,
      });
    } catch (error) {
      console.error("❌ Ошибка при отправке:", error);
      this.hideTypingIndicator();
      this.appendMessage("bot", "❌ Ошибка соединения с сервером");
    } finally {
      this.elements.sendBtn.disabled = false;
      this.elements.inputBox.focus();
    }
  },

  // Загрузка примера
  loadExample(text) {
    this.elements.inputBox.value = text;
    this.elements.inputBox.focus();
    console.log("📝 Загружен пример:", text);
  },

  // Очистка чата
  clearChat() {
    this.elements.chatDiv.innerHTML =
      '<div class="message bot">Чат очищен. Чем могу помочь?</div>';
    console.log("🧹 Чат очищен");
  },
};

// Глобальные функции
window.loadExample = function (text) {
  chatApp.loadExample(text);
};

window.clearChat = function () {
  chatApp.clearChat();
};

// Инициализация при загрузке DOM
document.addEventListener("DOMContentLoaded", function () {
  console.log("🌐 DOM загружен, инициализация с Vite...");
  chatApp.init();
});
