/* REPLAY EMAIL MODAL CONTROLLERS */
        function openReplyModal(emailId) {
            const email = officialEmailsCache.find(e => e.id === emailId);
            if (!email) {
                showNotification("Message details not found.", "error");
                return;
            }

            document.getElementById('replyEmailId').value = email.id;
            document.getElementById('replyToEmail').value = email.sender_email;
            document.getElementById('replySubject').value = `Re: ${email.subject}`;
            document.getElementById('replyMessageText').value = '';
            
            document.getElementById('replyOriginalSender').innerText = `From: ${email.sender_name} (${email.sender_email})`;
            document.getElementById('replyOriginalSubject').innerText = `Subject: ${email.subject}`;
            document.getElementById('replyOriginalMessage').innerText = email.message;

            const modalOverlay = document.getElementById('replyModalOverlay');
            modalOverlay.style.display = 'flex';
        }

        function closeReplyModal() {
            document.getElementById('replyModalOverlay').style.display = 'none';
        }

        async function submitReply(event) {
            event.preventDefault();
            const emailId = document.getElementById('replyEmailId').value;
            const toEmail = document.getElementById('replyToEmail').value;
            const subject = document.getElementById('replySubject').value;
            const text = document.getElementById('replyMessageText').value.trim();

            if (!text) {
                showNotification("Reply message cannot be empty.", "error");
                return;
            }

            const savedUser = localStorage.getItem('resumeUser');
            let senderUsername = "official";
            if (savedUser) {
                const userObj = JSON.parse(savedUser);
                senderUsername = userObj.username || "official";
            }

            showNotification(`Sending reply...`, 'success');

            try {
                const response = await fetch("http://127.0.0.1:8000/api/replies", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message_id: emailId,
                        sender_username: senderUsername,
                        reply_text: text
                    })
                });
                const data = await response.json();
                if (data.success) {
                    closeReplyModal();
                    showNotification(`Professional reply sent successfully to ${toEmail}!`, 'success');
                } else {
                    showNotification(data.message || "Failed to save reply on server.", "error");
                }
            } catch (err) {
                console.error("Failed to send reply", err);
                showNotification("Network error occurred while sending reply.", "error");
            }
        }
