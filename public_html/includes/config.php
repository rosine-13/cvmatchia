<?php
session_start();

// Paramètres base de données
define('DB_HOST', 'localhost');
define('DB_NAME', 'cvmatch_db');
define('DB_USER', 'root');
define('DB_PASS', '');

// URL de base du site (sans slash final)
define('BASE_URL', 'http://localhost/CVMatchIA/public_html');

// URL du microservice Python (par défaut sur le port 8000)
define('PYTHON_API_URL', 'http://localhost:8000');

// Connexion PDO
try {
    $pdo = new PDO("mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8", DB_USER, DB_PASS);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Erreur de connexion à la base de données : " . $e->getMessage());
}

// Inclure les fonctions et classes
require_once __DIR__ . '/functions.php';
require_once __DIR__ . '/classes/CVManager.php';
?>