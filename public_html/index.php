<?php require_once 'includes/config.php'; ?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CVMatch IA - Recrutement intelligent</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow">
        <div class="container">
            <a class="navbar-brand fw-bold" href="index.php"><i class="fas fa-brain me-2"></i>CVMatch IA</a>
            <div class="ms-auto">
                <a href="candidate_login.php" class="btn btn-outline-light me-2"><i class="fas fa-sign-in-alt"></i> Candidat</a>
                <a href="admin_login.php" class="btn btn-light"><i class="fas fa-user-tie"></i> Recruteur</a>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row align-items-center">
            <div class="col-md-6">
                <h1 class="display-4 fw-bold">La bonne rencontre <br> entre <span class="text-primary">talents</span> et <span class="text-primary">entreprises</span></h1>
                <p class="lead mt-3">Déposez votre CV, notre IA analyse vos compétences et vous met en relation avec les recruteurs.</p>
                <a href="candidate_login.php" class="btn btn-primary btn-lg mt-2"><i class="fas fa-upload"></i> Déposer mon CV</a>
            </div>
            <div class="col-md-6 text-center">
                <img src="https://images.unsplash.com/photo-1581091226033-d5c48150dbaa?w=600&h=400&fit=crop" class="img-fluid rounded shadow" alt="IA">
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>