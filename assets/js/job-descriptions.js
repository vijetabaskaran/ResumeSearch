/* JOB DESCRIPTION MANAGEMENT FUNCTIONS */
        let currentJDMatches = [];
        let currentJDTitle = "";

        function toggleJDMethod(method) {
            const textGroup = document.getElementById('jdTextGroup');
            const fileGroup = document.getElementById('jdFileGroup');
            const descriptionInput = document.getElementById('jdDescription');
            const fileInput = document.getElementById('jdFile');
            
            if (method === 'text') {
                textGroup.style.display = 'block';
                fileGroup.style.display = 'none';
                descriptionInput.setAttribute('required', 'true');
                fileInput.removeAttribute('required');
                fileInput.value = '';
            } else {
                textGroup.style.display = 'none';
                fileGroup.style.display = 'block';
                descriptionInput.removeAttribute('required');
                descriptionInput.value = '';
                fileInput.setAttribute('required', 'true');
            }
        }

        async function createJobDescription(event) {
            event.preventDefault();
            const title = document.getElementById('jdTitle').value.trim();
            const department = document.getElementById('jdDepartment').value.trim();
            const method = document.querySelector('input[name="jdMethod"]:checked').value;

            if (!title || !department) {
                showNotification("Title and Department are required.", "error");
                return;
            }

            const formData = new FormData();
            formData.append("title", title);
            formData.append("department", department);

            if (method === 'text') {
                const description = document.getElementById('jdDescription').value.trim();
                if (!description) {
                    showNotification("Please provide JD description text.", "error");
                    return;
                }
                formData.append("description", description);
            } else {
                const fileInput = document.getElementById('jdFile');
                const file = fileInput.files[0];
                if (!file) {
                    showNotification("Please select job requirement document.", "error");
                    return;
                }
                formData.append("file", file);
            }

            showNotification("Processing and saving Job Description...", "success");

            try {
                const response = await fetch("http://127.0.0.1:8000/api/job_descriptions", {
                    method: "POST",
                    headers: { "X-User-Role": (JSON.parse(localStorage.getItem('resumeUser') || '{}')).role || '' },
                    body: formData
                });
                const data = await response.json();
                if (data.success) {
                    showNotification("Job description created successfully!", "success");
                    document.getElementById('jdTitle').value = '';
                    document.getElementById('jdDepartment').value = '';
                    document.getElementById('jdDescription').value = '';
                    document.getElementById('jdFile').value = '';
                    
                    // Reset to text input
                    const textRadio = document.getElementById('jdMethodText');
                    textRadio.checked = true;
                    toggleJDMethod('text');

                    loadJobDescriptions();
                } else {
                    showNotification(data.message || "Failed to create JD.", "error");
                }
            } catch (err) {
                console.error("Failed to create JD", err);
                showNotification("FastAPI backend connection failure during JD create.", "error");
            }
        }

        async function loadJobDescriptions() {
            const listDiv = document.getElementById('jdsList');
            const activeCounter = document.getElementById('jdsCount');
            if (!listDiv) return;
            try {
                const response = await fetch("http://127.0.0.1:8000/api/job_descriptions");
                const data = await response.json();
                if (data.success) {
                    if (activeCounter) {
                        activeCounter.innerText = data.job_descriptions.length;
                    }
                    if (data.job_descriptions.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center py-4">No active job descriptions posted yet.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Job Title</th>
                                        <th>Department</th>
                                        <th>Description</th>
                                        <th style="width: 250px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.job_descriptions.forEach(jd => {
                        html += `
                            <tr id="jd-row-${jd.id}">
                                <td class="fw-bold text-info">${jd.title}</td>
                                <td class="fw-bold text-light">${jd.department}</td>
                                <td style="white-space: pre-wrap; font-size: 13.5px; color: var(--text-secondary);">${jd.description}</td>
                                <td>
                                    <div class="d-flex gap-2">
                                        <button class="btn btn-sm btn-success" onclick="matchJobDescription('${jd.id}', '${jd.title.replace(/'/g, "\\'")}')"><i class="bi bi-bullseye"></i> Matches</button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteJobDescription('${jd.id}')"><i class="bi bi-trash"></i> Delete</button>
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
                    listDiv.innerHTML = `<p class="text-danger text-center">Failed to fetch JDs.</p>`;
                }
            } catch (err) {
                console.error("Failed to load JDs", err);
                listDiv.innerHTML = '<p class="text-danger text-center">Failed to connect to JD database.</p>';
            }
        }

        async function deleteJobDescription(id) {
            if (!confirm("Are you sure you want to delete this job description?")) return;
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/job_descriptions/${id}`, {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (data.success) {
                    showNotification("Job description deleted successfully.", "success");
                    
                    const row = document.getElementById(`jd-row-${id}`);
                    if (row) {
                        row.style.transition = "all 0.3s ease";
                        row.style.opacity = "0";
                        row.style.transform = "translateX(20px)";
                        setTimeout(() => row.remove(), 300);
                    }
                    loadJobDescriptions();
                    closeJDMatches();
                } else {
                    showNotification(data.message || "Failed to remove JD.", "error");
                }
            } catch (err) {
                console.error("Delete JD failed", err);
                showNotification("Network crash requesting JD deletion.", "error");
            }
        }

        async function matchJobDescription(id, title) {
            const panel = document.getElementById('jdMatchPanel');
            const resultsDiv = document.getElementById('jdMatchResults');
            const titleElem = document.getElementById('jdMatchTitle');

            currentJDTitle = title;
            titleElem.innerHTML = `<i class="bi bi-bullseye text-success me-2"></i>Candidate Matches for: ${title}`;
            panel.style.display = 'block';
            resultsDiv.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-success" role="status"></div><p class="mt-2 text-muted">Calculating semantic similarity scores from Qdrant vector database...</p></div>';
            
            panel.scrollIntoView({ behavior: 'smooth' });

            try {
                const response = await fetch(`http://127.0.0.1:8000/api/job_descriptions/${id}/match`, {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (data.success) {
                    currentJDMatches = data.results;
                    if (data.results.length === 0) {
                        resultsDiv.innerHTML = '<p class="text-muted text-center py-4">No matching candidates detected above threshold similarity.</p>';
                        return;
                    }

                    let html = `
                        <div class="table-responsive table-container mt-3">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Candidate Profile</th>
                                        <th>Skills Detected</th>
                                        <th>Semantic Match</th>
                                        <th>Document Link</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    data.results.forEach(candidate => {
                        let linkHtml = '';
                        if (candidate.resume_url) {
                            let linkUrl = candidate.resume_url;
                            if (!linkUrl.startsWith('http://') && !linkUrl.startsWith('https://')) {
                                linkUrl = `http://127.0.0.1:8000/uploads/${linkUrl}`;
                            }
                            linkHtml = `<a href="${encodeURI(linkUrl)}" target="_blank" class="btn btn-sm btn-primary px-3"><i class="bi bi-file-pdf"></i> View PDF</a>`;
                        } else {
                            linkHtml = `<span class="text-muted">No attachment</span>`;
                        }

                        // Determine score color
                        let percent = parseFloat(candidate.match_percentage);
                        let scoreColor = 'text-success';
                        if (percent < 65) scoreColor = 'text-warning';
                        if (percent < 50) scoreColor = 'text-danger';

                        html += `
                            <tr>
                                <td class="fw-bold text-light">${candidate.name}</td>
                                <td><span style="font-size: 13.5px; color: var(--text-secondary);">${candidate.skills || 'None'}</span></td>
                                <td class="fw-bold ${scoreColor}">${candidate.match_percentage}</td>
                                <td>${linkHtml}</td>
                            </tr>
                        `;
                    });

                    html += `
                                </tbody>
                            </table>
                        </div>
                    `;
                    resultsDiv.innerHTML = html;
                    showNotification(`Identified ${data.results.length} semantic candidate matches!`, 'success');
                } else {
                    resultsDiv.innerHTML = `<p class="text-danger">Error matching: ${data.error}</p>`;
                }
            } catch (err) {
                console.error("Match failed", err);
                resultsDiv.innerHTML = '<p class="text-danger">Qdrant vector query failed. Check backend console.</p>';
            }
        }

        function closeJDMatches() {
            document.getElementById('jdMatchPanel').style.display = 'none';
            currentJDMatches = [];
            currentJDTitle = "";
        }

        function exportJDMatches() {
            if (!currentJDMatches || currentJDMatches.length === 0) {
                showNotification("No match data available to export.", "error");
                return;
            }
            let csv = "Candidate Name,Skills,Match Percentage,Resume URL\n";
            currentJDMatches.forEach(item => {
                let name = `"${(item.name || '').replace(/"/g, '""')}"`;
                let skills = `"${(item.skills || '').replace(/"/g, '""')}"`;
                let pct = `"${item.match_percentage || ''}"`;
                let url = `"${(item.resume_url || '').replace(/"/g, '""')}"`;
                csv += `${name},${skills},${pct},${url}\n`;
            });
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.setAttribute("href", url);
            link.setAttribute("download", `candidate_matches_${currentJDTitle.toLowerCase().replace(/[^a-z0-9]/g, '_')}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
