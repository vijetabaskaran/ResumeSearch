/* DYNAMIC OPENINGS PREVIEW LOAD ON LANDING PAGE */
        async function loadLoginOpenings() {
            const listDiv = document.getElementById('loginJdList');
            if (!listDiv) return;
            try {
                const response = await fetch("http://127.0.0.1:8000/api/job_descriptions");
                const data = await response.json();
                if (data.success) {
                    if (data.job_descriptions.length === 0) {
                        listDiv.innerHTML = '<p class="text-muted text-center m-0" style="font-size: 12px; padding: 10px;">No open roles currently posted.</p>';
                        return;
                    }

                    let html = '';
                    data.job_descriptions.forEach(jd => {
                        html += `
                            <div class="p-2 mb-2 rounded" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.03); transition: 0.2s;">
                                <div style="font-size: 13px; font-weight: 600; color: #00c6ff;">${jd.title}</div>
                                <div class="d-flex justify-content-between align-items-center mt-1">
                                    <span style="font-size: 11px; color: #a0aec0;"><i class="bi bi-building me-1"></i>${jd.department}</span>
                                    <span class="badge bg-success-subtle text-success border border-success-subtle" style="font-size: 9px; padding: 3px 6px;">Active</span>
                                </div>
                            </div>
                        `;
                    });
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<p class="text-danger text-center m-0" style="font-size: 12px; padding: 10px;">Error loading open positions.</p>`;
                }
            } catch (err) {
                console.error("Failed to load login openings", err);
                listDiv.innerHTML = '<p class="text-danger text-center m-0" style="font-size: 12px; padding: 10px;">Failed to fetch active roles.</p>';
            }
        }
