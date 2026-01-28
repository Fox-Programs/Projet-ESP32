# main.py
import machine
import dht
import time

# --- Configuration du Capteur DHT11 ---
# Assurez-vous que le DHT11 est connecté à la broche GPIO 27 (D27)
DHT_PIN = 27
sensor = dht.DHT11(machine.Pin(DHT_PIN))

print("Démarrage de la lecture du DHT11...")

# --- Boucle Principale de Lecture ---
while True:
    try:
        # 1. Effectuer la mesure
        sensor.measure()

        # 2. Récupérer les valeurs
        temp = sensor.temperature()
        humi = sensor.humidity()

        # 3. Afficher les résultats dans le terminal
        print("---------------------------------")
        print(f"🌡️ Température: {temp:.1f} °C")
        print(f"💧 Humidité:    {humi:.1f} %")
        print("---------------------------------")

    except OSError as e:
        # Gérer les erreurs de lecture du capteur (courantes avec le DHT)
        print("⚠️ Erreur de lecture du capteur DHT11 :", e)
        print("   Vérifiez le câblage et la résistance pull-up.")

    # 4. Attendre 5 secondes avant la prochaine lecture
    time.sleep(5)