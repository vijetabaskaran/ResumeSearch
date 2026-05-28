/* SYSTEM THEME CHANGE */
        function changeTheme(mode) {
            if (mode === "light") {
                document.body.classList.add("light-mode");
            } else {
                document.body.classList.remove("light-mode");
            }
            showNotification(`Theme switched to ${mode} mode!`, 'success');
        }
