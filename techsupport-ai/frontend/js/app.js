// Основной объект приложения
const chatApp = {
    // Элементы DOM
    elements: {
        chatDiv: document.getElementById("chat"),
        inputBox: document.getElementById("inputBox"),
        sendBtn: document.getElementById("sendBtn")
    },

    // URL API
    apiUrl: "http://localhost:8000/tickets/",

    // Инициализация приложения
    init() {
        this.bindEvents();
        this.elements.inputBox.focus();
        console.log("AI TechSupport App инициализирован");
    },

    // Привязка событий
    bindEvents() {
        this.elements.sendBtn.addEventListener("click", () => this.sendMessage());
        this.elements.inputBox.addEventListener("keypress", (e) => {
            if (e.key === "Enter") this.sendMessage();
        });
    },

    // Добавление сообщения в чат
    appendMessage(sender, message, metadata = {}) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender}`;
        
        let messageHTML = this.escapeHtml(message).replace(/\n/g, '<br>');
        
        // Только предупреждение если нужен человек
        if (metadata.needsHuman) {
            msgDiv.classList.add('human-escalation');
            messageHTML = '⚠️ ' + messageHTML;
        }
        
        msgDiv.innerHTML = messageHTML;
        this.elements.chatDiv.appendChild(msgDiv);
        this.elements.chatDiv.scrollTop = this.elements.chatDiv.scrollHeight;
    },

    // Экранирование HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Показать индикатор набора сообщения
    showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "message bot typing-indicator";
        typingDiv.id = "typingIndicator";
        typingDiv.textContent = "AI думает...";
        typingDiv.style.display = 'block';
        this.elements.chatDiv.appendChild(typingDiv);
        this.elements.chatDiv.scrollTop = this.elements.chatDiv.scrollHeight;
    },

    // Скрыть индикатор набора сообщения
    hideTypingIndicator() {
        const typingIndicator = document.getElementById("typingIndicator");
        if (typingIndicator) {
            typingIndicator.remove();
        }
    },

    // Отправка сообщения
    async sendMessage() {
        const text = this.elements.inputBox.value.trim();
        if (!text) return;

        this.appendMessage("user", text);
        this.elements.inputBox.value = "";
        this.elements.sendBtn.disabled = true;
        
        this.showTypingIndicator();

        try {
            const response = await fetch(this.apiUrl, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ 
                    user_id: "user_" + Date.now(), 
                    message: text 
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.hideTypingIndicator();
            
            this.appendMessage("bot", data.response, {
                needsHuman: data.needs_human
            });
            
        } catch (error) {
            this.hideTypingIndicator();
            this.appendMessage("bot", "❌ Ошибка соединения с сервером. Проверьте, запущен ли бэкенд на localhost:8000");
            console.error("Ошибка:", error);
        } finally {
            this.elements.sendBtn.disabled = false;
            this.elements.inputBox.focus();
        }
    },

    // Загрузка примера
    loadExample(text) {
        this.elements.inputBox.value = text;
        this.elements.inputBox.focus();
    },

    // Очистка чата
    clearChat() {
        this.elements.chatDiv.innerHTML = '<div class="message bot">Чат очищен. Чем могу помочь?</div>';
    }
};

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    chatApp.init();
});

// Глобальные функции для кнопок
function loadExample(text) {
    chatApp.loadExample(text);
}

function clearChat() {
    chatApp.clearChat();
}