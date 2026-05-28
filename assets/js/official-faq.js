/* ============================================================
   OFFICIAL DASHBOARD — Published FAQ Management Panel
   Calls GET /api/faq  (public) and DELETE /api/faq/{id} (official)
   ============================================================ */

/**
 * Load all published FAQs and render them in #officialFaqList
 * with a Delete button on each entry.
 */
async function loadOfficialFaqs() {
    const listDiv    = document.getElementById("officialFaqList");
    const countBadge = document.getElementById("officialFaqCount");
    if (!listDiv) return;

    listDiv.innerHTML = `
        <div class="d-flex align-items-center gap-2 text-secondary py-2">
            <div class="spinner-border spinner-border-sm text-warning" role="status"></div>
            Loading published FAQs...
        </div>`;

    try {
        const res  = await fetch("http://127.0.0.1:8000/api/faq");
        const data = await res.json();

        if (!data.success) {
            listDiv.innerHTML = `<p class="text-danger text-center py-3" style="font-size:13px;">Failed to load FAQ entries.</p>`;
            return;
        }

        const faqs = data.faqs || [];
        if (countBadge) countBadge.textContent = `${faqs.length} entr${faqs.length === 1 ? "y" : "ies"}`;

        if (faqs.length === 0) {
            listDiv.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-patch-question" style="font-size:36px; color:rgba(255,190,50,0.2);"></i>
                    <p class="text-secondary mt-2 mb-0" style="font-size:13.5px;">No FAQ entries published yet.</p>
                    <p class="text-muted" style="font-size:12px;">When you reply to a candidate with "Allow to Post as FAQ" enabled, it will appear here.</p>
                </div>`;
            return;
        }

        let html = `<div class="faq-manage-list">`;
        faqs.forEach(faq => {
            const date    = faq.created_at ? faq.created_at.split(" ")[0] : "";
            const by      = faq.sender_username || "official";
            const subject = escOfficialHtml(faq.original_subject || "No Subject");
            const question = escOfficialHtml((faq.original_message || "").substring(0, 200));
            const answer   = escOfficialHtml((faq.reply_text || "").substring(0, 300));

            html += `
                <div class="faq-manage-card" id="official-faq-${faq.id}">
                    <div class="faq-manage-header">
                        <div class="faq-manage-meta">
                            <i class="bi bi-question-circle-fill text-warning me-2"></i>
                            <span class="faq-manage-subject">${subject}</span>
                            <span class="faq-manage-date ms-3"><i class="bi bi-calendar3 me-1"></i>${date}</span>
                            <span class="faq-manage-by ms-2"><i class="bi bi-person-badge me-1"></i>${escOfficialHtml(by)}</span>
                        </div>
                        <button
                            class="faq-manage-delete-btn"
                            onclick="deleteFaq('${faq.id}')"
                            title="Unpublish this FAQ entry"
                        >
                            <i class="bi bi-trash-fill me-1"></i>Remove
                        </button>
                    </div>
                    <div class="faq-manage-body">
                        <div class="faq-manage-q">
                            <span class="faq-manage-label faq-label-q">Q</span>
                            <span class="faq-manage-text">${question}${(faq.original_message || "").length > 200 ? "…" : ""}</span>
                        </div>
                        <div class="faq-manage-a mt-2">
                            <span class="faq-manage-label faq-label-a">A</span>
                            <span class="faq-manage-text faq-answer-text">${answer}${(faq.reply_text || "").length > 300 ? "…" : ""}</span>
                        </div>
                    </div>
                </div>`;
        });
        html += `</div>`;
        listDiv.innerHTML = html;

    } catch (err) {
        console.error("Failed to load official FAQs", err);
        listDiv.innerHTML = `<p class="text-danger text-center py-3" style="font-size:13px;">Could not connect to server.</p>`;
    }
}

/**
 * Unpublish a FAQ entry (official-only DELETE).
 * Removes the card from the DOM on success with a fade animation.
 * @param {string} faqId - UUID of the reply row to unpublish
 */
async function deleteFaq(faqId) {
    if (!confirm("Remove this FAQ entry? The reply will remain private to the candidate.")) return;

    try {
        const res  = await fetch(`http://127.0.0.1:8000/api/faq/${faqId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        const data = await res.json();

        if (data.success) {
            showNotification("FAQ entry unpublished successfully.", "success");
            const card = document.getElementById(`official-faq-${faqId}`);
            if (card) {
                card.style.transition = "all 0.3s ease";
                card.style.opacity    = "0";
                card.style.transform  = "translateX(20px)";
                setTimeout(() => {
                    card.remove();
                    // Refresh count badge
                    loadOfficialFaqs();
                }, 320);
            }
        } else {
            showNotification(data.message || "Failed to remove FAQ entry.", "error");
        }
    } catch (err) {
        console.error("FAQ delete failed", err);
        showNotification("Network error while removing FAQ.", "error");
    }
}

function escOfficialHtml(str) {
    if (!str) return "";
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
