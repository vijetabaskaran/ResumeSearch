/* DYNAMIC SIDEBAR HIGHLIGHTING PAGE NAVIGATOR */
        function showPage(pageId) {
            // Hide all pages
            const pages = document.querySelectorAll('.page');
            pages.forEach(p => p.classList.remove('active-page'));
            
            // Show targeted page
            const targetPage = document.getElementById(pageId);
            if (targetPage) {
                targetPage.classList.add('active-page');
            } else {
                console.warn(`Page container ID [${pageId}] not found.`);
            }

            // Remove highlighted state from all sidebar buttons
            const sidebarButtons = document.querySelectorAll('#sidebarLinks button');
            sidebarButtons.forEach(btn => btn.classList.remove('active'));

            // Set active state on button corresponding to target page
            const activeBtn = document.getElementById(`btn-${pageId}`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }
        }

        function navigateToDashboard() {
            const savedUser = localStorage.getItem('resumeUser');
            if (savedUser) {
                const userObj = JSON.parse(savedUser);
                if (userObj.role === 'official') {
                    showPage('official-dashboard-page');
                } else {
                    showPage('candidate-dashboard-page');
                }
            } else {
                showPage('home-page');
            }
        }
