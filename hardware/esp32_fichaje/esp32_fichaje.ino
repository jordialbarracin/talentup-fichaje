/*
 * TalentUP Fichaje - Firmware ESP32 para lector NFC
 * =================================================
 *
 * Lee tarjetas NFC con PN532 via SPI y envía el UID al backend
 * TalentUP Fichaje para registrar entrada/salida.
 * Incluye cola offline con SPIFFS para operación sin conexión
 * y watchdog timer para reinicio automático en caso de cuelgue.
 *
 * Conexiones ESP32 -> PN532:
 *   GPIO5  (SS)   -> NSS  (CS)
 *   GPIO18 (SCK)  -> SCK
 *   GPIO19 (MISO) -> MISO
 *   GPIO23 (MOSI) -> MOSI
 *   GPIO2  (LED Verde)
 *   GPIO4  (LED Rojo)
 *   GPIO15 (LED Azul - cola offline)
 *
 * Librerías necesarias (PlatformIO / Arduino IDE):
 *   - WiFi (built-in ESP32)
 *   - HTTPClient (built-in ESP32)
 *   - ArduinoJson       ^6.x
 *   - Adafruit PN532    ^1.3
 *   - Adafruit BusIO     (dependencia PN532)
 *   - SPI (built-in ESP32)
 *   - SPIFFS (built-in ESP32)
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
#define PIN_LED_BLUE    15
#define PIN_PN532_SS    5
#define PIN_PN532_SCK   18
#define PIN_PN532_MISO  19
#define PIN_PN532_MOSI  23

// Temporización
#define DEBOUNCE_MS     2000
#define LED_ON_MS       1500
#define WIFI_RETRY_S    5
#define NFC_POLL_MS     100
#define SYNC_INTERVAL_MS 30000   // 30s entre intentos de sincronización
#define WDT_TIMEOUT_S   10       // Watchdog timeout en segundos
#define MAX_QUEUE_SIZE  100      // Máximo de fichajes en cola offline

// ==========================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_PN532.h>
#include <SPIFFS.h>
#include <esp_task_wdt.h>

// Instancia PN532 por SPI
Adafruit_PN532 nfc(PIN_PN532_SS);

// Estado
String lastUID = "";
unsigned long lastReadTime = 0;
unsigned long lastLedOffTime = 0;
bool ledActive = false;
unsigned long lastSyncTime = 0;
int pendingCount = 0;           // Fichajes pendientes de sincronizar
unsigned long lastBlueToggle = 0;
bool blueState = false;

// ===================== PROTOTIPOS =====================
void connectWiFi();
void sendToBackend(const String &uid);
void setLED(bool green, bool red);
void blinkError(int times, int delayMs);
void fatalError();
void initSPIFFS();
bool saveToQueue(const String &uid);
int loadQueue(JsonArray &arr);
bool writeQueue(JsonArray &arr);
void syncQueue();
void updateBlueLED();
void feedWatchdog();

// ===================== SETUP ==========================
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  TalentUP Fichaje - ESP32 NFC Reader"));
  Serial.println(F("  Con cola offline SPIFFS + WDT"));
  Serial.println(F("========================================"));

  // LEDs
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  setLED(false, false);
  digitalWrite(PIN_LED_BLUE, LOW);

  // --- Watchdog Timer (10s, reinicia si se cuelga) ---
  esp_task_wdt_init(WDT_TIMEOUT_S, true);
  esp_task_wdt_add(NULL);
  feedWatchdog();

  // --- SPIFFS ---
  initSPIFFS();

  // --- WiFi ---
  connectWiFi();

  // --- PN532 ---
  SPI.begin(PIN_PN532_SCK, PIN_PN532_MISO, PIN_PN532_MOSI, PIN_PN532_SS);
  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println(F("[FATAL] No se detecta PN532. Revisa conexiones."));
    fatalError();
  }

  Serial.print(F("PN532 detectado - Chip: "));
  Serial.print((versiondata >> 24) & 0xFF, HEX);
  Serial.print(F(" Rev: "));
  Serial.print((versiondata >> 16) & 0xFF, DEC);
  Serial.print(F(" V")); Serial.print((versiondata >> 8) & 0xFF, DEC);
  Serial.println();

  nfc.SAMConfig();

  // Cargar cola pendiente al arrancar
  pendingCount = 0;
  {
    StaticJsonDocument<6144> doc;
    JsonArray arr = doc.to<JsonArray>();
    pendingCount = loadQueue(arr);
  }
  if (pendingCount > 0) {
    Serial.print(F("[INFO] "));
    Serial.print(pendingCount);
    Serial.println(F(" fichajes pendientes de sincronizar."));
  }

  Serial.println();
  Serial.println(F("TalentUP Fichaje - Esperando tarjeta..."));
  Serial.println();
}

// ===================== LOOP ==========================
void loop() {
  feedWatchdog();

  // --- Verificar WiFi (reconectar si es necesario) ---
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WARN] WiFi desconectado. Reintentando..."));
    setLED(false, true);
    connectWiFi();
    setLED(false, false);
    // No hacemos return: permitimos lectura NFC offline
  }

  // --- Sincronizar cola pendiente cada 30s ---
  unsigned long now = millis();
  if (WiFi.status() == WL_CONNECTED && (now - lastSyncTime >= SYNC_INTERVAL_MS || lastSyncTime == 0)) {
    lastSyncTime = now;
    syncQueue();
  }

  // --- LED azul: parpadeo si hay pendientes ---
  updateBlueLED();

  // --- Apagar LEDs tras el tiempo configurado ---
  if (ledActive && (now - lastLedOffTime >= LED_ON_MS)) {
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
  if (now - lastReadTime < DEBOUNCE_MS) {
    return;
  }
  lastReadTime = now;

  // Convertir UID a hex string con formato XX:XX:XX:XX
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

  // Enviar al backend (o guardar offline si no hay conexión)
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
    feedWatchdog();

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
 * Si no hay WiFi o falla la conexión, guarda en cola offline.
 */
