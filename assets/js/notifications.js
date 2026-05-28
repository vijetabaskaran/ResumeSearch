/* FLOATING TOAST SYSTEM NOTIFICATION */
        function showNotification(message, type = 'success') {
            const container = document.getElementById('toastContainer') || createToastContainer();
            
            const toast = document.createElement('div');
            toast.className = `custom-toast animate-slide-in ${type}`;
            toast.style.cssText = `
                background: ${type === 'success' ? 'rgba(0, 176, 155, 0.95)' : 'rgba(220, 53, 69, 0.95)'};
                color: white;
                backdrop-filter: blur(12px);
                border: 1px solid ${type === 'success' ? 'rgba(0, 176, 155, 0.3)' : 'rgba(220, 53, 69, 0.3)'};
                border-radius: 12px;
                padding: 16px 24px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 12px;
                font-weight: 600;
                font-size: 14.5px;
                pointer-events: auto;
                transition: all 0.3s ease;
                min-width: 250px;
                margin-top: 10px;
            `;
            
            const icon = document.createElement('i');
            icon.className = type === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill';
            icon.style.fontSize = '18px';
            
            const text = document.createElement('span');
            text.innerText = message;
            
            toast.appendChild(icon);
            toast.appendChild(text);
            container.appendChild(toast);
            
            // Auto fade out and remove
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(15px)';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function createToastContainer() {
            let container = document.getElementById('toastContainer');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toastContainer';
                container.style.cssText = `
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    z-index: 99999;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    pointer-events: none;
                `;
                document.body.appendChild(container);
            }
            return container;
        }
