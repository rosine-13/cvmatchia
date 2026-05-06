<?php
require_once 'includes/config.php';
requireAuth('admin');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $originalQuery = $input['original_query'] ?? '';
    $userMessage = $input['user_message'] ?? '';
    $currentIds = $input['current_results_ids'] ?? [];

    // Appel direct à l'API Python /chat
    $ch = curl_init(PYTHON_API_URL . '/chat');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'original_query' => $originalQuery,
        'user_message' => $userMessage,
        'current_results_ids' => $currentIds
    ]));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    curl_close($ch);
    echo $response;
}
?>