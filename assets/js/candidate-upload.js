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

        /* UPLOAD RESUME (RESOLVING MISSING successMessage BUG!) */
        async function uploadResume() {
            let name = document.getElementById("candidateName").value.trim();
            if (!name) {
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

            // Show processing status UI
            const uploadLoader = document.getElementById("uploadLoader");
            uploadLoader.style.display = "block";

            try {
                let response = await fetch("http://127.0.0.1:8000/insert_resume", {
                    method: "POST",
                    body: formData
                });

                let data = await response.json();
                uploadLoader.style.display = "none";

                if (data.message) {
                    showNotification("Resume processed and uploaded successfully!", "success");
                    alert("Resume processed successfully!\n\nAI Extracted Skills:\n" + (data.skills || "None"));
                    
                    // Clear form
                    document.getElementById("candidateName").value = "";
                    document.getElementById("resumeFile").value = "";
                    document.getElementById("resumeUrl").value = "";
                } else {
                    showNotification(data.error || "Failed to process resume.", "error");
                }
            } catch (error) {
                uploadLoader.style.display = "none";
                console.error("Resume upload crash", error);
                showNotification("Backend connection crashed during parsing.", "error");
            }
        }
