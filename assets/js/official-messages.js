/* INQUIRIES & simulated REPLY FOR MESSAGES PAGE (OFFICIAL) */
        let officialEmailsCache = [];

        async function loadOfficialEmails() {
            const listDiv = document.getElementById('emailsReceivedList');
            const messagesCounter = document.getElementById('messagesCount');
            if (!listDiv) return;
            try {
                const response = await fetch("http://127.0.0.1:8000/api/emails", {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (Array.isArray(data)) {
                    officialEmailsCache = data;
                    if (messagesCounter) {
                        messagesCounter.innerText = data.length;
                    }
                    if (data.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center py-4">No inquiry messages received in Inbox.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Candidate Info</th>
                                        <th>Inquiry Subject</th>
                                        <th>Details</th>
                                        <th style="width: 180px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.forEach(email => {
                        html += `
                            <tr id="email-row-${email.id}">
                                <td style="font-size: 13px; color: var(--text-secondary); min-width: 140px;">${email.timestamp || ''}</td>
                                <td>
                                    <div class="fw-bold text-light">${email.sender_name}</div>
                                    <div style="font-size: 12px; color: var(--text-secondary);">${email.sender_email}</div>
                                </td>
                                <td class="fw-semibold text-info">${email.subject}</td>
                                <td style="white-space: pre-wrap; font-size: 13.5px; color: var(--text-secondary);">${email.message}</td>
                                <td>
                                    <div class="d-flex gap-2">
                                        <button class="btn btn-sm btn-primary" onclick="openReplyModal('${email.id}')"><i class="bi bi-reply-fill"></i> Reply</button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteEmail('${email.id}')"><i class="bi bi-trash"></i> Delete</button>
                                    </div>
                                </td>
                            </tr>
                        `;
                    });

                    html += `
                                </tbody>
                            </table>
                        </div>
                    `;
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<p class="text-danger text-center">Failed to parse inbox metrics.</p>`;
                }
            } catch (err) {
                console.error("Failed to load emails", err);
                listDiv.innerHTML = '<p class="text-danger text-center">Failed to sync message database.</p>';
            }
        }

        async function deleteEmail(id) {
            if (!confirm("Are you sure you want to delete this candidate email?")) return;
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/emails/${id}`, {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (data.success) {
                    showNotification("Email inquiry deleted from Inbox.", "success");
                    
                    const row = document.getElementById(`email-row-${id}`);
                    if (row) {
                        row.style.transition = "all 0.3s ease";
                        row.style.opacity = "0";
                        row.style.transform = "translateX(20px)";
                        setTimeout(() => row.remove(), 300);
                    }
                    setTimeout(loadOfficialEmails, 400);
                } else {
                    showNotification(data.message || "Failed to remove email.", "error");
                }
            } catch (err) {
                console.error("Delete failed", err);
                showNotification("Network failure during deletion request.", "error");
            }
        }
