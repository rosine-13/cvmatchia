<?php require_once 'includes/config.php'; ?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Inscription Candidat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-light">
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-6">
                <div class="card shadow border-0">
                    <div class="card-header bg-primary text-white text-center">
                        <h4><i class="fas fa-user-plus"></i> Créer mon espace candidat</h4>
                    </div>
                    <div class="card-body">
                        <?php if ($_SERVER['REQUEST_METHOD'] === 'POST'): 
                            // Traitement de l'inscription
                            $email = $_POST['email'];
                            $password = password_hash($_POST['password'], PASSWORD_DEFAULT);
                            $full_name = $_POST['full_name'];
                            $phone = $_POST['phone'];
                            $city = $_POST['city'];
                            $birth_date = $_POST['birth_date'];
                            $gender = $_POST['gender'];
                            $skills = $_POST['skills'];
                            $experience_years = !empty($_POST['experience_years']) ? floatval($_POST['experience_years']) : 0;


                            try {
                                $pdo->beginTransaction();
                                $stmt = $pdo->prepare("INSERT INTO users (email, password) VALUES (?, ?)");
                                $stmt->execute([$email, $password]);
                                $userId = $pdo->lastInsertId();

                                $stmt2 = $pdo->prepare("INSERT INTO candidates (user_id, full_name, phone, city, birth_date, gender, skills_manual, experience_years) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
                                $stmt2->execute([$userId, $full_name, $phone, $city, $birth_date, $gender, $skills, $experience_years]);
                                $pdo->commit();

                                $_SESSION['user_id'] = $userId;
                                $_SESSION['role'] = 'candidate';
                                $_SESSION['full_name'] = $full_name;
                                header('Location: dashboard_candidate.php');
                                exit;
                            } catch(Exception $e) {
                                $pdo->rollBack();
                                $error = "Erreur : " . $e->getMessage();
                            }
                        endif; ?>

                        <?php if (isset($error)): ?>
                            <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
                        <?php endif; ?>

                        <form method="post">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label>Nom complet</label>
                                    <input type="text" name="full_name" class="form-control" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Email</label>
                                    <input type="email" name="email" class="form-control" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Mot de passe</label>
                                    <input type="password" name="password" class="form-control" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Téléphone</label>
                                    <input type="text" name="phone" class="form-control">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Ville</label>
                                    <input type="text" name="city" class="form-control">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Date de naissance</label>
                                    <input type="date" name="birth_date" class="form-control">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Genre</label>
                                    <select name="gender" class="form-select">
                                        <option value="M">Homme</option>
                                        <option value="F">Femme</option>
                                        <option value="other">Autre</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label>Années d'expérience</label>
                                    <input type="number" step="0.5" name="experience_years" class="form-control">
                                </div>
                                <div class="col-12 mb-3">
                                    <label>Compétences (séparées par des virgules)</label>
                                    <textarea name="skills" rows="2" class="form-control" placeholder="PHP, MySQL, JavaScript..."></textarea>
                                </div>
                                <div class="col-12">
                                    <button type="submit" class="btn btn-primary w-100"><i class="fas fa-check-circle"></i> S'inscrire</button>
                                </div>
                            </div>
                        </form>
                        <p class="mt-3 text-center">Déjà un compte ? <a href="candidate_login.php">Connectez-vous</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>