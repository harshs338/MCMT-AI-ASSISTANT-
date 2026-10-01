const messageForm = document.querySelector(".message-form");
const messageInput = document.querySelector(
    '.message-form input[name="content"]'
);
const chatMessages = document.querySelector(".student-messages");

messageForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const content = messageInput.value.trim();

    if (!content) {
        return;
    }

    const formData = new FormData(messageForm);

    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.innerHTML = `
        <span class="message-content">${content}</span>
    `;

    chatMessages.appendChild(userMessage);

    messageInput.value = "";

    const thinkingMessage = document.createElement("div");
    thinkingMessage.className = "ai-message";
    thinkingMessage.textContent = "AI is thinking...";

    chatMessages.appendChild(thinkingMessage);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(messageForm.action, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            thinkingMessage.textContent = data.ai_response;
        } else {
            thinkingMessage.textContent =
                "Sorry, something went wrong.";
        }

    } catch (error) {
        thinkingMessage.textContent =
            "Sorry, I could not connect to the server.";
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
});