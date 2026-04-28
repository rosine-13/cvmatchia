<?php
require_once 'includes/config.php';
requireAuth('admin');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $userId = $input['user_id'] ?? 0;
    $subject = $input['subject'] ?? 'Offre d\'emploi';
    $message = $input['message'] ?? '';

    // Récupérer l'email du candidat
    $stmt = $pdo->prepare("SELECT u.email, c.full_name FROM users u JOIN candidates c ON u.id = c.user_id WHERE u.id = ?");
    $stmt->execute([$userId]);
    $candidate = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$candidate) {
        echo json_encode(['success' => false, 'error' => 'Candidat introuvable']);
        exit;
    }

    $to = $candidate['email'];
    $fullName = $candidate['full_name'];
    $headers = "From: recruteur@example.com\r\n";
    $headers .= "Reply-To: recruteur@example.com\r\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
    $body = "Bonjour $fullName,\n\n$message\n\nCordialement,\nL'équipe recrutement";

    // Envoi (sous XAMPP, mail() peut nécessiter une configuration)
    $sent = mail($to, $subject, $body, $headers);
    
    if ($sent) {
        echo json_encode(['success' => true, 'message' => 'Email envoyé à ' . $to]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Erreur serveur mail. Configurez sendmail ou utilisez PHPMailer.']);
    }
    exit;
}
?>