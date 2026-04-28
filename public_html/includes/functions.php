<?php
/**
 * Vérifie si l'utilisateur est connecté et a le bon rôle
 */
function requireAuth($role = null) {
    if (!isset($_SESSION['user_id'])) {
        header('Location: ' . BASE_URL . '/login.php');
        exit;
    }
    if ($role && $_SESSION['role'] !== $role) {
        die("Accès non autorisé.");
    }
}

/**
 * Récupère les informations d'un utilisateur (candidat)
 */
function getUserById($pdo, $userId) {
    $stmt = $pdo->prepare("SELECT u.*, c.* FROM users u LEFT JOIN candidates c ON u.id = c.user_id WHERE u.id = ?");
    $stmt->execute([$userId]);
    return $stmt->fetch(PDO::FETCH_ASSOC);
}

/**
 * Envoie une requête POST au microservice Python
 */
function callPythonAPI($endpoint, $data) {
    $url = PYTHON_API_URL . $endpoint;
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($httpCode != 200) {
        return ['error' => "Erreur API ($httpCode)"];
    }
    return json_decode($response, true);
}
/**
 * Formate l'expérience : supprime ".0" si la valeur est entière
 * @param float|int|string $years
 * @return string
 */
function formatExperience($years) {
    $years = floatval($years);
    if ($years == (int)$years) {
        return (string)(int)$years;
    }
    return number_format($years, 1, '.', '');
}


?>