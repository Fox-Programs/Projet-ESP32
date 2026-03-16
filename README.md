🏠 Système IoT de Surveillance Domestique (ESP32 + MQTT + Firebase)
Ce projet consiste en une plateforme IoT complète à l'aide de deux unités ESP32, d'un broker MQTT distant et d'une application web interactive.

📋 Fonctionnalités
🔌 Unité Capteurs (ESP32 n°1)
Mesure Environnementale : Température et humidité via un capteur DHT22.
Détection de Présence : Capteur de mouvement (PIR).
Contrôle Local : * Bouton d'activation/désactivation du flux MQTT.
Bouton d'armement/désarmement manuel du capteur de mouvement.

🚨 Unité Actionneurs & Alerte (ESP32 n°2)
Signalisation : Buzzer pour l'alerte sonore et LED RGB pour l'alerte visuelle.
Affichage : Écran OLED affichant en temps réel l'état du système et du buzzer.
Interaction : Bouton physique pour stopper l'alarme localement.

💻 Dashboard Web (Application Moderne & Responsive)
Visualisation Temps Réel : Graphiques de température/humidité et histogramme de détection (Jour vs Nuit).
Contrôle à distance : Activation de la surveillance, arrêt de l'alarme et changement de la tonalité du buzzer.
Interface Flexible : Système de Drag & Drop pour personnaliser la disposition des widgets.
Gestion d'état : Diagnostic en direct de la disponibilité de chaque composant (Health check).
Persistance : Historique des alertes stocké sur Firebase (via le client web).

🛠️ Stack Technique
Matériel : 2x ESP32, DHT22, PIR HC-SR501, LED RGB, Buzzer Actif, Écran OLED I2C.
Communication : Protocole MQTT (Broker distant).
Frontend : Framework moderne (React/Vue/JS), bibliothèques de graphiques (Chart.js/ApexCharts) et librairie de Drag & Drop.
Backend / Database : Firebase (Realtime Database ou Firestore).

🚀 Installation et Configuration
1. Configuration des ESP32
Installez les bibliothèques nécessaires dans l'IDE Arduino : PubSubClient, DHT sensor library, Adafruit SSD1306, etc.
Renseignez vos identifiants Wi-Fi et les informations du Broker MQTT dans les fichiers sources.
Téléversez le code esp32_sensors.ino sur le premier et esp32_actuators.ino sur le second.

2. Configuration Web
Créez un projet sur Firebase et récupérez votre configuration.
Ajoutez vos accès MQTT dans le fichier de configuration du frontend.


📸 Aperçu de l'Interface
Mode Surveillance : Une fois activé depuis le web, toute détection de mouvement déclenche le buzzer et la LED RGB.
Diagnostic : Si le DHT22 est débranché, l'interface grise automatiquement les graphiques associés et affiche une alerte "Déconnecté".

📝 Auteur
FACON Alexis - Projet réalisé dans le cadre de ma formation B2Info.
