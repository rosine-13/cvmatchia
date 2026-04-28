<?php
require_once 'includes/config.php';
requireAuth('candidate');

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['cv_file'])) {
    $manager = new CVManager($pdo);
    $result = $manager->addCV($_SESSION['user_id'], $_FILES['cv_file']['tmp_name'], $_FILES['cv_file']['name']);
    if ($result) {
        $_SESSION['flash_message'] = "✅ CV envoyé avec succès. L'analyse par l'IA va commencer dans quelques instants.";
        $_SESSION['flash_type'] = 'success';
    } else {
        $_SESSION['flash_message'] = "❌ Erreur lors de l'upload. Veuillez réessayer.";
        $_SESSION['flash_type'] = 'danger';
    }
}
header('Location: dashboard_candidate.php');
exit;