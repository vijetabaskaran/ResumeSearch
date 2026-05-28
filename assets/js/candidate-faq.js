/* ============================================================
   CANDIDATE FAQ — Load & render public FAQ entries
   Calls GET /api/faq  (public endpoint, no auth required)
   ============================================================ */

let _faqCache = [];  // Module-level cache for client-side search

/**
 * Load all public FAQ entries from the server and render them
 * as collapsible accordion cards inside #faqEntriesList.
 */
async function loadFaqEntries() {
    const listDiv = document.getElementById('faqEntriesList');
    const countBadge = document.getElementById('faqCount');
    if (!listDiv) return;

    listDiv.innerHTML = `
        <div class="d-flex align-items-center justify-content-center py-5 gap-3 text-secondary">
            <div class="spinner-border spinner-border-sm text-info" role="status"></div>
            Loading FAQ entries...
        </div>`;

    try {
        const response = await fetch("http://127.0.0.1:8000/api/faq");
        const data = await response.json();

        if (data.success) {
            _faqCache = data.faqs || [];
            renderFaqCards(_faqCache, listDiv, countBadge);
        } else {
            listDiv.innerHTML = `<p class="text-danger text-center py-4">Failed to load FAQ entries. Please try again later.</p>`;
        }
    } catch (err) {
        console.error("Failed to load FAQ entries", err);
        listDiv.innerHTML = `<p class="text-danger text-center py-4">Could not connect to the server. Please check your connection.</p>`;
    }
}

/**
 * Render an array of FAQ entries as accordion cards.
 * @param {Array}  entries   - Array of FAQ objects from the API
 * @param {Element} container - DOM element to inject HTML into
 * @param {Element} badge     - Count badge element
 */
function renderFaqCards(entries, container, badge) {
    if (badge) badge.textContent = entries.length;

    if (!entries || entries.length === 0) {
        container.innerHTML = `
            <div class="glass-card text-center py-5">
                <i class="bi bi-patch-question" style="font-size: 48px; color: rgba(255,255,255,0.15);"></i>
                <p class="text-secondary mt-3 mb-0" style="font-size: 15px;">No FAQ entries have been published yet.</p>
                <p class="text-muted mt-1" style="font-size: 13px;">Check back later — the recruitment team will post answers here.</p>
            </div>`;
        return;
    }

    let html = `<div class="faq-accordion" id="faqAccordion">`;

    entries.forEach((faq, index) => {
        const collapseId = `faqCollapse${index}`;
        const headerId   = `faqHeader${index}`;
        const dateStr    = faq.created_at ? faq.created_at.split(' ')[0] : '';
        const by         = faq.sender_username || 'Recruitment Team';

        // Truncate long question previews for the card header
        const questionPreview = (faq.original_subject || 'Untitled Question').substring(0, 90);
        const questionFull    = escapeHtml(faq.original_message || '');
        const answerFull      = escapeHtml(faq.reply_text || '');

        html += `
            <div class="faq-card mb-3" id="faq-item-${index}">
                <!-- Question Header (always visible) -->
                <button
                    class="faq-card-header w-100 text-start"
                    type="button"
                    onclick="toggleFaq('${collapseId}', this)"
                    aria-expanded="false"
                    aria-controls="${collapseId}"
                    id="${headerId}"
                >
                    <div class="d-flex align-items-start gap-3">
                        <div class="faq-q-icon flex-shrink-0">
                            <i class="bi bi-question-lg"></i>
                        </div>
                        <div class="flex-grow-1 min-w-0">
                            <div class="faq-question-text">${escapeHtml(questionPreview)}</div>
                            <div class="faq-meta mt-1">
                                <span><i class="bi bi-calendar3 me-1"></i>${dateStr}</span>
                                <span class="ms-3"><i class="bi bi-person-badge me-1"></i>${escapeHtml(by)}</span>
                            </div>
                        </div>
                        <div class="faq-chevron flex-shrink-0">
                            <i class="bi bi-chevron-down"></i>
                        </div>
                    </div>
                </button>

                <!-- Expanded Answer Body -->
                <div class="faq-card-body" id="${collapseId}" style="display: none;">
                    <div class="faq-full-question mb-3">
                        <div class="faq-section-label"><i class="bi bi-chat-left-quote-fill me-2"></i>Candidate Question</div>
                        <div class="faq-question-body">${questionFull}</div>
                    </div>
                    <div class="faq-answer-block">
                        <div class="faq-section-label answer-label"><i class="bi bi-patch-check-fill me-2"></i>Official Answer</div>
                        <div class="faq-answer-body">${answerFull}</div>
                    </div>
                </div>
            </div>`;
    });

    html += `</div>`;
    container.innerHTML = html;
}

/**
 * Toggle a single FAQ accordion panel open/closed.
 * @param {string}  collapseId - ID of the collapsible body element
 * @param {Element} btn        - The header button element that was clicked
 */
function toggleFaq(collapseId, btn) {
    const body = document.getElementById(collapseId);
    if (!body) return;

    const isOpen = body.style.display === 'block';
    const chevron = btn.querySelector('.faq-chevron i');

    if (isOpen) {
        // Collapse with slide-up animation
        body.style.maxHeight = body.scrollHeight + 'px';
        body.style.overflow = 'hidden';
        requestAnimationFrame(() => {
            body.style.transition = 'max-height 0.3s ease, opacity 0.25s ease';
            body.style.maxHeight = '0px';
            body.style.opacity = '0';
        });
        setTimeout(() => {
            body.style.display = 'none';
            body.style.maxHeight = '';
            body.style.overflow = '';
            body.style.opacity = '';
        }, 320);
        btn.setAttribute('aria-expanded', 'false');
        btn.classList.remove('faq-card-header--open');
        if (chevron) chevron.style.transform = 'rotate(0deg)';
    } else {
        // Expand with slide-down animation
        body.style.display = 'block';
        body.style.maxHeight = '0px';
        body.style.overflow = 'hidden';
        body.style.opacity = '0';
        requestAnimationFrame(() => {
            body.style.transition = 'max-height 0.35s ease, opacity 0.3s ease';
            body.style.maxHeight = body.scrollHeight + 500 + 'px';
            body.style.opacity = '1';
        });
        setTimeout(() => {
            body.style.overflow = '';
        }, 360);
        btn.setAttribute('aria-expanded', 'true');
        btn.classList.add('faq-card-header--open');
        if (chevron) chevron.style.transform = 'rotate(180deg)';
    }
}

/**
 * Client-side search/filter across FAQ entries (searches subject + message + reply_text).
 * @param {string} query - User-typed search string
 */
function filterFaq(query) {
    const listDiv = document.getElementById('faqEntriesList');
    const countBadge = document.getElementById('faqCount');
    const q = query.trim().toLowerCase();

    if (!q) {
        renderFaqCards(_faqCache, listDiv, countBadge);
        return;
    }

    const filtered = _faqCache.filter(faq => {
        const subject = (faq.original_subject || '').toLowerCase();
        const message = (faq.original_message || '').toLowerCase();
        const reply   = (faq.reply_text || '').toLowerCase();
        return subject.includes(q) || message.includes(q) || reply.includes(q);
    });

    renderFaqCards(filtered, listDiv, countBadge);
}

/**
 * Safely escape HTML to prevent XSS when injecting user-generated content.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
