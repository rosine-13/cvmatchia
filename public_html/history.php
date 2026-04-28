<?php
require_once 'includes/config.php';
requireAuth('candidate');
$manager = new CVManager($pdo);
$cvs = $manager->getHistory($_SESSION['user_id']);

// Récupérer l'expérience depuis candidates (si besoin)
$stmt = $pdo->prepare("SELECT experience_years FROM candidates WHERE user_id = ?");
$stmt->execute([$_SESSION['user_id']]);
$userExp = $stmt->fetchColumn();
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Mon historique</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body class="bg-light">
    <div class="container mt-4">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">
                <i class="fas fa-history"></i> Historique des CV déposés
            </div>
            <div class="card-body">
                <p><strong>Mon expérience actuelle :</strong> <?= formatExperience($userExp) ?> ans</p>
                <?php if (count($cvs) === 0): ?>
                    <p>Aucun CV déposé pour le moment.</p>
                <?php else: ?>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr><th>Fichier</th><th>Date d'envoi</th><th>Statut extraction</th><th>Compétences extraites</th><th>Expérience extraite</th></tr>
                            </thead>
                            <tbody>
                                <?php foreach($cvs as $cv): ?>
                                <tr>
                                    <td><?= htmlspecialchars($cv['file_name']) ?></td>
                                    <td><?= date('d/m/Y H:i', strtotime($cv['upload_date'])) ?></td>
                                    <td>
                                        <?php if($cv['extraction_status'] === 'done'): ?>
                                            <span class="badge bg-success">Terminé</span>
                                        <?php elseif($cv['extraction_status'] === 'pending'): ?>
                                            <span class="badge bg-warning">En attente</span>
                                        <?php else: ?>
                                            <span class="badge bg-danger">Échec</span>
                                        <?php endif; ?>
                                    </td>
                                    <td><?= htmlspecialchars(substr($cv['extracted_skills'], 0, 100)) ?></td>
                                    <td>
                                        <?php 
                                        $exp = $cv['extracted_experience'] ?? '0';
                                        echo formatExperience($exp) . ' ans';
                                        ?>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                <?php endif; ?>
                <a href="dashboard_candidate.php" class="btn btn-secondary"><i class="fas fa-arrow-left"></i> Retour</a>
            </div>
        </div>
    </div>
</body>
</html>