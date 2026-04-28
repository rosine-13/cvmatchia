document.getElementById('btnSearch')?.addEventListener('click', async () => {
    const query = document.getElementById('searchQuery').value;
    if (!query) return;
    const loading = document.getElementById('loading');
    loading.style.display = 'block';
    const response = await fetch('admin_search_ajax.php', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: query})
    });
    const data = await response.json();
    loading.style.display = 'none';
    displayResults(data.results || []);
    // Stocker la dernière recherche et les IDs pour le chat
    window.lastQuery = query;
    window.lastResults = data.results || [];
});

function displayResults(results) {
    const container = document.getElementById('results');
    if (!results.length) {
        container.innerHTML = '<div class="alert alert-warning">Aucun candidat trouvé.</div>';
        return;
    }
    let html = '';
    results.forEach(r => {
        // Utiliser le champ formaté envoyé par PHP, ou formater à la volée
        let expDisplay = r.experience_years_display;
        if (!expDisplay && r.experience_years !== undefined) {
            let exp = parseFloat(r.experience_years);
            expDisplay = (exp === Math.floor(exp)) ? exp.toString() : exp.toFixed(1);
        }
        html += `
            <div class="col-md-6 col-lg-4">
                <div class="card result-card shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-user-circle text-primary"></i> ${escapeHtml(r.full_name)}</h5>
                        <p class="card-text">
                            <strong>Score :</strong> <span class="badge bg-success">${r.score}%</span><br>
                            <strong>Ville :</strong> ${escapeHtml(r.city)}<br>
                            <strong>Expérience :</strong> ${escapeHtml(expDisplay || '0')} ans<br>
                            <strong>Compétences :</strong> ${escapeHtml(r.skills)}<br>
                            <strong>Explication :</strong> ${escapeHtml(r.explanation)}
                        </p>
                        <button class="btn btn-sm btn-info text-white" onclick="openChat(${r.user_id})"><i class="fas fa-comment-dots"></i> Contacter (simulé)</button>
                    </div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

function openChat(userId) {
    const modal = new bootstrap.Modal(document.getElementById('chatModal'));
    modal.show();
    // Stocker les IDs actuels pour l'agent conversationnel
    window.currentIds = window.lastResults.map(r => r.user_id);
    window.currentQuery = window.lastQuery;
}

document.getElementById('btnChatSend')?.addEventListener('click', async () => {
    const userMsg = document.getElementById('chatInput').value;
    if (!userMsg) return;
    const response = await fetch('admin_chat_ajax.php', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            original_query: window.currentQuery,
            user_message: userMsg,
            current_ids: window.currentIds
        })
    });
    const data = await response.json();
    document.getElementById('chatResponse').innerHTML = `<i class="fas fa-robot"></i> ${data.message}`;
    if (data.filtered_ids) {
        // Mettre à jour l'affichage avec les IDs filtrés
        const filteredResults = window.lastResults.filter(r => data.filtered_ids.includes(r.user_id));
        displayResults(filteredResults);
        window.lastResults = filteredResults;
        window.currentIds = data.filtered_ids;
    }
});

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}