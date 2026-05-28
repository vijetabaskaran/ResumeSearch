const APP_PARTIALS = {
    auth: 'partials/auth/login.html',
    shell: 'partials/layout/app-shell.html',
    widgets: 'partials/widgets/chatbot.html',
    modal: 'partials/modals/reply-modal.html',
    pages: [
        'partials/pages/home.html',
        'partials/pages/official-dashboard.html',
        'partials/pages/resumes.html',
        'partials/pages/messages.html',
        'partials/pages/job-descriptions.html',
        'partials/pages/candidate-dashboard.html',
        'partials/pages/candidate-upload.html',
        'partials/pages/candidate-support.html',
        'partials/pages/settings.html'
    ]
};

async function fetchPartial(path) {
    const response = await fetch(path, { cache: 'no-cache' });
    if (!response.ok) {
        throw new Error(`Unable to load ${path}: ${response.status}`);
    }
    return response.text();
}

async function loadPartialInto(targetId, path) {
    const target = document.getElementById(targetId);
    if (!target) {
        throw new Error(`Missing partial target #${targetId}`);
    }
    target.innerHTML = await fetchPartial(path);
}

async function loadPartialsInto(targetId, paths) {
    const target = document.getElementById(targetId);
    if (!target) {
        throw new Error(`Missing partial target #${targetId}`);
    }
    const html = await Promise.all(paths.map(fetchPartial));
    target.innerHTML = html.join('\n');
}

async function loadApplicationPartials() {
    await loadPartialInto('auth-root', APP_PARTIALS.auth);
    await loadPartialInto('app-root', APP_PARTIALS.shell);
    await loadPartialsInto('pages-root', APP_PARTIALS.pages);
    await loadPartialInto('widget-root', APP_PARTIALS.widgets);
    await loadPartialInto('modal-root', APP_PARTIALS.modal);
}
