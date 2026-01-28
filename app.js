// --- CONFIGURATION MQTT ---
const MQTT_BROKER = "ab8b2af6147b4edcac51c6fd3c92f133.s1.eu.hivemq.cloud";
const MQTT_PORT = 8883; // HiveMQ Cloud utilise 8883 pour TLS, 8000 pour WebSockets
const MQTT_USER = "Facon_Alexis";
const MQTT_PASS = "DpAsyqP6eck9jr9";

// Le client Web utilise WebSockets (port 8000), le chemin standard est /mqtt
const MQTT_WS_PORT = 8000;
const MQTT_PATH = "/mqtt";
const MQTT_CLIENT_ID = "DASHBOARD_WEB_ALEXIS_" + Math.random().toString(16).substr(2, 8); // ID unique

// Topics
const SUB_TOPIC_TEMP = "esp32/telemetrie/temperature";
const SUB_TOPIC_HUM = "esp32/telemetrie/humidite";
const SUB_TOPIC_MOUVEMENT = "esp32/evenement/mouvement";
const PUB_TOPIC_BUZZER = "esp32/commandes/buzzer";
const SUB_TOPIC_STATUS_EMETTEUR = "esp32/status/emetteur";
const SUB_TOPIC_STATUS_RECEPTEUR = "esp32/status/recepteur";

let mqttClient = null;
const MAX_DATA_POINTS = 20;
let temperatureReadings = [];
let totalTemperature = 0;

const componentStatus = {
    'dht': { connected: false, elementId: 'status-dht', relatedControlId: null },
    'pir': { connected: false, elementId: 'status-pir', relatedControlId: null },
    'buzzer': { connected: false, elementId: 'status-buzzer', relatedControlId: 'buzzer-frequency' }
};

// --- INITIALISATION DES GRAPHIQUES ---
const chartOptions = {
    responsive: true,
    animation: false,
    scales: {
        x: {
            type: 'time',
            time: {
                unit: 'second'
            }
        }
    },
    plugins: {
        legend: { display: false }
    }
};

// Graphique de Température
const tempCtx = document.getElementById('temperatureChart').getContext('2d');
const temperatureChart = new Chart(tempCtx, {
    type: 'line',
    data: {
        datasets: [{
            label: 'Température (°C)',
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
            borderColor: 'rgb(255, 99, 132)',
            data: [],
            parsing: false, // Utilisation de données {x, y}
        }]
    },
    options: {
        ...chartOptions,
        scales: {
            ...chartOptions.scales,
            y: { min: 0, max: 40, title: { display: true, text: '°C' } }
        }
    }
});

// Graphique d'Humidité
const humCtx = document.getElementById('humidityChart').getContext('2d');
const humidityChart = new Chart(humCtx, {
    type: 'line',
    data: {
        datasets: [{
            label: 'Humidité (%)',
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgb(54, 162, 235)',
            data: [],
            parsing: false,
        }]
    },
    options: {
        ...chartOptions,
        scales: {
            ...chartOptions.scales,
            y: { min: 0, max: 100, title: { display: true, text: '%' } }
        }
    }
});

function updateChart(chart, value, labelId) {
    const now = Date.now();
    chart.data.datasets[0].data.push({ x: now, y: value });

    // Limite le nombre de points
    if (chart.data.datasets[0].data.length > MAX_DATA_POINTS) {
        chart.data.datasets[0].data.shift();
    }

    chart.update();
    document.getElementById(labelId).textContent = value.toFixed(1);
}

// --- FONCTIONS MQTT ---
function connectMQTT() {
    console.log(`Tentative de connexion à ws://${MQTT_BROKER}:${MQTT_WS_PORT}${MQTT_PATH}`);
    mqttClient = new Paho.MQTT.Client(MQTT_BROKER, 8884, "/mqtt", MQTT_CLIENT_ID);
    mqttClient.onConnectionLost = onConnectionLost;
    mqttClient.onMessageArrived = onMessageArrived;

    const options = {
        timeout: 3,
        userName: MQTT_USER,
        password: MQTT_PASS,
        useSSL: true,
        onSuccess: onConnect,
        onFailure: onFailure
    };

    try {
        mqttClient.connect(options);
    } catch (e) {
        console.error("Erreur lors de la tentative de connexion :", e);
        updateStatus(false, "Échec");
    }
}

function onConnect() {
    console.log("Connecté à MQTT via WebSockets (WSS).");
    updateStatus(true, "Connecté");

    // Souscription aux topics de télémétrie et d'événement
    mqttClient.subscribe(SUB_TOPIC_TEMP);
    mqttClient.subscribe(SUB_TOPIC_HUM);
    mqttClient.subscribe(SUB_TOPIC_MOUVEMENT);
    mqttClient.subscribe(SUB_TOPIC_STATUS_EMETTEUR);
    mqttClient.subscribe(SUB_TOPIC_STATUS_RECEPTEUR);
    console.log("Souscription aux topics de télémétrie et mouvement.");

    // Initialiser les statuts à "Déconnecté" / "En attente" tant qu'on n'a rien reçu
    updateComponentStatus('dht', false, 'Non connecté');
    updateComponentStatus('pir', false, 'Non connecté');
    updateComponentStatus('buzzer', false, 'Non connecté');
}

