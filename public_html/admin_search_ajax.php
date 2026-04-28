<?php
require_once 'includes/config.php';
requireAuth('admin');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $query = $input['query'] ?? '';
    if (empty($query)) {
        echo json_encode(['error' => 'Requête vide']);
        exit;
    }
    $result = callPythonAPI('/search', ['query' => $query]);
    
    if (isset($result['results']) && is_array($result['results']) && !empty($result['results'])) {
        // Récupérer les IDs des candidats
        $userIds = array_column($result['results'], 'user_id');
        $placeholders = implode(',', array_fill(0, count($userIds), '?'));
        // Chercher le chemin du CV le plus récent pour chaque candidat
        $stmt = $pdo->prepare("SELECT user_id, file_path FROM cvs WHERE user_id IN ($placeholders) ORDER BY upload_date DESC");
        $stmt->execute($userIds);
        $paths = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            if (!isset($paths[$row['user_id']])) {
                $paths[$row['user_id']] = $row['file_path'];
            }
        }
        foreach ($result['results'] as &$candidate) {
            $uid = $candidate['user_id'];
            $candidate['file_path'] = $paths[$uid] ?? null;
            // Formatage de l'expérience (supprimer .0)
            $candidate['experience_years_display'] = formatExperience($candidate['experience_years'] ?? 0);
        }
    }
    
    echo json_encode($result);
}
?>