<?php
require_once 'includes/config.php';
requireAuth('candidate');
$user = getUserById($pdo, $_SESSION['user_id']);
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Mon espace candidat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary shadow">
        <div class="container">
            <span class="navbar-brand"><i class="fas fa-user-circle"></i> Bonjour <?= htmlspecialchars($_SESSION['full_name']) ?></span>
            <a href="logout.php" class="btn btn-outline-light"><i class="fas fa-sign-out-alt"></i> Déconnexion</a>
        </div>
    </nav>


    <?php if (isset($_SESSION['flash_message'])): ?>
    <div class="container mt-3">
        <div class="alert alert-<?= $_SESSION['flash_type'] ?> alert-dismissible fade show" role="alert">
            <?= htmlspecialchars($_SESSION['flash_message']) ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    </div>
    <?php unset($_SESSION['flash_message'], $_SESSION['flash_type']); ?>
<?php endif; ?>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-6 mb-4">
                <div class="card shadow h-100">
                    <div class="card-header bg-white fw-bold"><i class="fas fa-upload"></i> Déposer un nouveau CV</div>
                    <div class="card-body">
                        <form action="candidate_upload_cv.php" method="post" enctype="multipart/form-data">
                            <div class="mb-3">
                                <input type="file" name="cv_file" class="form-control" accept=".pdf,.docx,.jpg,.png" required>
                            </div>
                            <button type="submit" class="btn btn-success"><i class="fas fa-cloud-upload-alt"></i> Analyser et enregistrer</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-4">
                <div class="card shadow h-100">
                    <div class="card-header bg-white fw-bold"><i class="fas fa-history"></i> Historique des candidatures</div>
                    <div class="card-body">
                        <p>Consultez la liste de vos CV déposés et les analyses effectuées.</p>
                        <a href="history.php" class="btn btn-info text-white"><i class="fas fa-eye"></i> Voir mon historique</a>
                    </div>
                </div>
            </div>
        </div>
        <div class="card shadow mt-2">
            <div class="card-header bg-white">Mes informations</div>
            <div class="card-body">
                <p><strong>Email :</strong> <?= htmlspecialchars($user['email']) ?></p>
                <p><strong>Téléphone :</strong> <?= htmlspecialchars($user['phone']) ?></p>
                <p><strong>Ville :</strong> <?= htmlspecialchars($user['city']) ?></p>
                <p><strong>Expérience :</strong> <?= formatExperience($user['experience_years']) ?> ans</p>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>