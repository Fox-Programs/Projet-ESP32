from machine import Pin, SoftI2C, PWM
from time import sleep
import network
import gc

from umqtt import MQTTClient
import ssl as ssl_lib
import utime
from lcd_lib import LCD

# --- CONFIGURATION ---
WIFI_SSID = "FOXconnect"
WIFI_PASS = "FoxFurryPaws"

# --- CONFIGURATION MQTT SECURISEE
MQTT_BROKER = "ab8b2af6147b4edcac51c6fd3c92f133.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Facon_Alexis"
MQTT_PASS = "DpAsyqP6eck9jr9"
MQTT_CLIENT_ID = "ESP32_RECEPTEUR_ALEXIS"


# Topics de Souscription
SUB_TOPIC_TEMP = b"esp32/telemetrie/temperature"
SUB_TOPIC_HUM = b"esp32/telemetrie/humidite"
SUB_TOPIC_MOUVEMENT = b"esp32/evenement/mouvement"
SUB_TOPIC_BUZZER_CMD = b"esp32/commandes/buzzer"
TOPIC_STATUS_MQTT = b"esp32/status/mqtt"
TOPIC_STATUS_RECEPTEUR = b"esp32/status/recepteur"

# --- BROCHES PÉRIPHÉRIQUE  ---
LED_R_PIN = 25
BUZZER_PIN = 13
BTN_STOP_PIN = 5

# OLED I2C
OLED_SCL = 18
OLED_SDA = 19
I2C_FREQ = 400000

# PWM Setup
led_r = Pin(LED_R_PIN, Pin.OUT)
buzzer_pwm = PWM(Pin(BUZZER_PIN), freq=1000, duty=0)
btn_stop = Pin(BTN_STOP_PIN, Pin.IN, Pin.PULL_UP)

# --- VARIABLES D'ÉTAT ---
is_alert = False
buzzer_muted = False
last_temp = 0.0
last_hum = 0.0
movement_status = "ARRET"
last_stop_toggle = utime.ticks_ms()

# Instances
try:
    i2c = SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=I2C_FREQ)
    display = LCD(i2c)
    print("OLED connecté")
except Exception as e:
    print(f"Erreur LCD non initialisé: {e}")

def start_alert_visuals():
    global buzzer_muted, is_alert
    is_alert = True
    if not buzzer_muted:
        buzzer_pwm.duty(512)
        # La fréquence par défaut si aucune n'a été envoyée
        if buzzer_pwm.freq() == 0 or buzzer_pwm.freq() is None:
             buzzer_pwm.freq(1000)


def stop_alert_visuals():
    global is_alert
    is_alert = False
    buzzer_pwm.duty(0)


# --- Fonction Callback MQTT ---
def sub_cb(topic, msg):
    global last_temp, last_hum, movement_status
    msg_str = msg.decode()

    if topic == SUB_TOPIC_TEMP:
        # ... (Logique T° existante) ...
        try:
            last_temp = float(msg_str)
        except ValueError:
            pass

    elif topic == SUB_TOPIC_HUM:
        # ... (Logique H% existante) ...
        try:
            last_hum = float(msg_str)
        except ValueError:
            pass

    elif topic == SUB_TOPIC_MOUVEMENT:
        # ... (Logique Mouvement existante) ...
        if msg_str == "DETECTE":
            movement_status = "MOUVEMENT"
            start_alert_visuals()
        else:
            movement_status = "ARRET"
            stop_alert_visuals()

    # NOUVELLE LOGIQUE POUR LE BUZZER
    elif topic == SUB_TOPIC_BUZZER_CMD:
        try:
            new_freq = int(msg_str)
            # Limite la fréquence pour éviter les problèmes
            if 200 <= new_freq <= 4000:
                if is_alert and not buzzer_muted:
                    buzzer_pwm.freq(new_freq)
                print(f"Fréquence Buzzer changée à {new_freq} Hz par commande web.")
        except ValueError:
            print("Commande Buzzer reçue invalide.")


# --- Fonctions WiFi et MQTT ---
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
        gc.collect()
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
        client.set_callback(sub_cb)
        client.connect()
        print("MQTT Connecté au cluster HiveMQ Cloud (TLS).")
        client.publish(TOPIC_STATUS_RECEPTEUR, b"Buzzer OK", retain = True)
        client.subscribe(SUB_TOPIC_TEMP)
        client.subscribe(SUB_TOPIC_HUM)
        client.subscribe(SUB_TOPIC_MOUVEMENT)
        client.subscribe(SUB_TOPIC_BUZZER_CMD)
        return client
    except Exception as e:
        print(f"Échec de la connexion MQTT: {e}")
        print(f"Type d'erreur : {type(e).__name__}")
        return None


# --- Fonctions Affichage et Contrôle ---
def update_oled():
    display.clear()

    # Ligne 1: T° et H%
    display.puts(f"T: {last_temp:02.1f}C H: {last_hum:02.1f}%", y=0, x=0)

    # Ligne 2: Alerte
    alert_text = "ALERTE: OUI" if is_alert else "ALERTE: NON"
    display.puts(alert_text, y=1, x=0)

    # Ligne 3: Statut du buzzer
    buzzer_state = "ON" if (is_alert and not buzzer_muted) else ("MUTED" if buzzer_muted else "OFF")
    display.puts(f"Buzzer: {buzzer_state}", y=2, x=0)

    # Ligne 4: Mouvement
    display.puts(f"Mouv: {movement_status}", y=3, x=0)

    if hasattr(display, 'show'):
        display.show()
    elif hasattr(display, 'display'):
        display.display()

def check_stop_button():
    global buzzer_muted, last_stop_toggle
    current_time = utime.ticks_ms()
    if btn_stop.value() == 0 and utime.ticks_diff(current_time, last_stop_toggle) > 300:
        if is_alert:
            buzzer_muted = not buzzer_muted
            buzzer_pwm.duty(512 if not buzzer_muted else 0)
            print(f"Buzzer {'ACTIF' if not buzzer_muted else 'MUTE'} par bouton.")
        else:
            buzzer_muted = False
        last_stop_toggle = current_time

# --- BOUCLE PRINCIPALE ---
wifi = connect_wifi()
client = connect_mqtt()

while True:
    try:
        if client:
            client.check_msg()
        check_stop_button()

        # Clignotement de la LED en cas d'alerte (si le buzzer est toujours actif)
        if is_alert and not buzzer_muted:
            static_last_blink = 0
            BLINK_INTERVAL = 500
            current_time = utime.ticks_ms()
            if utime.ticks_diff(current_time, static_last_blink) > BLINK_INTERVAL:
                static_last_blink = current_time
                led_r.value(not led_r.value())

        # Mettre a jour l'affichage toutes les 1000ms
        static_last_display_update = 0
        DISPLAY_INTERVAL = 1000
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, static_last_display_update) > DISPLAY_INTERVAL:
            update_oled()
            static_last_display_update = current_time

    except Exception as e:
        print(f"Erreur Récepteur: {e}")
        client = None
        sleep(5)
        # Tenter de reconnecter
        if not wifi.isconnected():
            connect_wifi()
        client = connect_mqtt()

    sleep(0.01)