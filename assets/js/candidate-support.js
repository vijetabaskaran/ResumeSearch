/* RECRUITMENT INQUIRY SUPPORT SENDER */
        async function sendHREmail(event) {
            event.preventDefault();
            const subject = document.getElementById('emailSubject').value.trim();
            const message = document.getElementById('emailMessage').value.trim();

            const savedUser = localStorage.getItem('resumeUser');
            let senderName = "Anonymous Candidate";
            let senderEmail = "candidate@idealtechlabs.com";
            let senderUsername = "";
            if (savedUser) {
                const userObj = JSON.parse(savedUser);
                senderName = userObj.name || userObj.username;
                senderEmail = `${userObj.username}@idealtechlabs.com`;
                senderUsername = userObj.username;
            }

            try {
                const response = await fetch("http://127.0.0.1:8000/api/send_email", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        sender_name: senderName,
                        sender_email: senderEmail,
                        sender_username: senderUsername,
                        subject: subject,
                        message: message
                    })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification("Inquiry sent successfully to Recruiters!", "success");
                    document.getElementById('emailSubject').value = '';
                    document.getElementById('emailMessage').value = '';
                } else {
                    showNotification(data.message || "Failed to dispatch email support.", "error");
                }
            } catch (err) {
                console.error("Support failed", err);
                showNotification("Could not dispatch message to recruitment team.", "error");
            }
        }
