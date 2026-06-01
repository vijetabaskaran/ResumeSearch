/* SEARCH SKILL (SEMANTIC SEARCH) */
        let lastSearchResults = [];

        async function searchSkill() {
            let skill = document.getElementById("skillSearch").value.trim();
            if (!skill) {
                showNotification("Please specify a skill keyword.", "error");
                return;
            }

            try {
                let response = await fetch(`http://127.0.0.1:8000/search_resume?skill=${skill}`);
                let data = await response.json();
                let resultsDiv = document.getElementById("searchResults");
                resultsDiv.innerHTML = "";

                if (!data.results || data.results.length === 0) {
                    resultsDiv.innerHTML = `<div class="p-3 text-center text-muted">No matching candidate profiles index for skill "${skill}".</div>`;
                    return;
                }

                lastSearchResults = data.results;

                let html = `
                    <div class="mt-4 p-3 rounded" style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="fw-bold m-0"><i class="bi bi-cpu-fill text-info me-2"></i>Semantic Search Results</h5>
                            <button class="btn btn-sm btn-success" onclick="exportSearchResults()"><i class="bi bi-download me-1"></i> Export CSV</button>
                        </div>
                        <div class="table-responsive table-container">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Candidate Name</th>
                                        <th>Skills Detected</th>
                                        <th>Semantic Match</th>
                                        <th>Resume Document</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;

                data.results.forEach(function (item) {
                    let resumeDisplay = "";
                    if (item.resume_url) {
                        let linkUrl = item.resume_url;
                        if (!linkUrl.startsWith("http://") && !linkUrl.startsWith("https://")) {
                            linkUrl = `http://127.0.0.1:8000/uploads/${linkUrl}`;
                        }
                        resumeDisplay = `<a href="${encodeURI(linkUrl)}" target="_blank" class="btn btn-sm btn-primary py-1.5 px-3"><i class="bi bi-file-earmark-pdf me-1"></i> View PDF</a>`;
                    } else {
                        resumeDisplay = `<span class="text-muted">No attachment</span>`;
                    }

                    html += `
                        <tr>
                            <td class="fw-bold text-light">${item.name}</td>
                            <td>${formatSkillsCell(item.skills, item.name)}</td>
                            <td class="fw-bold text-success">${item.match_percentage}</td>
                            <td>${resumeDisplay}</td>
                        </tr>
                    `;
                });

                html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;

                resultsDiv.innerHTML = html;
                showNotification(`Found ${data.results.length} semantic matches!`, "success");
            } catch (error) {
                console.error(error);
                showNotification("Search execution failed.", "error");
            }
        }

        function exportSearchResults() {
            if (!lastSearchResults || lastSearchResults.length === 0) {
                showNotification("No results to export.", "error");
                return;
            }
            let csv = "Name,Skills,Match Percentage,Resume URL\n";
            lastSearchResults.forEach(item => {
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
            link.setAttribute("download", "resume_search_results.csv");
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
