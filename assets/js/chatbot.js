/* FLOATING CHATBOT CONTROLLER */
        function toggleChatbot() {
            const chatWindow = document.getElementById('chatbotWindow');
            const toggleBtn = document.getElementById('chatbotToggleBtn');
            if (chatWindow.style.display === 'none' || chatWindow.style.display === '') {
                chatWindow.style.display = 'flex';
                toggleBtn.style.transform = 'scale(0.9) rotate(90deg)';
                setTimeout(() => document.getElementById('chatbotInput').focus(), 100);
            } else {
                chatWindow.style.display = 'none';
                toggleBtn.style.transform = 'scale(1) rotate(0deg)';
            }
        }

        async function sendChatbotMessage() {
            const input = document.getElementById('chatbotInput');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';

            const chatBody = document.getElementById('chatbotBody');

            const userMsgDiv = document.createElement('div');
            userMsgDiv.style.cssText = "background: linear-gradient(135deg, #0072ff 0%, #00c6ff 100%); border-radius: 12px; padding: 12px; font-size: 14px; max-width: 85%; align-self: flex-end; color: white; box-shadow: 0 4px 12px rgba(0, 114, 255, 0.2); font-weight: 500;";
            userMsgDiv.innerText = message;
            chatBody.appendChild(userMsgDiv);
            chatBody.scrollTop = chatBody.scrollHeight;

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-msg-ai';
            loadingDiv.style.cssText = "border-radius: 12px; padding: 12px; font-size: 14px; max-width: 85%; align-self: flex-start; display: flex; align-items: center; gap: 8px;";
            loadingDiv.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" style="width:12px; height:12px; border-width:2px;"></span> AI is thinking...';
            chatBody.appendChild(loadingDiv);
            chatBody.scrollTop = chatBody.scrollHeight;

            try {
                const response = await fetch("http://127.0.0.1:8000/ask_ai", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ question: message })
                });

                const data = await response.json();
                chatBody.removeChild(loadingDiv);

                const responseDiv = document.createElement('div');
                responseDiv.className = 'chat-msg-ai';
                responseDiv.style.cssText = "border-radius: 12px; padding: 12px; font-size: 14px; max-width: 85%; align-self: flex-start; white-space: pre-wrap; font-weight: 500;";
                responseDiv.innerText = data.answer || "No response received.";
                chatBody.appendChild(responseDiv);
                chatBody.scrollTop = chatBody.scrollHeight;
            } catch (error) {
                console.error("Chatbot failed", error);
                chatBody.removeChild(loadingDiv);

                const responseDiv = document.createElement('div');
                responseDiv.style.cssText = "background: rgba(255,77,77,0.1); border: 1px solid rgba(255,77,77,0.25); border-radius: 12px; padding: 12px; font-size: 14px; max-width: 85%; align-self: flex-start; color: var(--accent-red); font-weight: 500;";
                responseDiv.innerText = "Failed to sync query with support server.";
                chatBody.appendChild(responseDiv);
                chatBody.scrollTop = chatBody.scrollHeight;
            }
        }
