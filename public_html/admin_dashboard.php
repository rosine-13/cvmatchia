<?php
require_once 'includes/config.php';
requireAuth('admin');

// Statistiques
$stmt = $pdo->query("SELECT COUNT(*) FROM users WHERE role = 'candidate'");
$totalCandidates = $stmt->fetchColumn();
$stmt = $pdo->query("SELECT COUNT(*) FROM cvs");
$totalCVs = $stmt->fetchColumn();
$stmt = $pdo->query("SELECT COUNT(*) FROM cvs WHERE extraction_status = 'done'");
$analyzedCVs = $stmt->fetchColumn();
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Dashboard Recruteur - CVMatch IA</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        .result-card { border-left: 5px solid #0d6efd; margin-bottom: 20px; transition: transform 0.2s; }
        .result-card:hover { transform: translateY(-5px); }
        .stat-card { border-radius: 15px; }
        /* Le style du bouton flottant n'est plus utilisé, mais on le garde pour ne pas casser */
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark shadow">
        <div class="container">
            <span class="navbar-brand"><i class="fas fa-chart-line"></i> CVMatch IA - Recruteur</span>
            <a href="logout.php" class="btn btn-outline-light"><i class="fas fa-sign-out-alt"></i> Déconnexion</a>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Cartes statistiques -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card text-white bg-primary stat-card shadow">
                    <div class="card-body">
                        <h5><i class="fas fa-users"></i> Candidats inscrits</h5>
                        <h2 class="display-6"><?= $totalCandidates ?></h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-success stat-card shadow">
                    <div class="card-body">
                        <h5><i class="fas fa-file-upload"></i> CV uploadés</h5>
                        <h2 class="display-6"><?= $totalCVs ?></h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-info stat-card shadow">
                    <div class="card-body">
                        <h5><i class="fas fa-brain"></i> CV analysés (IA)</h5>
                        <h2 class="display-6"><?= $analyzedCVs ?></h2>
                        <small><?= round(($analyzedCVs / max($totalCVs,1))*100) ?>% du total</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recherche -->
        <div class="card shadow mb-4">
            <div class="card-header bg-white fw-bold"><i class="fas fa-search"></i> Recherche intelligente</div>
            <div class="card-body">
                <textarea id="searchQuery" class="form-control mb-2" rows="3" placeholder="Exemple : Développeur web PHP avec 2 ans d'expérience, PowerBI, Abidjan"></textarea>
                <button id="btnSearch" class="btn btn-primary"><i class="fas fa-microchip"></i> Analyser avec l'IA</button>
                <div id="loading" class="mt-2 text-muted" style="display:none;"><i class="fas fa-spinner fa-spin"></i> Recherche en cours...</div>
            </div>
        </div>

        <!-- Résultats -->
        <div id="results" class="row"></div>
    </div>

    <!-- Bouton flottant pour l'agent conversationnel (désactivé) -->
    <!-- <button class="chat-floating-btn" id="openChatBtn" title="Agent IA conversationnel">
        <i class="fas fa-comment-dots"></i>
    </button> -->

    <!-- Modal Agent conversationnel (désactivé) -->
    <!-- <div class="modal fade" id="chatModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title"><i class="fas fa-robot"></i> Agent IA conversationnel</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Affinez les résultats actuels :</p>
                    <input type="text" id="chatInput" class="form-control" placeholder="Ex: Montre-moi seulement les femmes de moins de 30 ans">
                    <div id="chatResponse" class="mt-2 text-muted"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                    <button type="button" id="btnChatSend" class="btn btn-primary">Interroger</button>
                </div>
            </div>
        </div>
    </div> -->

    <!-- Modal Envoyer un email -->
    <div class="modal fade" id="emailModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title"><i class="fas fa-envelope"></i> Contacter le candidat</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="hidden" id="emailUserId">
                    <div class="mb-2">
                        <label>Sujet</label>
                        <input type="text" id="emailSubject" class="form-control" value="Opportunité professionnelle">
                    </div>
                    <div class="mb-2">
                        <label>Message</label>
                        <textarea id="emailBody" rows="5" class="form-control" placeholder="Votre message..."></textarea>
                    </div>
                    <div id="emailResult"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                    <button type="button" id="btnSendEmail" class="btn btn-primary">Envoyer</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let lastQuery = '', lastResults = [];

        document.getElementById('btnSearch')?.addEventListener('click', async () => {
            const query = document.getElementById('searchQuery').value;
            if (!query) return;
            document.getElementById('loading').style.display = 'block';
            const response = await fetch('admin_search_ajax.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            });
            const data = await response.json();
            document.getElementById('loading').style.display = 'none';
            displayResults(data.results || []);
            lastQuery = query;
            lastResults = data.results || [];
        });

        function displayResults(results) {
            const container = document.getElementById('results');
            if (!results.length) {
                container.innerHTML = '<div class="alert alert-warning">Aucun candidat trouvé.</div>';
                return;
            }
            let html = '';
            results.forEach(r => {
                let expDisplay = r.experience_years_display;
                if (!expDisplay && r.experience_years !== undefined) {
                    let exp = parseFloat(r.experience_years);
                    expDisplay = (exp === Math.floor(exp)) ? exp.toString() : exp.toFixed(1);
                }
                const fullName = r.full_name || 'Candidat';
                const city = r.city || 'Non renseignée';
                const skills = r.skills || '';
                // Données DeepSeek
                const certifications = r.certifications && Array.isArray(r.certifications) ? r.certifications : [];
                const resume = r.resume || '';
                const langueMaternelle = r.langue_maternelle || '';
                const centresInteret = r.centres_interet && Array.isArray(r.centres_interet) ? r.centres_interet : [];
                const projets = r.projets_phares && Array.isArray(r.projets_phares) ? r.projets_phares : [];
                const situation = r.situation_matrimoniale || '';

                html += `
                    <div class="col-md-6 col-lg-4">
                        <div class="card result-card shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-user-circle text-primary"></i> ${escapeHtml(fullName)}</h5>
                                <p class="card-text">
                                    <strong>Score :</strong> <span class="badge bg-success">${r.score}%</span><br>
                                    <strong>Ville :</strong> ${escapeHtml(city)}<br>
                                    <strong>Expérience :</strong> ${escapeHtml(expDisplay || '0')} ans<br>
                                    <strong>Compétences :</strong> ${escapeHtml(skills)}<br>
                                    ${certifications.length ? `<strong>Certifications :</strong> ${escapeHtml(certifications.join(', '))}<br>` : ''}
                                    ${langueMaternelle ? `<strong>Langue maternelle :</strong> ${escapeHtml(langueMaternelle)}<br>` : ''}
                                    ${centresInteret.length ? `<strong>Centres d'intérêt :</strong> ${escapeHtml(centresInteret.join(', '))}<br>` : ''}
                                    ${projets.length ? `<strong>Projets phares :</strong> ${escapeHtml(projets.join(', '))}<br>` : ''}
                                    ${situation ? `<strong>Situation matrimoniale :</strong> ${escapeHtml(situation)}<br>` : ''}
                                    ${resume ? `<em class="text-muted small">${escapeHtml(resume)}</em><br>` : ''}
                                </p>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-sm btn-info text-white" onclick="openEmailModal(${r.user_id}, '${escapeHtml(fullName)}')">
                                        <i class="fas fa-envelope"></i> Contacter
                                    </button>
                                    ${r.file_path ? `<a href="${r.file_path}" target="_blank" class="btn btn-sm btn-secondary"><i class="fas fa-file-pdf"></i> Voir CV</a>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // Fonctions liées à l'agent conversationnel (désactivées)
        /*
        function openChatModal() {
            const modal = new bootstrap.Modal(document.getElementById('chatModal'));
            modal.show();
            window.currentIds = lastResults.map(r => r.user_id);
            window.currentQuery = lastQuery;
        }

        document.getElementById('openChatBtn')?.addEventListener('click', openChatModal);

        document.getElementById('btnChatSend')?.addEventListener('click', async () => {
            const userMsg = document.getElementById('chatInput').value;
            if (!userMsg) return;
            ...
        });
        */

        function openEmailModal(userId, fullName) {
            document.getElementById('emailUserId').value = userId;
            document.getElementById('emailBody').value = `Bonjour ${fullName},\n\nJe suis intéressé par votre profil...\n\nCordialement.`;
            document.getElementById('emailResult').innerHTML = '';
            const modal = new bootstrap.Modal(document.getElementById('emailModal'));
            modal.show();
        }

        document.getElementById('btnSendEmail')?.addEventListener('click', async () => {
            const userId = document.getElementById('emailUserId').value;
            const subject = document.getElementById('emailSubject').value;
            const message = document.getElementById('emailBody').value;
            const resultDiv = document.getElementById('emailResult');
            resultDiv.innerHTML = '<div class="spinner-border spinner-border-sm"></div> Envoi...';
            const response = await fetch('send_email.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, subject: subject, message: message})
            });
            const data = await response.json();
            if (data.success) {
                resultDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                setTimeout(() => bootstrap.Modal.getInstance(document.getElementById('emailModal')).hide(), 2000);
            } else {
                resultDiv.innerHTML = `<div class="alert alert-danger">${data.error || 'Erreur d\'envoi'}</div>`;
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
    </script>
</body>
</html>