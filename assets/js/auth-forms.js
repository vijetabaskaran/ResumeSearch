/* CANDIDATE REGISTRATION FORM HANDLER */

/**
 * Handle candidate registration form submission.
 * Role is NOT sent — the backend always assigns 'candidate'.
 */
async function handleRegister(event) {
    event.preventDefault();
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;

    const errorDiv = document.getElementById('registerError');
    const successDiv = document.getElementById('registerSuccess');
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    try {
        const response = await fetch("http://127.0.0.1:8000/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // NOTE: role is intentionally omitted — backend enforces 'candidate'
            body: JSON.stringify({ name, email, username, password })
        });
        const data = await response.json();

        if (data.success) {
            successDiv.innerText = "Account registered successfully! Redirecting to login...";
            successDiv.style.display = 'block';

            // Clear form fields
            document.getElementById('registerName').value = '';
            document.getElementById('registerEmail').value = '';
            document.getElementById('registerUsername').value = '';
            document.getElementById('registerPassword').value = '';

            setTimeout(() => {
                toggleAuthView('login');
                const loginUsernameInput = document.getElementById('loginUsername');
                if (loginUsernameInput) loginUsernameInput.value = username;
                const loginPasswordInput = document.getElementById('loginPassword');
                if (loginPasswordInput) loginPasswordInput.value = '';
            }, 1500);
        } else {
            errorDiv.innerText = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error("Registration failed", error);
        errorDiv.innerText = "Connection to register server failed.";
        errorDiv.style.display = 'block';
    }
}
