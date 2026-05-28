/* CANDIDATE PORTAL METRIC FEEDS & DISPLAYS */
        async function loadCandidateJobDescriptions() {
            const listDiv = document.getElementById('candidateJdList');
            const openCounter = document.getElementById('candidateOpenRolesCount');
            const deptCounter = document.getElementById('candidateDeptCount');
            if (!listDiv) return;
            try {
                const response = await fetch("http://127.0.0.1:8000/api/job_descriptions");
                const data = await response.json();
                if (data.success) {
                    // Update dynamic counts inside Candidate Dashboard
                    if (openCounter) {
                        openCounter.innerText = data.job_descriptions.length;
                    }
                    
                    // Dynamic unique department counting
                    if (deptCounter) {
                        const depts = new Set();
                        data.job_descriptions.forEach(jd => {
                            if (jd.department) depts.add(jd.department.trim().toLowerCase());
                        });
                        deptCounter.innerText = depts.size;
                    }

                    if (data.job_descriptions.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center py-4">No open job positions posted by ITL Recruiters currently.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Job Title</th>
                                        <th>Department / Squad</th>
                                        <th>Requirements / Overview</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.job_descriptions.forEach(jd => {
                        html += `
                            <tr>
                                <td class="fw-bold text-info">${jd.title}</td>
                                <td class="fw-bold text-light">${jd.department}</td>
                                <td style="white-space: pre-wrap; font-size: 13.5px; color: var(--text-secondary);">${jd.description}</td>
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
                    listDiv.innerHTML = `<p class="text-danger text-center">Failed to sync open job positions.</p>`;
                }
            } catch (err) {
                console.error("Failed to load candidate JDs", err);
                listDiv.innerHTML = '<p class="text-danger text-center">Failed to contact Recruiter server.</p>';
            } finally {
                loadCandidateReplies();
            }
        }

        async function loadCandidateReplies() {
            const listDiv = document.getElementById('candidateRepliesList');
            if (!listDiv) return;

            const savedUser = localStorage.getItem('resumeUser');
            if (!savedUser) {
                listDiv.innerHTML = '<p class="text-muted">Please log in to view your messages and replies.</p>';
                return;
            }

            const userObj = JSON.parse(savedUser);
            const username = userObj.username;

            try {
                const response = await fetch(`http://127.0.0.1:8000/api/replies/${username}`);
                const data = await response.json();

                if (data.success) {
                    if (!data.replies || data.replies.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center py-4">No support inquiries or recruiter replies found.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>My Inquiry</th>
                                        <th>Recruiter Reply</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.replies.forEach(reply => {
                        const faqBadge = reply.is_faq
                            ? `<span class="faq-public-badge ms-2"><i class="bi bi-globe2 me-1"></i>Public FAQ</span>`
                            : '';
                        html += `
                            <tr>
                                <td style="font-size: 13px; color: var(--text-secondary); min-width: 140px;">${reply.created_at || ''}</td>
                                <td>
                                    <div class="fw-semibold text-info">${reply.original_subject || 'Inquiry'}</div>
                                    <div style="font-size: 13px; color: var(--text-secondary); white-space: pre-wrap;">${reply.original_message || ''}</div>
                                </td>
                                <td>
                                    <div class="fw-bold text-success"><i class="bi bi-reply-fill"></i> HR Response (from ${reply.sender_username}):${faqBadge}</div>
                                    <div style="font-size: 13.5px; color: #e2e8f0; white-space: pre-wrap; background: rgba(0, 180, 216, 0.05); padding: 10px; border-radius: 8px; margin-top: 5px; border: 1px solid rgba(0, 180, 216, 0.1);">${reply.reply_text}</div>
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
                    listDiv.innerHTML = '<p class="text-danger text-center">Failed to sync message replies.</p>';
                }
            } catch (err) {
                console.error("Failed to load candidate replies", err);
                listDiv.innerHTML = '<p class="text-danger text-center">Failed to sync message database.</p>';
            }
        }
