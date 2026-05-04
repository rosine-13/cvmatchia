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

    // Appel direct à l'API Python (FastAPI)
    $ch = curl_init(PYTHON_API_URL . '/search');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['query' => $query]));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) {
        echo json_encode(['error' => "Erreur API Python (HTTP $httpCode)", 'details' => $response]);
        exit;
    }

    $result = json_decode($response, true);
    if (!is_array($result)) {
        echo json_encode(['error' => 'Réponse JSON invalide', 'raw' => $response]);
        exit;
    }

    // Si l'API a retourné une clé "results", on la garde ; sinon on encapsule
    if (!isset($result['results'])) {
        // Si c'est déjà un tableau, on le retourne tel quel (certaines versions retournent directement le tableau)
        $result = ['results' => $result];
    }

    // Ajout du chemin du CV (optionnel)
    if (!empty($result['results'])) {
        $userIds = array_column($result['results'], 'user_id');
        if (!empty($userIds)) {
            $placeholders = implode(',', array_fill(0, count($userIds), '?'));
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
            }
        }
    }

    echo json_encode($result);
}
?>