/*
 * TalentUP Fichaje - Firmware ESP32 para lector NFC
 * =================================================
 *
 * Lee tarjetas NFC con PN532 via SPI y envía el UID al backend
 * TalentUP Fichaje para registrar entrada/salida.
 *
 * Conexiones ESP32 -> PN532:
 *   GPIO5  (SS)   -> NSS  (CS)
 *   GPIO18 (SCK)  -> SCK
 *   GPIO19 (MISO) -> MISO
 *   GPIO23 (MOSI) -> MOSI
 *   GPIO2  (LED Verde)
 *   GPIO4  (LED Rojo)
 *
 * Librerías necesarias (PlatformIO / Arduino IDE):
 *   - WiFi (built-in ESP32)
 *   - HTTPClient (built-in ESP32)
 *   - ArduinoJson       ^6.x
 *   - Adafruit PN532    ^1.3
 *   - Adafruit BusIO     (dependencia PN532)
 *   - SPI (built-in ESP32)
 */

// ===================== CONFIGURACIÓN =====================
#ifndef WIFI_SSID
#define WIFI_SSID       "TU_WIFI_SSID"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS       "TU_WIFI_PASSWORD"
#endif
#ifndef BACKEND_URL
#define BACKEND_URL     "http://192.168.1.100:8000"
#endif
#ifndef TENANT_ID
#define TENANT_ID       "CAMBIAR-POR-TU-TENANT-ID-UUID"
#endif

// Pines
#define PIN_LED_GREEN   2
#define PIN_LED_RED     4
#define PIN_PN532_SS    5
#define PIN_PN532_SCK   18
#define PIN_PN532_MISO  19
#define PIN_PN532_MOSI  23

// Temporización
#define DEBOUNCE_MS     2000
#define LED_ON_MS       1500
#define WIFI_RETRY_S    5
#define NFC_POLL_MS     100

// ==========================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// Instancia PN532 por SPI
Adafruit_PN532 nfc(PIN_PN532_SS);

// Estado
String lastUID = "";
unsigned long lastReadTime = 0;
unsigned long lastLedOffTime = 0;
bool ledActive = false;

// ===================== PROTOTIPOS =====================
void connectWiFi();
void sendToBackend(const String &uid);
void setLED(bool green, bool red);
void blinkError(int times, int delayMs);
void fatalError();

// ===================== SETUP ==========================
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  TalentUP Fichaje - ESP32 NFC Reader"));
  Serial.println(F("========================================"));

  // LEDs
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  setLED(false, false);

  // --- WiFi ---
  connectWiFi();

  // --- PN532 ---
  // Configurar pines SPI explícitamente para ESP32
  SPI.begin(PIN_PN532_SCK, PIN_PN532_MISO, PIN_PN532_MOSI, PIN_PN532_SS);
  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println(F("[FATAL] No se detecta PN532. Revisa conexiones."));
    fatalError();
  }

  // Mostrar versión del chip PN532
  Serial.print(F("PN532 detectado - Chip: "));
  Serial.print((versiondata >> 24) & 0xFF, HEX);
  Serial.print(F(" Rev: "));
  Serial.print((versiondata >> 16) & 0xFF, DEC);
  Serial.print(F(" V")); Serial.print((versiondata >> 8) & 0xFF, DEC);
  Serial.println();

  // Configurar modo SAM (lectura de tarjetas)
  nfc.SAMConfig();

  Serial.println();
  Serial.println(F("TalentUP Fichaje - Esperando tarjeta..."));
  Serial.println();
}

// ===================== LOOP ===========================
void loop() {
  // --- Verificar WiFi ---
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WARN] WiFi desconectado. Reintentando..."));
    setLED(false, true);
    connectWiFi();
    setLED(false, false);
    return;
  }

  // --- Apagar LEDs tras el tiempo configurado ---
  if (ledActive && (millis() - lastLedOffTime >= LED_ON_MS)) {
    setLED(false, false);
    ledActive = false;
  }

  // --- Leer tarjeta NFC ---
  uint8_t uid[7];
  uint8_t uidLength;

  boolean success = nfc.readPassiveTargetID(
    PN532_MIFARE_ISO14443A, uid, &uidLength, NFC_POLL_MS
  );

  if (!success) {
    return;  // No hay tarjeta presente
  }

  // Debounce
  unsigned long now = millis();
  if (now - lastReadTime < DEBOUNCE_MS) {
    return;
  }
  lastReadTime = now;

  // Convertir UID a hex string con formato XX:XX:XX:XX (igual que la BD)
  String uidStr = "";
  for (uint8_t i = 0; i < uidLength; i++) {
    if (i > 0) uidStr += ":";
    if (uid[i] < 0x10) uidStr += "0";
    uidStr += String(uid[i], HEX);
  }
  uidStr.toUpperCase();

  // Evitar lecturas duplicadas consecutivas
  if (uidStr == lastUID) {
    return;
  }
  lastUID = uidStr;

  Serial.println(F("----------------------------------------"));
  Serial.print(F("Tarjeta detectada - UID: "));
  Serial.println(uidStr);
  Serial.println(F("----------------------------------------"));

  // Enviar al backend
  sendToBackend(uidStr);
}

