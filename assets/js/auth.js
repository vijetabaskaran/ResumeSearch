/* ROLE MANAGEMENT & LOGIN SYSTEM */

// ================================================
// AUTH VIEW TOGGLER (replaces setLoginRole tabs)
// ================================================

/**
 * Switch between the three auth views:
 *   'login'        → Candidate login (default)
 *   'register'     → Candidate registration
 *   'admin-login'  → Official/Admin login
 */
function toggleAuthView(view) {
    const views = ['candidate-login', 'candidate-register', 'admin-login'];
    views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) el.style.display = 'none';
    });

    const openingsPreview = document.getElementById('loginOpeningsPreview');

    // Clear error/success messages on switch
    ['loginError', 'registerError', 'registerSuccess', 'adminLoginError'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    if (view === 'login') {
        const el = document.getElementById('view-candidate-login');
        if (el) el.style.display = 'block';
        if (openingsPreview) {
            openingsPreview.style.display = 'block';
            loadLoginOpenings();
        }
    } else if (view === 'register') {
        const el = document.getElementById('view-candidate-register');
        if (el) el.style.display = 'block';
        if (openingsPreview) openingsPreview.style.display = 'none';
    } else if (view === 'admin-login') {
        const el = document.getElementById('view-admin-login');
        if (el) el.style.display = 'block';
        if (openingsPreview) openingsPreview.style.display = 'none';
    }
}

// Keep backward compat alias used by some partials (openings.js etc.)
function toggleAuthForm(mode) {
    if (mode === 'register') toggleAuthView('register');
    else toggleAuthView('login');
}

// ================================================
// AUTH HEADERS HELPER
// ================================================

/**
 * Returns the Authorization headers that must be sent with every
 * official-only API request. The backend reads X-User-Role to enforce
 * role-based access control.
 *
 * NOTE: For production, replace with JWT Bearer token headers.
 */
function getAuthHeaders() {
    const savedUser = localStorage.getItem('resumeUser');
    if (!savedUser) return { 'Content-Type': 'application/json' };
    try {
        const user = JSON.parse(savedUser);
        return {
            'Content-Type': 'application/json',
            'X-User-Role': user.role || ''
        };
    } catch {
        return { 'Content-Type': 'application/json' };
    }
}

// ================================================
// CANDIDATE LOGIN
// ================================================

async function handleCandidateLogin(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    errorDiv.style.display = 'none';

    try {
        const response = await fetch("http://127.0.0.1:8000/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
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
        console.error("Candidate login failed", error);
        errorDiv.innerText = "Connection to login server failed. Make sure the backend is active.";
        errorDiv.style.display = 'block';
    }
}

// ================================================
// OFFICIAL / ADMIN LOGIN
// ================================================

async function handleOfficialLogin(event) {
    event.preventDefault();
    const username = document.getElementById('adminUsername').value.trim();
    const password = document.getElementById('adminPassword').value;
    const errorDiv = document.getElementById('adminLoginError');
    errorDiv.style.display = 'none';

    try {
        const response = await fetch("http://127.0.0.1:8000/api/admin-login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
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
            showNotification(`Welcome, ${data.name}!`, 'success');
        } else {
            errorDiv.innerText = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error("Official login failed", error);
        errorDiv.innerText = "Connection to server failed. Make sure the backend is active.";
        errorDiv.style.display = 'block';
    }
}

// ================================================
// LOGOUT
// ================================================

function handleLogout() {
    localStorage.removeItem('resumeUser');
    document.body.classList.remove('user-candidate', 'user-official');
    document.body.classList.add('logged-out');

    // Reset input values
    const loginPassword = document.getElementById('loginPassword');
    if (loginPassword) loginPassword.value = '';
    const adminPassword = document.getElementById('adminPassword');
    if (adminPassword) adminPassword.value = '';

    // Clear search history
    const skillSearch = document.getElementById('skillSearch');
    if (skillSearch) skillSearch.value = '';
    const searchResults = document.getElementById('searchResults');
    if (searchResults) searchResults.innerHTML = '';

    // Reset to candidate login view
    toggleAuthView('login');

    // Close chatbot if open
    const chatWindow = document.getElementById('chatbotWindow');
    if (chatWindow) chatWindow.style.display = 'none';
    const toggleBtn = document.getElementById('chatbotToggleBtn');
    if (toggleBtn) toggleBtn.style.transform = 'scale(1) rotate(0deg)';

    showPage('home-page');
    showNotification("Successfully logged out.", "success");
}

// ================================================
// APPLY ROLE — POST-LOGIN ROUTING
// ================================================

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
