/* RESUMES MANAGER FOR OFFICIALS */
        async function loadOfficialResumes() {
            const listDiv = document.getElementById('resumesReceivedList');
            if (!listDiv) return;
            try {
                const response = await fetch("http://127.0.0.1:8000/api/resumes", {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (data.success) {
                    if (data.resumes.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center py-4">No resumes received in vector index yet.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Candidate Profile</th>
                                        <th>Skills Detected</th>
                                        <th>Document</th>
                                        <th style="width: 100px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.resumes.forEach(resume => {
                        let linkHtml = '';
                        if (resume.resume_url) {
                            let linkUrl = resume.resume_url;
                            if (!linkUrl.startsWith('http://') && !linkUrl.startsWith('https://')) {
                                linkUrl = `http://127.0.0.1:8000/uploads/${linkUrl}`;
                            }
                            linkHtml = `<a href="${encodeURI(linkUrl)}" target="_blank" class="btn btn-sm btn-primary"><i class="bi bi-file-pdf"></i> View PDF</a>`;
                        } else {
                            linkHtml = `<span class="text-muted">No attachment</span>`;
                        }

                        html += `
                            <tr id="resume-row-${resume.id}">
                                <td class="fw-bold text-light">${resume.name}</td>
                                <td><span style="font-size: 13.5px; color: var(--text-secondary);">${resume.skills || 'None'}</span></td>
                                <td>${linkHtml}</td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="deleteResume('${resume.id}')"><i class="bi bi-trash"></i> Delete</button>
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
                    listDiv.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
                }
            } catch (err) {
                console.error("Failed to load resumes", err);
                listDiv.innerHTML = '<p class="text-danger text-center">Failed to fetch uploaded resumes.</p>';
            }
        }

        async function deleteResume(id) {
            if (!confirm("Are you sure you want to delete this candidate resume? This deletes it from vector database index.")) return;
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/resumes/${id}`, {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (data.success) {
                    showNotification("Resume index deleted successfully.", "success");
                    
                    // Fade out row animation
                    const row = document.getElementById(`resume-row-${id}`);
                    if (row) {
                        row.style.transition = "all 0.3s ease";
                        row.style.opacity = "0";
                        row.style.transform = "translateX(20px)";
                        setTimeout(() => row.remove(), 300);
                    }
                    getResumeCount();
                    
                    // Delay reload slightly for smooth layout transition
                    setTimeout(loadOfficialResumes, 400);
                } else {
                    showNotification("Failed to delete candidate profile.", "error");
                }
            } catch (err) {
                console.error("Delete failed", err);
                showNotification("Backend connection issue during delete request.", "error");
            }
        }
