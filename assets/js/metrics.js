/* GET RESUME COUNT & TOTAL METRIC UPDATER FOR OFFICIAL */
        async function getResumeCount() {
            try {
                let response = await fetch("http://127.0.0.1:8000/resume_count");
                let data = await response.json();
                const resumeElem = document.getElementById("resumeCount");
                if (resumeElem) {
                    resumeElem.innerHTML = data.total_resumes !== undefined ? data.total_resumes : 0;
                }
            } catch (error) {
                console.error("Failed to fetch resume counts:", error);
            }
        }
