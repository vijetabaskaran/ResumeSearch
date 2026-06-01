/* ============================================================
   SKILLS DISPLAY HELPER & MODAL CONTROLLERS
   Truncates long skill lists and provides a glassmorphic details modal
   ============================================================ */

/**
 * Formats the skill string for display in results tables.
 * If too long, wraps in container with a "View Skills" button/link.
 */
function formatSkillsCell(skills, candidateName) {
    if (!skills || skills.trim() === '' || skills.toLowerCase() === 'none') {
        return '<span class="text-muted">None</span>';
    }

    const safeName = candidateName.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const safeSkills = skills.replace(/'/g, "\\'").replace(/"/g, '&quot;');

    // Characters threshold (about 3 lines on standard resolution)
    const threshold = 120;
    if (skills.length <= threshold) {
        return `<span style="font-size: 13.5px; color: var(--text-secondary);">${skills}</span>`;
    }

    const truncated = skills.substring(0, threshold).trim() + '...';
    return `
        <div class="skills-cell-container">
            <span style="font-size: 13.5px; color: var(--text-secondary);">${truncated}</span>
            <div class="mt-1">
                <button class="btn btn-link btn-sm p-0 text-info fw-semibold text-decoration-none" 
                        style="font-size: 12.5px; transition: color 0.2s;" 
                        onclick="showSkillsModal('${safeName}', '${safeSkills}')">
                    <i class="bi bi-eye me-1"></i>View Skills
                </button>
            </div>
        </div>
    `;
}

/**
 * Dynamically constructs and opens the custom details modal.
 */
function showSkillsModal(candidateName, skillsText) {
    let modal = document.getElementById('skillsDetailsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'skillsDetailsModal';
        modal.className = 'custom-modal-overlay';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(7, 9, 19, 0.85);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            z-index: 10600;
            display: none;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.25s ease;
        `;
        document.body.appendChild(modal);
    }

    // Parse and split the skills
    const skillsList = skillsText.split(',')
        .map(s => s.trim())
        .filter(Boolean);

    const badgesHtml = skillsList.map(skill => {
        return `<span class="skill-badge-pill">${skill}</span>`;
    }).join('');

    modal.innerHTML = `
        <div class="glass-card custom-modal-content" 
             style="max-width: 480px; width: 90%; transform: scale(0.9); transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); border: 1px solid rgba(0, 198, 255, 0.2); background: rgba(15, 23, 42, 0.95);">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h5 class="fw-bold text-light m-0"><i class="bi bi-cpu text-info me-2"></i>Skills Profile</h5>
                <button onclick="closeSkillsModal()" class="btn-close-custom"><i class="bi bi-x-lg"></i></button>
            </div>
            <div class="mb-3">
                <span class="text-secondary" style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.5px;">Candidate Name</span>
                <h5 class="fw-bold text-white mt-1 mb-0">${candidateName}</h5>
            </div>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 16px 0;">
            <div class="mb-4">
                <span class="text-secondary" style="font-size: 11.5px; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Extracted Skills (${skillsList.length})</span>
                <div class="d-flex flex-wrap gap-2" style="max-height: 200px; overflow-y: auto; padding-right: 6px;" id="modalSkillsList">
                    ${badgesHtml}
                </div>
            </div>
            <div class="text-end">
                <button onclick="closeSkillsModal()" class="btn btn-sm btn-outline-info px-4 py-2" style="border-radius: 10px; font-weight: 600;">Close</button>
            </div>
        </div>
    `;

    // Ensure we handle light-mode correctly if active
    if (document.body.classList.contains('light-mode')) {
        const modalContent = modal.querySelector('.custom-modal-content');
        if (modalContent) {
            modalContent.style.background = '#ffffff';
            modalContent.style.borderColor = 'rgba(0, 114, 255, 0.15)';
        }
    }

    modal.style.display = 'flex';
    // Trigger reflow for transition
    modal.offsetHeight;
    modal.style.opacity = '1';
    modal.querySelector('.custom-modal-content').style.transform = 'scale(1)';

    // Style the scrollbar inside the modal skills list
    const skillsListDiv = document.getElementById('modalSkillsList');
    if (skillsListDiv) {
        skillsListDiv.style.scrollbarWidth = 'thin';
    }
}

/**
 * Closes the modal with smooth transition.
 */
function closeSkillsModal() {
    const modal = document.getElementById('skillsDetailsModal');
    if (modal) {
        modal.style.opacity = '0';
        const content = modal.querySelector('.custom-modal-content');
        if (content) {
            content.style.transform = 'scale(0.9)';
        }
        setTimeout(() => {
            modal.style.display = 'none';
        }, 250);
    }
}

// Global modal dismiss on clicking background overlay
window.addEventListener('click', function(e) {
    const modal = document.getElementById('skillsDetailsModal');
    if (e.target === modal) {
        closeSkillsModal();
    }
});
