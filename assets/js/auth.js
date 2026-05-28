/* ROLE MANAGEMENT & LOGIN SYSTEM */
        let selectedRole = 'candidate';

        function setLoginRole(role) {
            selectedRole = role;
            const tabCand = document.getElementById('tab-candidate');
            const tabOfficial = document.getElementById('tab-official');
            const demoCreds = document.getElementById('demo-credentials');
            const loginUser = document.getElementById('loginUsername');
            const openingsPreview = document.getElementById('loginOpeningsPreview');

            if (role === 'candidate') {
                tabCand.style.background = '#0072ff';
                tabCand.style.color = 'white';
                tabOfficial.style.background = 'transparent';
                tabOfficial.style.color = '#bfc7d9';
                demoCreds.innerHTML = 'Candidates must register before logging in.';
                loginUser.value = '';
                openingsPreview.style.display = 'block';
                loadLoginOpenings(); // fetch roles dynamically on login page
            } else {
                tabOfficial.style.background = '#0072ff';
                tabOfficial.style.color = 'white';
                tabCand.style.background = 'transparent';
                tabCand.style.color = '#bfc7d9';
                demoCreds.innerHTML = 'Official Login: <b>official</b> / <b>Admin@123</b>';
                loginUser.value = 'official';
                openingsPreview.style.display = 'none';
            }
        }

        async function handleLogin(event) {
            event.preventDefault();
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            const errorDiv = document.getElementById('loginError');
            errorDiv.style.display = 'none';

            try {
                const response = await fetch("http://127.0.0.1:8000/api/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ username: username, password: password, role: selectedRole })
                });
                const data = await response.json();

                if (data.success) {
                    localStorage.setItem('resumeUser', JSON.stringify({
                        role: data.role,
                        name: data.name,
                        username: data.username,
                        email: data.email || ''
                    }));
                    applyUserRole(data.role, data.name);
                    showNotification(`Welcome back, ${data.name}!`, 'success');
                } else {
                    errorDiv.innerText = data.message;
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                console.error("Login failed", error);
                errorDiv.innerText = "Connection to login server failed. Make sure the backend is active.";
                errorDiv.style.display = 'block';
            }
        }

        function handleLogout() {
            localStorage.removeItem('resumeUser');
            document.body.classList.remove('user-candidate', 'user-official');
            document.body.classList.add('logged-out');

            // Reset input values
            document.getElementById('loginPassword').value = '';
            // setLoginRole('candidate');

            // Clear search history
            const skillSearch = document.getElementById('skillSearch');
            if (skillSearch) skillSearch.value = '';
            const searchResults = document.getElementById('searchResults');
            if (searchResults) searchResults.innerHTML = '';

            // Reset forms toggles
            toggleAuthForm('login');

            // Close chatbot if open
            const chatWindow = document.getElementById('chatbotWindow');
            if (chatWindow) chatWindow.style.display = 'none';
            const toggleBtn = document.getElementById('chatbotToggleBtn');
            if (toggleBtn) toggleBtn.style.transform = 'scale(1) rotate(0deg)';

            showPage('home-page');
            showNotification("Successfully logged out.", "success");
        }

        function applyUserRole(role, name) {
            document.body.classList.remove('logged-out');
            document.body.classList.remove('user-candidate', 'user-official');
            document.body.classList.add('user-' + role);

            // Show Profile Widget
            document.getElementById('userProfile').style.display = 'block';
            document.getElementById('userRoleBadge').innerText = role;
            document.getElementById('userProfileName').innerText = name;

            // Generate Sidebar Navigation buttons dynamically based on user role
            const sidebarLinksDiv = document.getElementById('sidebarLinks');
            
            if (role === 'official') {
                sidebarLinksDiv.innerHTML = `
                    <button id="btn-official-dashboard-page" onclick="showPage('official-dashboard-page')">
                        <i class="bi bi-speedometer2"></i> Dashboard
                    </button>
                    <button id="btn-resumes-page" onclick="showPage('resumes-page')">
                        <i class="bi bi-file-earmark-person"></i> Resumes Management
                    </button>
                    <button id="btn-messages-page" onclick="showPage('messages-page')">
                        <i class="bi bi-envelope-paper"></i> Candidate Messages
                    </button>
                    <button id="btn-job-descriptions-page" onclick="showPage('job-descriptions-page')">
                        <i class="bi bi-briefcase"></i> Job Descriptions
                    </button>
                    <button id="btn-settings" onclick="showPage('settings')">
                        <i class="bi bi-gear"></i> Portal Settings
                    </button>
                `;
                
                // Fetch dynamic backend numbers for officials dashboard metrics
                getResumeCount();
                loadOfficialResumes();
                loadOfficialEmails();
                loadJobDescriptions();
                
                // Route directly to dashboard
                showPage('official-dashboard-page');
            } else {
                sidebarLinksDiv.innerHTML = `
                    <button id="btn-candidate-dashboard-page" onclick="showPage('candidate-dashboard-page')">
                        <i class="bi bi-speedometer2"></i> My Dashboard
                    </button>
                    <button id="btn-candidate-upload-page" onclick="showPage('candidate-upload-page')">
                        <i class="bi bi-cloud-arrow-up"></i> Upload My Resume
                    </button>
                    <button id="btn-candidate-support-page" onclick="showPage('candidate-support-page')">
                        <i class="bi bi-envelope"></i> Contact Recruiter
                    </button>
                    <button id="btn-settings" onclick="showPage('settings')">
                        <i class="bi bi-gear"></i> Portal Settings
                    </button>
                `;
                
                // Load candidate dynamic openings & statistics
                loadCandidateJobDescriptions();
                
                // Route directly to candidate dashboard
                showPage('candidate-dashboard-page');
            }
        }