// ===================== FUNCIONES ======================

/**
 * Conecta al WiFi con reintentos cada WIFI_RETRY_S segundos.
 */
void connectWiFi() {
  Serial.print(F("Conectando a WiFi: "));
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;

    if (attempts >= 40) {  // ~20 segundos
      Serial.println();
      Serial.print(F("[ERROR] No se pudo conectar a '"));
      Serial.print(WIFI_SSID);
      Serial.println(F("'. Reintentando en 5s..."));
      delay(WIFI_RETRY_S * 1000);
      attempts = 0;
      WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
  }

  Serial.println();
  Serial.print(F("WiFi conectado. IP: "));
  Serial.println(WiFi.localIP());
  Serial.print(F("SSID: "));
  Serial.println(WiFi.SSID());
}

/**
 * Envía el UID de la tarjeta al backend via POST JSON.
 * Parsea la respuesta y muestra el resultado por Serial.
 */
void sendToBackend(const String &uid) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[ERROR] No hay conexión WiFi para enviar datos."));
    setLED(false, true);
    ledActive = true;
    lastLedOffTime = millis();
    return;
  }

  HTTPClient http;
  String url = String(BACKEND_URL) + "/api/clock/nfc";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  // Timeout de 5 segundos
  http.setTimeout(5000);

  // Construir JSON body
  StaticJsonDocument<256> doc;
  doc["nfc_uid"] = uid;
  doc["tenant_id"] = TENANT_ID;

  String jsonBody;
  serializeJson(doc, jsonBody);

  Serial.print(F("POST -> "));
  Serial.println(url);
  Serial.print(F("Body: "));
  Serial.println(jsonBody);

  // Enviar petición
  int httpCode = http.POST(jsonBody);

  if (httpCode > 0) {
    String response = http.getString();
    response.trim();

    Serial.print(F("HTTP "));
    Serial.print(httpCode);
    Serial.print(F(": "));
    Serial.println(response);

    if (httpCode == 200 || httpCode == 201) {
      // Intentar parsear respuesta JSON del backend
      StaticJsonDocument<512> respDoc;
      DeserializationError err = deserializeJson(respDoc, response);

      if (!err) {
        // Respuesta JSON esperada: { "status": "ok", "message": "...", "employee": "...", "type": "..." }
        const char *status  = respDoc["status"] | "";
        const char *message = respDoc["message"] | "";
        const char *employee = respDoc["employee"] | "";
        const char *type    = respDoc["type"] | "";

        if (strcmp(status, "ok") == 0) {
          Serial.print(F("OK: "));
          if (strlen(employee) > 0) {
            Serial.print(employee);
            Serial.print(F(" - "));
          }
          if (strlen(type) > 0) {
            Serial.print(type);
            Serial.print(F(" "));
          }
          if (strlen(message) > 0) {
            Serial.print(message);
          }
          Serial.println();
          setLED(true, false);  // Verde
        } else {
          Serial.print(F("ERROR: "));
          Serial.println(message);
          setLED(false, true);  // Rojo
        }
      } else {
        // Respuesta no JSON - mostrar raw
        Serial.print(F("OK: "));
        Serial.println(response);
        setLED(true, false);
      }
    } else {
      // Error HTTP (4xx, 5xx)
      Serial.print(F("ERROR: "));
      if (response.length() > 0) {
        // Intentar extraer mensaje del JSON de error
        StaticJsonDocument<256> errDoc;
        DeserializationError err = deserializeJson(errDoc, response);
        if (!err && errDoc["message"].is<const char*>()) {
          Serial.println(errDoc["message"].as<const char*>());
        } else {
          Serial.println(response);
        }
      } else {
        Serial.print(F("HTTP error code: "));
        Serial.println(httpCode);
      }
      setLED(false, true);
    }
  } else {
    // Error de conexión (timeout, DNS, etc.)
    Serial.print(F("[ERROR] No se pudo contactar el backend. Código: "));
    Serial.println(httpCode);
    Serial.print(F("  URL: "));
    Serial.println(url);
    setLED(false, true);
  }

  http.end();
  ledActive = true;
  lastLedOffTime = millis();
}

/**
 * Controla los LEDs.
 * @param green true = enciende LED verde
 * @param red   true = enciende LED rojo
 */
void setLED(bool green, bool red) {
  digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_LED_RED, red ? HIGH : LOW);
}

/**
 * Parpadea el LED rojo N veces (para indicar error).
 */
void blinkError(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(PIN_LED_RED, HIGH);
    delay(delayMs);
    digitalWrite(PIN_LED_RED, LOW);
    if (i < times - 1) delay(delayMs);
  }
}

/**
 * Error fatal: parpadeo infinito rojo, bloquea el programa.
 */
void fatalError() {
  while (1) {
    digitalWrite(PIN_LED_RED, HIGH);
    delay(300);
    digitalWrite(PIN_LED_RED, LOW);
    delay(300);
  }
}
