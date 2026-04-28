<?php
class CVManager {
    private $pdo;

    public function __construct($pdo) {
        $this->pdo = $pdo;
    }

    /**
     * Ajoute un CV uploadé et déclenche le parsing Python
     */
    public function addCV($userId, $tmpPath, $originalName) {
        $uploadDir = __DIR__ . '/../../assets/uploads/';
        if (!is_dir($uploadDir)) mkdir($uploadDir, 0777, true);
        $safeName = uniqid() . '_' . basename($originalName);
        $targetPath = $uploadDir . $safeName;

        if (move_uploaded_file($tmpPath, $targetPath)) {
            // Enregistrement en base
            $stmt = $this->pdo->prepare("INSERT INTO cvs (user_id, file_name, file_path, extraction_status) VALUES (?, ?, ?, 'pending')");
            $stmt->execute([$userId, $originalName, 'assets/uploads/' . $safeName]);
            $cvId = $this->pdo->lastInsertId();

            // Appel asynchrone au microservice (pas d'attente)
            $this->callPythonParser($targetPath, $cvId);
            return true;
        }
        return false;
    }

    private function callPythonParser($filePath, $cvId) {
    // Convertir les backslashes en slashes pour Windows
    $filePath = str_replace('\\', '/', realpath($filePath));
    $data = [
        'file_path' => $filePath,
        'cv_id' => $cvId
    ];
    $ch = curl_init(PYTHON_API_URL . '/parse_cv');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 1); // ne pas attendre la réponse
    curl_exec($ch);
    curl_close($ch);
  }

    /**
     * Récupère l'historique des CV d'un candidat
     */
    public function getHistory($userId) {
        $stmt = $this->pdo->prepare("SELECT * FROM cvs WHERE user_id = ? ORDER BY upload_date DESC");
        $stmt->execute([$userId]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}
?>