function onFailure(responseObject) {
    console.log("Échec de la connexion MQTT : " + responseObject.errorMessage);
    updateStatus(false, "Déconnecté");
    setTimeout(connectMQTT, 5000);
}

function onConnectionLost(responseObject) {
    if (responseObject.errorCode !== 0) {
        console.log("Connexion perdue : " + responseObject.errorMessage);
        updateStatus(false, "Perdue");
        setTimeout(connectMQTT, 5000);
    }
}

// app.js (Modifier onMessageArrived)

function onMessageArrived(message) {
    const topic = message.destinationName;
    const payload = message.payloadString;
    let value = parseFloat(payload);

    if (topic === SUB_TOPIC_TEMP) {
        if (!isNaN(value)) {
            // Logique de la moyenne
            temperatureReadings.push(value);
            totalTemperature += value;
            const average = totalTemperature / temperatureReadings.length;
            document.getElementById('average-temp-display').textContent = average.toFixed(1);

            updateChart(temperatureChart, value, 'last-temp');
            document.getElementById('last-temp').textContent = value.toFixed(1);

            updateComponentStatus('dht', true, 'OK');
        }
    } else if (topic === SUB_TOPIC_HUM) {
        if (!isNaN(value)) {
            updateChart(humidityChart, value, 'last-hum');
            document.getElementById('last-hum').textContent = value.toFixed(1);
            // Le DHT est déjà marqué comme OK via la T°
        }
    } else if (topic === SUB_TOPIC_MOUVEMENT) {
        const pirStatusElement = document.getElementById('pir-status-display');
        pirStatusElement.textContent = payload === "DETECTE" ? "MOUVEMENT DÉTECTÉ" : "ARRET";
        pirStatusElement.className = payload === "DETECTE" ? "m-0 text-danger" : "m-0 text-success";

        // Le PIR est considéré comme connecté
        updateComponentStatus('pir', true, 'OK');
    } else if (topic === SUB_TOPIC_STATUS_EMETTEUR) {
        // L'émetteur a pu démarrer. Le statut réel des composants sera dans le payload.
        // Exemple simple: si on reçoit ce message, les composants de l'émetteur sont OK
        updateComponentStatus('dht', true, payload);
        updateComponentStatus('pir', true, payload);
    } else if (topic === SUB_TOPIC_STATUS_RECEPTEUR) {
        // Le récepteur a pu démarrer.
        updateComponentStatus('buzzer', true, payload);
    }
}

// Mettre à jour l'état et l'UI
function updateComponentStatus(componentKey, isConnected, statusText) {
    const component = componentStatus[componentKey];
    if (!component) return;

    component.connected = isConnected;
    const badgeElement = document.getElementById(component.elementId);

    // Mise à jour du badge
    if (badgeElement) {
        badgeElement.textContent = statusText;
        badgeElement.className = isConnected ? "badge bg-success" : "badge bg-danger";
    }

    // Désactivation/Activation du contrôle associé
    if (component.relatedControlId) {
        const controlElement = document.getElementById(component.relatedControlId);
        const buttonElement = document.getElementById('send-buzzer-command');
        if (controlElement) {
            controlElement.disabled = !isConnected;
        }
        if (buttonElement) {
            buttonElement.disabled = !isConnected;
        }
    }
}

// Fonction pour mettre à jour le statut général de connexion MQTT (existante, à modifier)
function updateStatus(isConnected, statusText) {
    const mqttStatusElement = document.getElementById('mqtt-status');
    mqttStatusElement.textContent = `MQTT ${statusText}`;
    mqttStatusElement.className = isConnected ? "badge bg-success" : "badge bg-danger";

    // Mise à jour de l'état MQTT de la table
    const mqttConnElement = document.getElementById('status-mqtt-conn');
    if (mqttConnElement) {
        mqttConnElement.textContent = isConnected ? "Connecté" : "Déconnecté";
        mqttConnElement.className = isConnected ? "badge bg-success" : "badge bg-danger";
    }
}

// --- CONTRÔLE BUZZER ---
function sendBuzzerCommand(freq) {
    if (mqttClient && mqttClient.isConnected()) {
        const message = new Paho.MQTT.Message(String(freq));
        message.destinationName = PUB_TOPIC_BUZZER;
        mqttClient.send(message);
        console.log(`Commande Buzzer envoyée : ${freq} Hz`);
    } else {
        alert("MQTT non connecté. Impossible d'envoyer la commande.");
    }
}

document.getElementById('send-buzzer-command').addEventListener('click', () => {
    const freq = document.getElementById('buzzer-frequency').value;
    sendBuzzerCommand(freq);
});

document.getElementById('buzzer-frequency').addEventListener('input', (e) => {
    document.getElementById('current-frequency').textContent = e.target.value;
});

// --- DRAG AND DROP (SortableJS) ---
const dashboardContainer = document.getElementById('dashboard-container');
new Sortable(dashboardContainer, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: function (evt) {
        console.log('Ordre des widgets changé.');
    },
});

// --- DÉMARRAGE DE L'APPLICATION ---
window.onload = () => {
    connectMQTT();
};