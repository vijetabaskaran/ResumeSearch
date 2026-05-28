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
                    // Refresh conversation history after sending
                    loadSupportReplies();
                } else {
                    showNotification(data.message || "Failed to dispatch email support.", "error");
                }
            } catch (err) {
                console.error("Support failed", err);
                showNotification("Could not dispatch message to recruitment team.", "error");
            }
        }

        /**
         * Load and render this candidate's full conversation history
         * (submitted messages + any official replies) in #supportRepliesList.
         * Reuses GET /api/replies/{username} — no new API needed.
         */
        async function loadSupportReplies() {
            const listDiv = document.getElementById('supportRepliesList');
            if (!listDiv) return;

            const savedUser = localStorage.getItem('resumeUser');
            if (!savedUser) {
                listDiv.innerHTML = '<p class="text-muted text-center py-3">Please log in to view your conversation history.</p>';
                return;
            }

            const userObj  = JSON.parse(savedUser);
            const username = userObj.username;

            listDiv.innerHTML = `
                <div class="d-flex align-items-center justify-content-center gap-2 text-secondary py-3">
                    <div class="spinner-border spinner-border-sm text-info" role="status"></div>
                    Loading conversation...
                </div>`;

            try {
                const res  = await fetch(`http://127.0.0.1:8000/api/replies/${username}`);
                const data = await res.json();

                if (!data.success) {
                    listDiv.innerHTML = '<p class="text-danger text-center py-3">Failed to load conversation history.</p>';
                    return;
                }

                const replies = data.replies || [];

                if (replies.length === 0) {
                    listDiv.innerHTML = `
                        <div class="text-center py-4">
                            <i class="bi bi-chat-dots" style="font-size: 36px; color: rgba(255,255,255,0.12);"></i>
                            <p class="text-secondary mt-2 mb-0" style="font-size: 13.5px;">No replies yet.</p>
                            <p class="text-muted" style="font-size: 12px;">Once a recruiter replies to your inquiry, it will appear here.</p>
                        </div>`;
                    return;
                }

                let html = `<div class="support-timeline">`;
                replies.forEach(reply => {
                    const faqBadge = reply.is_faq
                        ? `<span class="faq-public-badge ms-2"><i class="bi bi-globe2 me-1"></i>Public FAQ</span>`
                        : '';
                    html += `
                        <div class="support-timeline-item">
                            <!-- Candidate's original message -->
                            <div class="support-msg-block support-msg-candidate">
                                <div class="support-msg-meta">
                                    <i class="bi bi-person-circle me-2 text-info"></i>
                                    <span class="fw-semibold text-info">${escSupportHtml(reply.original_subject || 'Your Inquiry')}</span>
                                    <span class="support-msg-time ms-auto">${reply.created_at || ''}</span>
                                </div>
                                <div class="support-msg-body">${escSupportHtml(reply.original_message || '')}</div>
                            </div>
                            <!-- Official reply -->
                            <div class="support-msg-block support-msg-official mt-2">
                                <div class="support-msg-meta">
                                    <i class="bi bi-reply-fill me-2 text-success"></i>
                                    <span class="fw-semibold text-success">Recruiter Response</span>
                                    <span class="text-secondary ms-2" style="font-size: 12px;">from ${escSupportHtml(reply.sender_username || 'official')}</span>
                                    ${faqBadge}
                                    <span class="support-msg-time ms-auto">${reply.created_at || ''}</span>
                                </div>
                                <div class="support-msg-body support-reply-body">${escSupportHtml(reply.reply_text || '')}</div>
                            </div>
                        </div>`;
                });
                html += `</div>`;
                listDiv.innerHTML = html;

            } catch (err) {
                console.error("Failed to load support replies", err);
                listDiv.innerHTML = '<p class="text-danger text-center py-3">Could not connect to server.</p>';
            }
        }

        function escSupportHtml(str) {
            if (!str) return '';
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }
