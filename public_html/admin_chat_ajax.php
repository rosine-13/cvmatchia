<?php
require_once 'includes/config.php';
requireAuth('admin');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $originalQuery = $input['original_query'] ?? '';
    $userMessage = $input['user_message'] ?? '';
    $currentIds = $input['current_ids'] ?? [];
    $result = callPythonAPI('/chat', [
        'original_query' => $originalQuery,
        'user_message' => $userMessage,
        'current_results_ids' => $currentIds
    ]);
    echo json_encode($result);
}
?>