/* DYNAMIC AUTH FORM TOGGLERS */
        function toggleAuthForm(mode) {
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const loginToggleArea = document.getElementById('loginToggleArea');
            const registerToggleArea = document.getElementById('registerToggleArea');
            const tabContainer = document.querySelector('.d-flex.mb-4');
            const demoCredentials = document.getElementById('demo-credentials').parentElement;
            const openingsPreview = document.getElementById('loginOpeningsPreview');

            document.getElementById('loginError').style.display = 'none';
            document.getElementById('registerError').style.display = 'none';
            document.getElementById('registerSuccess').style.display = 'none';

            if (mode === 'register') {
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
                loginToggleArea.style.display = 'none';
                registerToggleArea.style.display = 'block';
                tabContainer.style.display = 'none';
                demoCredentials.style.display = 'none';
                openingsPreview.style.display = 'none';
            } else {
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
                loginToggleArea.style.display = 'block';
                registerToggleArea.style.display = 'none';
                tabContainer.style.display = 'flex';
                demoCredentials.style.display = 'block';
                if (selectedRole === 'candidate') {
                    openingsPreview.style.display = 'block';
                    loadLoginOpenings();
                } else {
                    openingsPreview.style.display = 'none';
                }
            }
        }

        async function handleRegister(event) {
            event.preventDefault();
            const name = document.getElementById('registerName').value.trim();
            const email = document.getElementById('registerEmail').value.trim();
            const username = document.getElementById('registerUsername').value.trim();
            const password = document.getElementById('registerPassword').value;
            const role = document.getElementById('registerRole').value;

            const errorDiv = document.getElementById('registerError');
            const successDiv = document.getElementById('registerSuccess');
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            try {
                const response = await fetch("http://127.0.0.1:8000/api/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ name, email, username, password, role })
                });
                const data = await response.json();

                if (data.success) {
                    successDiv.innerText = "Account registered successfully! Redirecting to login...";
                    successDiv.style.display = 'block';

                    document.getElementById('registerName').value = '';
                    document.getElementById('registerEmail').value = '';
                    document.getElementById('registerUsername').value = '';
                    document.getElementById('registerPassword').value = '';

                    setTimeout(() => {
                        toggleAuthForm('login');
                        document.getElementById('loginUsername').value = username;
                        document.getElementById('loginPassword').value = '';
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
