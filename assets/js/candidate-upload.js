/* TOGGLE SYSTEM METHODS */
function toggleUploadMethod(method) {
    const fileGroup = document.getElementById('fileInputGroup');
    const urlGroup = document.getElementById('urlInputGroup');
    if (method === 'file') {
        fileGroup.style.display = 'block';
        urlGroup.style.display = 'none';
    } else {
        fileGroup.style.display = 'none';
        urlGroup.style.display = 'block';
    }
}

/* UPLOAD RESUME */
async function uploadResume() {
    console.log("uploadResume() started execution");
    let name = document.getElementById("candidateName").value.trim();
    if (!name) {
        console.warn("Name is empty, triggering showNotification warning");
        showNotification("Please enter candidate name.", "error");
        return;
    }

    const method = document.querySelector('input[name="uploadMethod"]:checked').value;
    let formData = new FormData();
    formData.append("name", name);

    if (method === 'file') {
        let resumeFile = document.getElementById("resumeFile").files[0];
        if (!resumeFile) {
            showNotification("Please select a PDF file.", "error");
            return;
        }
        formData.append("file", resumeFile);
    } else {
        let resumeUrl = document.getElementById("resumeUrl").value.trim();
        if (!resumeUrl) {
            showNotification("Please enter resume URL.", "error");
            return;
        }
        if (!resumeUrl.startsWith("http://") && !resumeUrl.startsWith("https://")) {
            showNotification("Must start with http:// or https://", "error");
            return;
        }
        formData.append("resume_url", resumeUrl);
    }

    // Hide old result, show loader
    const uploadLoader = document.getElementById("uploadLoader");
    const uploadResult = document.getElementById("uploadResult");
    if (uploadResult) {
        uploadResult.style.display = "none";
        uploadResult.innerHTML = "";
    }
    if (uploadLoader) uploadLoader.style.display = "block";

    // Disable the button to prevent double-clicks
    const uploadBtn = document.querySelector('#resumeForm button[type="button"]');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div> Processing...';
    }

    try {
        console.log("Sending resume upload request...");
        let response = await fetch("http://127.0.0.1:8000/insert_resume", {
            method: "POST",
            body: formData
        }).then((res)=>{
            console.log("Raw response received:", res)
            console.log(res)
            return res;
        });

        // Guard: check HTTP status before parsing JSON
        if (!response.ok) {
            let errorMsg = "Server returned an error.";
            try {
                const errData = await response.json();
                errorMsg = errData.error || errData.detail || errorMsg;
            } catch (_) { /* non-JSON error body, keep default message */ }
            if (uploadLoader) uploadLoader.style.display = "none";
            showNotification(errorMsg, "error");
            return;
        }

        let data = await response.json();
        console.log("Parsed response data:", data);
        if (uploadLoader) uploadLoader.style.display = "none";

        if (data.message) {
            // === SUCCESS PATH ===
            console.log("Success path triggered, calling showNotification with success toast");
            showNotification("Resume processed and uploaded successfully!", "success");

            // Show inline skills result panel
            const skillsRaw = (data.skills || "").trim();
            let skillPillsHtml = '<span style="color: #94a3b8; font-size: 13px;">No skills detected</span>';
            console.log('skillsRaw', skillsRaw)
            if (skillsRaw && skillsRaw.toLowerCase() !== "none") {
                const pills = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);
                skillPillsHtml = pills.map(s =>
                    `<span style="
                        display: inline-block;
                        padding: 5px 14px;
                        border-radius: 20px;
                        font-size: 12.5px;
                        font-weight: 600;
                        background: rgba(56, 189, 248, 0.1);
                        border: 1px solid rgba(56, 189, 248, 0.25);
                        color: #38bdf8;
                    ">${s}</span>`
                ).join('');
            }

            if (uploadResult) {
                uploadResult.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                        <i class="bi bi-check-circle-fill" style="font-size: 24px; color: #00b09b;"></i>
                        <div>
                            <div style="font-weight: 700; font-size: 15px; color: #00b09b;">Resume uploaded successfully!</div>
                            <div style="font-size: 12.5px; color: #94a3b8;">AI extracted the following skills from your resume:</div>
                        </div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">${skillPillsHtml}</div>
                `;
                uploadResult.style.display = "block";
            }

            // Clear form inputs
            document.getElementById("candidateName").value = "";
            const resumeFileInput = document.getElementById("resumeFile");
            if (resumeFileInput) resumeFileInput.value = "";
            const resumeUrlInput = document.getElementById("resumeUrl");
            if (resumeUrlInput) resumeUrlInput.value = "";

        } else if (data.error) {
            showNotification(data.error, "error");
        } else {
            showNotification("Unexpected response from server.", "error");
        }

    } catch (error) {
        if (uploadLoader) uploadLoader.style.display = "none";
        console.error("Resume upload error stack trace:", error.stack || error);
        showNotification(`Error: ${error.message || error}`, "error");
    } finally {
        // Always re-enable the button
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="bi bi-cloud-arrow-up-fill me-2"></i> Upload & Process Resume';
        }
    }
}

window.uploadResume = uploadResume;
console.log("candidate-upload.js initialized globally as window.uploadResume");
