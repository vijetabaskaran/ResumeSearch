/* ============================================================
   OFFICIAL DASHBOARD — Recent Recruitment Activity Feed
   Calls GET /api/activities (official-only)
   ============================================================ */

/**
 * Activity type → { icon, colorClass, label } map.
 * colorClass maps to CSS custom properties defined in main.css.
 */
const ACTIVITY_CONFIG = {
    resume_uploaded:      { icon: "bi-file-earmark-arrow-up",  color: "#00c6ff", label: "Resume Upload"     },
    candidate_registered: { icon: "bi-person-plus-fill",        color: "#4ade80", label: "Registration"      },
    reply_sent:           { icon: "bi-reply-fill",              color: "#60a5fa", label: "Reply Sent"        },
    faq_posted:           { icon: "bi-patch-question-fill",     color: "#ffbe32", label: "FAQ Published"     },
    faq_deleted:          { icon: "bi-patch-exclamation-fill",  color: "#f87171", label: "FAQ Removed"       },
    jd_created:           { icon: "bi-briefcase-fill",          color: "#a78bfa", label: "Job Description"   },
    resume_search:        { icon: "bi-search",                  color: "#818cf8", label: "Resume Search"     },
    resume_deleted:       { icon: "bi-trash-fill",              color: "#f87171", label: "Resume Deleted"    },
    message_sent:         { icon: "bi-envelope-fill",           color: "#2dd4bf", label: "Message Received"  }
};

/**
 * Convert a datetime string to a human-readable relative time.
 * @param {string} dateStr - "YYYY-MM-DD HH:MM:SS" from the API
 * @returns {string} e.g. "2 minutes ago", "1 hour ago", "yesterday"
 */
function timeAgo(dateStr) {
    if (!dateStr) return "";
    const now = new Date();
    // The DB returns local-timezone strings — parse as-is
    const then = new Date(dateStr.replace(" ", "T"));
    const diffMs = now - then;
    if (isNaN(diffMs) || diffMs < 0) return dateStr;

    const secs  = Math.floor(diffMs / 1000);
    const mins  = Math.floor(secs  / 60);
    const hours = Math.floor(mins  / 60);
    const days  = Math.floor(hours / 24);

    if (secs  < 60)  return "just now";
    if (mins  < 60)  return `${mins} minute${mins !== 1 ? "s" : ""} ago`;
    if (hours < 24)  return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
    if (days  === 1) return "yesterday";
    if (days  < 7)   return `${days} days ago`;
    return then.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

/**
 * Fetch and render the latest recruitment activities in #recentActivityFeed.
 */
async function loadRecentActivity() {
    const feed = document.getElementById("recentActivityFeed");
    if (!feed) return;

    feed.innerHTML = `
        <div class="d-flex align-items-center gap-2 text-secondary py-2">
            <div class="spinner-border spinner-border-sm text-info" role="status"></div>
            Loading activity...
        </div>`;

    try {
        const res  = await fetch("http://127.0.0.1:8000/api/activities", { headers: getAuthHeaders() });
        const data = await res.json();

        if (!data.success) {
            feed.innerHTML = `<p class="text-danger text-center py-3" style="font-size:13px;">Failed to load activity feed.</p>`;
            return;
        }

        const activities = data.activities || [];

        if (activities.length === 0) {
            feed.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-hourglass" style="font-size:32px; color:rgba(255,255,255,0.12);"></i>
                    <p class="text-secondary mt-2 mb-0" style="font-size:13.5px;">No activity recorded yet.</p>
                    <p class="text-muted" style="font-size:12px;">Actions like uploads, registrations, and replies will appear here.</p>
                </div>`;
            return;
        }

        let html = `<div class="activity-feed">`;
        activities.forEach((act, idx) => {
            const cfg   = ACTIVITY_CONFIG[act.activity_type] || { icon: "bi-circle-fill", color: "#64748b", label: act.activity_type };
            const time  = timeAgo(act.created_at);
            const isLast = idx === activities.length - 1;

            html += `
                <div class="activity-item${isLast ? " activity-item--last" : ""}">
                    <div class="activity-dot-wrap">
                        <div class="activity-dot" style="background: ${cfg.color}; box-shadow: 0 0 8px ${cfg.color}55;">
                            <i class="bi ${cfg.icon}" style="font-size:11px; color:#0f172a;"></i>
                        </div>
                        ${!isLast ? `<div class="activity-line"></div>` : ""}
                    </div>
                    <div class="activity-body">
                        <div class="activity-label-row">
                            <span class="activity-type-badge" style="background: ${cfg.color}18; border-color: ${cfg.color}44; color: ${cfg.color};">
                                ${cfg.label}
                            </span>
                            <span class="activity-time">${time}</span>
                        </div>
                        <div class="activity-message">${escapeActivityHtml(act.message)}</div>
                        <div class="activity-by">by <strong>${escapeActivityHtml(act.performed_by)}</strong></div>
                    </div>
                </div>`;
        });
        html += `</div>`;
        feed.innerHTML = html;

    } catch (err) {
        console.error("Failed to load activity feed", err);
        feed.innerHTML = `<p class="text-danger text-center py-3" style="font-size:13px;">Could not connect to the server.</p>`;
    }
}

function escapeActivityHtml(str) {
    if (!str) return "";
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