void sendToBackend(const String &uid) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WARN] No hay conexión WiFi. Guardando offline..."));
    if (saveToQueue(uid)) {
      Serial.print(F("Fichaje guardado offline ("));
      Serial.print(pendingCount);
      Serial.println(F(" en cola)"));
    }
    setLED(false, true);
    ledActive = true;
    lastLedOffTime = millis();
    return;
  }

  HTTPClient http;
  String url = String(BACKEND_URL) + "/api/clock/nfc";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  StaticJsonDocument<256> doc;
  doc["nfc_uid"] = uid;
  doc["tenant_id"] = TENANT_ID;

  String jsonBody;
  serializeJson(doc, jsonBody);

  Serial.print(F("POST -> "));
  Serial.println(url);
  Serial.print(F("Body: "));
  Serial.println(jsonBody);

  int httpCode = http.POST(jsonBody);

  if (httpCode > 0) {
    String response = http.getString();
    response.trim();

    Serial.print(F("HTTP "));
    Serial.print(httpCode);
    Serial.print(F(": "));
    Serial.println(response);

    if (httpCode == 200 || httpCode == 201) {
      StaticJsonDocument<512> respDoc;
      DeserializationError err = deserializeJson(respDoc, response);

      if (!err) {
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
          setLED(true, false);
        } else {
          Serial.print(F("ERROR: "));
          Serial.println(message);
          setLED(false, true);
        }
      } else {
        Serial.print(F("OK: "));
        Serial.println(response);
        setLED(true, false);
      }
    } else {
      // Error HTTP (4xx, 5xx)
      Serial.print(F("ERROR: "));
      if (response.length() > 0) {
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
    // Error de conexión (timeout, DNS, etc.) - guardar offline
    Serial.print(F("[ERROR] No se pudo contactar el backend. Código: "));
    Serial.println(httpCode);
    Serial.print(F("  URL: "));
    Serial.println(url);

    if (saveToQueue(uid)) {
      Serial.print(F("Fichaje guardado offline ("));
      Serial.print(pendingCount);
      Serial.println(F(" en cola)"));
    }
    setLED(false, true);
  }

  http.end();
  ledActive = true;
  lastLedOffTime = millis();
}

/**
 * Controla los LEDs.
 */
void setLED(bool green, bool red) {
  digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_LED_RED, red ? HIGH : LOW);
}

/**
 * Parpadea el LED rojo N veces.
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

// ============== FUNCIONES COLA OFFLINE (SPIFFS) ==============

#define QUEUE_FILE "/queue.json"

/**
 * Inicializa SPIFFS. Si falla, formatea automáticamente.
 */
void initSPIFFS() {
  if (!SPIFFS.begin(true)) {
    Serial.println(F("[ERROR] SPIFFS mount failed. Formateando..."));
    if (!SPIFFS.format()) {
      Serial.println(F("[FATAL] SPIFFS format failed."));
      fatalError();
    }
    if (!SPIFFS.begin(true)) {
      Serial.println(F("[FATAL] SPIFFS remount failed after format."));
      fatalError();
    }
  }
  Serial.println(F("[OK] SPIFFS montado correctamente."));
}

/**
 * Carga la cola de fichajes desde SPIFFS a un JsonArray.
 * Devuelve el número de entradas pendientes (synced=false).
 */
int loadQueue(JsonArray &arr) {
  if (!SPIFFS.exists(QUEUE_FILE)) {
    return 0;
  }

  File file = SPIFFS.open(QUEUE_FILE, "r");
  if (!file) {
    Serial.println(F("[WARN] No se pudo abrir queue.json para lectura."));
    return 0;
  }

  size_t size = file.size();
  if (size == 0) {
    file.close();
    return 0;
  }

  String content = file.readString();
  file.close();

  DeserializationError err = deserializeJson(arr, content);
  if (err) {
    Serial.print(F("[WARN] Error parseando queue.json: "));
    Serial.println(err.c_str());
    return 0;
  }

  // Contar pendientes
  int count = 0;
  for (size_t i = 0; i < arr.size(); i++) {
    if (!arr[i]["synced"].as<bool>()) {
      count++;
    }
  }
  return count;
}

