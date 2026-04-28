<?php
require_once 'includes/config.php';

// Récupérer tous les CV en attente
$stmt = $pdo->query("SELECT id, file_path FROM cvs WHERE extraction_status = 'pending'");
$cvs = $stmt->fetchAll(PDO::FETCH_ASSOC);

$manager = new CVManager($pdo);
foreach ($cvs as $cv) {
    $fullPath = __DIR__ . '/' . $cv['file_path'];
    if (file_exists($fullPath)) {
        // Appel direct au microservice (identique à celui de CVManager)
        $data = ['file_path' => realpath($fullPath), 'cv_id' => $cv['id']];
        $ch = curl_init(PYTHON_API_URL . '/parse_cv');
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        echo "CV ID {$cv['id']} : HTTP $httpCode - " . ($response ?: 'ok') . "<br>";
    } else {
        echo "Fichier introuvable pour CV ID {$cv['id']} : {$cv['file_path']}<br>";
    }
}
echo "Terminé.";