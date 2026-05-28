/* APP ONLOAD SYSTEM ENTRYPOINT */
async function initializeApplication() {
    try {
        await loadApplicationPartials();
    } catch (error) {
        console.error('Failed to load frontend partials', error);
        document.body.innerHTML = `
            <main style="min-height: 100vh; display: grid; place-items: center; padding: 24px; background: #070913; color: #f8fafc; font-family: Arial, sans-serif;">
                <section style="max-width: 560px; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 28px; background: rgba(15,23,42,0.72);">
                    <h1 style="font-size: 24px; margin: 0 0 12px;">ResumeX could not load its UI files</h1>
                    <p style="color: #94a3b8; line-height: 1.6; margin: 0;">Run this project through a local web server so the HTML partials can be fetched. For example: <code>python -m http.server 5500</code>.</p>
                </section>
            </main>
        `;
        return;
    }

    // Load landing page job openings preview by default
    loadLoginOpenings();

    const savedUser = localStorage.getItem('resumeUser');
    if (savedUser) {
        const userObj = JSON.parse(savedUser);
        applyUserRole(userObj.role, userObj.name);
    } else {
        document.body.classList.add('logged-out');
        setLoginRole('candidate');
    }
}

document.addEventListener('DOMContentLoaded', initializeApplication);