/**
 * Escribe un JsonArray completo a SPIFFS.
 */
bool writeQueue(JsonArray &arr) {
  File file = SPIFFS.open(QUEUE_FILE, "w");
  if (!file) {
    Serial.println(F("[ERROR] No se pudo abrir queue.json para escritura."));
    return false;
  }

  serializeJson(arr, file);
  file.close();
  return true;
}

/**
 * Guarda un fichaje en la cola offline.
 * Formato: { "uid": "XX:XX:XX:XX", "timestamp": 1234567890, "synced": false }
 * Máximo MAX_QUEUE_SIZE entradas (FIFO: descarta la más antigua si está llena).
 */
bool saveToQueue(const String &uid) {
  StaticJsonDocument<6144> doc;
  JsonArray arr = doc.to<JsonArray>();

  // Cargar cola existente
  loadQueue(arr);

  // Verificar límite: si está llena, descartar la más antigua
  if (arr.size() >= MAX_QUEUE_SIZE) {
    Serial.println(F("[WARN] Cola offline llena. Descartando fichaje más antiguo..."));
    for (size_t i = 1; i < arr.size(); i++) {
      arr[i - 1] = arr[i];
    }
    arr.remove(arr.size() - 1);
  }

  // Añadir nuevo fichaje
  JsonObject entry = arr.createNestedObject();
  entry["uid"] = uid;
  entry["timestamp"] = millis() / 1000;  // Tiempo desde arranque (relativo)
  entry["synced"] = false;

  if (!writeQueue(arr)) {
    return false;
  }

  // Actualizar contador de pendientes
  pendingCount = 0;
  for (size_t i = 0; i < arr.size(); i++) {
    if (!arr[i]["synced"].as<bool>()) {
      pendingCount++;
    }
  }

  return true;
}

/**
 * Intenta sincronizar todos los fichajes pendientes con el backend.
 * Si OK, marca synced=true y elimina del queue.
 * Si falla alguno, mantiene en cola para reintentar.
 */
void syncQueue() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  StaticJsonDocument<6144> doc;
  JsonArray arr = doc.to<JsonArray>();
  int total = loadQueue(arr);

  if (total == 0) {
    return;
  }

  // Contar solo los pendientes
  int pendientes = 0;
  for (size_t i = 0; i < arr.size(); i++) {
    if (!arr[i]["synced"].as<bool>()) {
      pendientes++;
    }
  }

  if (pendientes == 0) {
    return;
  }

  Serial.print(F("Sincronizando "));
  Serial.print(pendientes);
  Serial.println(F(" fichajes..."));

  bool allSynced = true;
  for (size_t i = 0; i < arr.size(); i++) {
    if (arr[i]["synced"].as<bool>()) {
      continue;
    }

    const char *uid = arr[i]["uid"] | "";

    HTTPClient http;
    String url = String(BACKEND_URL) + "/api/clock/nfc";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);

    StaticJsonDocument<256> postDoc;
    postDoc["nfc_uid"] = uid;
    postDoc["tenant_id"] = TENANT_ID;

    String jsonBody;
    serializeJson(postDoc, jsonBody);

    int httpCode = http.POST(jsonBody);
    http.end();

    if (httpCode == 200 || httpCode == 201) {
      arr[i]["synced"] = true;
      Serial.print(F("  OK: "));
      Serial.println(uid);
    } else {
      Serial.print(F("  FAIL: "));
      Serial.print(uid);
      Serial.print(F(" (HTTP "));
      Serial.print(httpCode);
      Serial.println(F(")"));
      allSynced = false;
    }

    feedWatchdog();
  }

  if (allSynced) {
    // Todos sincronizados - limpiar cola
    arr.clear();
    Serial.println(F("Todo sincronizado"));
  }

  // Guardar estado actualizado
  writeQueue(arr);

  // Actualizar contador
  pendingCount = 0;
  for (size_t i = 0; i < arr.size(); i++) {
    if (!arr[i]["synced"].as<bool>()) {
      pendingCount++;
    }
  }
}

/**
 * Actualiza el LED azul: parpadea cada 500ms cuando hay fichajes pendientes.
 */
void updateBlueLED() {
  if (pendingCount > 0) {
    unsigned long now = millis();
    if (now - lastBlueToggle >= 500) {
      lastBlueToggle = now;
      blueState = !blueState;
      digitalWrite(PIN_LED_BLUE, blueState ? HIGH : LOW);
    }
  } else {
    digitalWrite(PIN_LED_BLUE, LOW);
    blueState = false;
  }
}

/**
 * Alimenta el watchdog timer para evitar el reinicio.
 * Se llama en cada iteración del loop y durante operaciones largas.
 */
void feedWatchdog() {
  esp_task_wdt_reset();
}
