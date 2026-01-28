# --- IMPORTS CRUCIAUX POUR TLS ---
import gc
import network
from time import sleep
import dht
import utime
from machine import Pin
from umqtt import MQTTClient
import ssl as ssl_lib

# --- CONFIGURATION À MODIFIER ---
WIFI_SSID = "FOXconnect"
WIFI_PASS = "FoxFurryPaws"
MQTT_BROKER = "ab8b2af6147b4edcac51c6fd3c92f133.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Facon_Alexis"
MQTT_PASS = "DpAsyqP6eck9jr9"
MQTT_CLIENT_ID = "ESP32_EMETTEUR_ALEXIS"

# Topics de Publication
TOPIC_TEMP = b"esp32/telemetrie/temperature"
TOPIC_HUM = b"esp32/telemetrie/humidite"
TOPIC_DETECTION_PIR = b"esp32/evenement/mouvement"
TOPIC_STATUS_EMETTEUR = b"esp32/status/emetteur"
TOPIC_STATUS_MQTT = b"esp32/status/mqtt"

# --- BROCHES CAPTEURS ET CONTRÔLES ---
DHT_PIN = 27
sensor_dht = dht.DHT11(Pin(DHT_PIN))

PIR_PIN = 13
pir_pin = Pin(PIR_PIN, Pin.IN)

BTN_MQTT_PIN = 26
btn_mqtt = Pin(BTN_MQTT_PIN, Pin.IN, Pin.PULL_UP)
mqtt_enabled = True

BTN_PIR_PIN = 25
btn_pir = Pin(BTN_PIR_PIN, Pin.IN, Pin.PULL_UP)
pir_active = True


# --- FONCTIONS GÉNÉRALES ---
def connect_wifi():
    """Tente de connecter l'ESP32 au réseau Wi-Fi."""
    print("Connecting to WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if not sta_if.isconnected():
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        while not sta_if.isconnected():
            print(".", end="")
            sleep(0.5)
    print(" Connected!")
    return sta_if


def connect_mqtt():
    """Tente de connecter l'ESP32 au broker MQTT sécurisé (TLS)."""
    global client
    try:
        # Configuration des paramètres TLS (SNI)
        ssl_params = {"server_hostname": MQTT_BROKER}

        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            user=MQTT_USER,
            password=MQTT_PASS,
            ssl=ssl_lib,
            ssl_params=ssl_params
        )
        client.connect()
        print("MQTT Connecté au cluster HiveMQ Cloud (TLS).")
        client.publish(TOPIC_STATUS_EMETTEUR, b"DHT+PIR OK")
        return client
    except Exception as e:
        print(f"Échec de la connexion MQTT: {e}")
        print(f"Type d'erreur : {type(e).__name__}")
        return None


# --- INITIALISATION ET BOUCLE PRINCIPALE ---
wifi = connect_wifi()
client = connect_mqtt()
last_mqtt_toggle = utime.ticks_ms()
last_pir_toggle = utime.ticks_ms()

DHT_INTERVAL = 3000
last_pir_detection = 0
last_dht_detection = 0
DEBOUNCE_DELAY_MS = 200

while True:
    current_time = utime.ticks_ms()

    # --- Logique Bouton MQTT (avec Debouncing) ---
    if btn_mqtt.value() == 0:
        print("Button Pressed")
        # Vérifie si le temps écoulé depuis le dernier traitement est suffisant
        if utime.ticks_diff(current_time, last_mqtt_toggle) > DEBOUNCE_DELAY_MS:
            mqtt_enabled = not mqtt_enabled
            last_mqtt_toggle = current_time # Mise à jour du temps de bascule
            if mqtt_enabled:
                print("--- MQTT ACTIF ---")
            else :
                client.publish(TOPIC_DETECTION_PIR, b"MQTT DOWN")
                print("--- MQTT INACTIF ---")

            if mqtt_enabled and not client:
                client = connect_mqtt()
        sleep(0.2)

    # --- Logique Bouton PIR (avec Debouncing) ---
    if btn_pir.value() == 0:
        print("Button Pressed")
        # Vérifie si le temps écoulé depuis le dernier traitement est suffisant
        if utime.ticks_diff(current_time, last_pir_toggle) > DEBOUNCE_DELAY_MS:
            pir_active = not pir_active
            last_pir_toggle = current_time # Mise à jour du temps de bascule

            print("--- CAPTEUR PIR ACTIF/INACTIF ---", "ACTIF" if pir_active else "INACTIF")
        sleep(0.2)

    # Logique de publication MQTT
    if mqtt_enabled and client:
        try:
            client.check_msg()
            sensor_dht.measure()
            temp = sensor_dht.temperature()
            hum = sensor_dht.humidity()

            if utime.ticks_diff(current_time, last_dht_detection) > 1000:
                client.publish(TOPIC_TEMP, str(temp).encode())
                client.publish(TOPIC_HUM, str(hum).encode())
                last_dht_detection = current_time

            # Lecture et Publication PIR
            if pir_active:
                if pir_pin.value() == 1 and utime.ticks_diff(current_time, last_pir_detection) > 1000:
                    client.publish(TOPIC_DETECTION_PIR, b"DETECTE")
                    print("MOUVEMENT DÉTECTÉ et publié!")
                    last_pir_detection = current_time
                elif utime.ticks_diff(current_time, last_pir_detection) > 1000:
                    client.publish(TOPIC_DETECTION_PIR, b"NON DETECTE")
                    print("MOUVEMENT NON DÉTECTÉ et publié!")
                    last_pir_detection = current_time
            elif utime.ticks_diff(current_time, last_pir_detection) > 1000:
                client.publish(TOPIC_DETECTION_PIR, b"NON DETECTE")
                print("ARRÊT publié!")
                last_pir_detection = current_time


        except Exception as e:
            # Gère les erreurs liées à MQTT (perte de connexion, etc.)
            print(f"--- Erreur critique MQTT/Réseau: {e} ---")
            client = None
            gc.collect()
            sleep(5)

            # Tente de se reconnecter
            if mqtt_enabled:
                if not wifi.isconnected():
                    wifi = connect_wifi()  # Reconnexion WiFi
                client = connect_mqtt()  # Reconnexion MQTT

    elif not mqtt_enabled and client:
        # Si le bouton est sur INACTIF, déconnecte proprement MQTT si client existe
        try:
            client.disconnect()
            print("Déconnexion MQTT propre.")
        except:
            pass
        client = None

    sleep(0.01)