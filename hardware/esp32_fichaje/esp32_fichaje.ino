/*
 * TalentUP Fichaje - Firmware ESP32 para lector NFC
 * =================================================
 *
 * Lee tarjetas NFC con PN532 via SPI y envía el UID al backend
 * TalentUP Fichaje para registrar entrada/salida.
 * Incluye cola offline con LittleFS + journaling para operación sin conexión
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
 *   - WiFiClientSecure (built-in ESP32)
 *   - HTTPClient (built-in ESP32)
 *   - ArduinoJson       ^6.x
 *   - Adafruit PN532    ^1.3
 *   - Adafruit BusIO     (dependencia PN532)
 *   - SPI (built-in ESP32)
 *   - LittleFS (built-in ESP32)
 */

// ===================== CONFIGURACIÓN =====================
#ifndef WIFI_SSID
#define WIFI_SSID       "TU_WIFI_SSID"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS       "TU_WIFI_PASSWORD"
#endif
#ifndef BACKEND_URL
#define BACKEND_URL     "https://192.168.1.100:8000"
#endif
#ifndef TENANT_ID
#define TENANT_ID       "CAMBIAR-POR-TU-TENANT-ID-UUID"
#endif
#ifndef DEVICE_TOKEN
#define DEVICE_TOKEN    "CAMBIAR-POR-TU-DEVICE-TOKEN"
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
#define MAX_QUEUE_SIZE  100      // Máximo fichajes en cola offline

// ==========================================================

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_PN532.h>
#include <LittleFS.h>
#include <esp_task_wdt.h>

// Instancia PN532 por SPI
Adafruit_PN532 nfc(PIN_PN532_SS);

// Cliente TLS para HTTPS (global para reutilizar)
WiFiClientSecure tlsClient;

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
void initLittleFS();
bool saveToQueue(const String &uid);
int loadPendingCount();
void syncQueue();
void updateBlueLED();
void feedWatchdog();

// ===================== SETUP ==========================
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  TalentUP Fichaje - ESP32 NFC Reader"));
  Serial.println(F("  Con cola offline LittleFS + journaling + WDT"));
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

  // --- LittleFS ---
  initLittleFS();

  // --- WiFi ---
  connectWiFi();

  // --- TLS ---
  tlsClient.setInsecure();  // Para desarrollo: acepta cualquier certificado
  Serial.println(F("[INFO] TLS modo desarrollo (setInsecure)."));

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
  pendingCount = loadPendingCount();
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

// ============== FUNCIONES COLA OFFLINE (LittleFS + journaling) ==============

#define QUEUE_DIR       "/queue"
#define QUEUE_INDEX     "/queue/index.json"
#define QUEUE_FILE_FMT  "/queue/%03d.json"
#define QUEUE_MAX_DIGITS 3

/**
 * Inicializa LittleFS. Si falla, formatea automáticamente.
 * Crea el directorio /queue si no existe.
 */
void initLittleFS() {
  if (!LittleFS.begin(true)) {
    Serial.println(F("[ERROR] LittleFS mount failed. Formateando..."));
    if (!LittleFS.format()) {
      Serial.println(F("[FATAL] LittleFS format failed."));
      fatalError();
    }
    if (!LittleFS.begin(true)) {
      Serial.println(F("[FATAL] LittleFS remount failed after format."));
      fatalError();
    }
  }

  if (!LittleFS.exists(QUEUE_DIR)) {
    if (!LittleFS.mkdir(QUEUE_DIR)) {
      Serial.println(F("[FATAL] No se pudo crear /queue."));
      fatalError();
    }
  }

  Serial.println(F("[OK] LittleFS montado correctamente (journaling /queue)."));
}

/**
 * Lee el contador actual desde /queue/index.json.
 * Si el archivo no existe o está corrupto, calcula el siguiente
 * número seguro a partir de los archivos existentes.
 */
static int readIndexCounter() {
  if (!LittleFS.exists(QUEUE_INDEX)) {
    return 0;
  }

  File file = LittleFS.open(QUEUE_INDEX, "r");
  if (!file) {
    return 0;
  }

  String content = file.readString();
  file.close();

  StaticJsonDocument<128> doc;
  DeserializationError err = deserializeJson(doc, content);
  if (err || !doc["counter"].is<int>()) {
    Serial.println(F("[WARN] index.json corrupto, recalculando contador."));
    return 0;
  }

  return doc["counter"].as<int>();
}

/**
 * Escribe el contador en /queue/index.json.
 */
static bool writeIndexCounter(int counter) {
  File file = LittleFS.open(QUEUE_INDEX, "w");
  if (!file) {
    Serial.println(F("[ERROR] No se pudo abrir index.json para escritura."));
    return false;
  }

  StaticJsonDocument<128> doc;
  doc["counter"] = counter;
  serializeJson(doc, file);
  file.close();
  return true;
}

/**
 * Lista los archivos de fichaje en /queue y los ordena por número.
 * 'numbers' debe tener capacidad MAX_QUEUE_SIZE.
 * Devuelve la cantidad de archivos encontrados.
 */
static int listQueueFiles(int *numbers, int maxCount) {
  File dir = LittleFS.open(QUEUE_DIR);
  if (!dir || !dir.isDirectory()) {
    return 0;
  }

  int count = 0;
  File file = dir.openNextFile();
  while (file && count < maxCount) {
    String name = String(file.name());
    file.close();

    // Solo archivos 001.json, 002.json, ...
    if (name.endsWith(".json") && name != "index.json") {
      String numPart = name.substring(0, name.length() - 5);
      int n = numPart.toInt();
      if (n > 0) {
        numbers[count++] = n;
      }
    }
    file = dir.openNextFile();
  }

  // Ordenar ascendente (burbuja simple, max 100 elementos)
  for (int i = 0; i < count - 1; i++) {
    for (int j = i + 1; j < count; j++) {
      if (numbers[j] < numbers[i]) {
        int tmp = numbers[i];
        numbers[i] = numbers[j];
        numbers[j] = tmp;
      }
    }
  }

  return count;
}

/**
 * Cuenta cuántos fichajes hay pendientes en /queue.
 */
int loadPendingCount() {
  int numbers[MAX_QUEUE_SIZE];
  return listQueueFiles(numbers, MAX_QUEUE_SIZE);
}

/**
 * Guarda un fichaje en la cola offline como archivo individual:
 *   /queue/001.json, /queue/002.json, ...
 * Mantiene /queue/index.json con el contador secuencial.
 * Si se supera MAX_QUEUE_SIZE, descarta el fichaje más antiguo (FIFO).
 */
bool saveToQueue(const String &uid) {
  // Asegurar que existe /queue
  if (!LittleFS.exists(QUEUE_DIR)) {
    LittleFS.mkdir(QUEUE_DIR);
  }

  int numbers[MAX_QUEUE_SIZE];
  int count = listQueueFiles(numbers, MAX_QUEUE_SIZE);

  // FIFO: si la cola está llena, borrar el fichaje más antiguo
  if (count >= MAX_QUEUE_SIZE) {
    Serial.println(F("[WARN] Cola offline llena. Descartando fichaje más antiguo..."));
    char oldest[32];
    snprintf(oldest, sizeof(oldest), QUEUE_FILE_FMT, numbers[0]);
    LittleFS.remove(oldest);
    count--;
  }

  // Determinar siguiente número (a partir de index.json)
  int counter = readIndexCounter();
  int next = counter + 1;

  // Evitar colisión con archivos existentes por si index.json se desfasó
  for (int i = 0; i < count; i++) {
    if (numbers[i] >= next) {
      next = numbers[i] + 1;
    }
  }

  // Guardar fichaje individual
  char path[32];
  snprintf(path, sizeof(path), QUEUE_FILE_FMT, next);

  File file = LittleFS.open(path, "w");
  if (!file) {
    Serial.print(F("[ERROR] No se pudo crear "));
    Serial.println(path);
    return false;
  }

  StaticJsonDocument<256> doc;
  doc["uid"] = uid;
  doc["timestamp"] = millis() / 1000;  // Tiempo desde arranque (relativo)
  doc["synced"] = false;

  if (serializeJson(doc, file) == 0) {
    file.close();
    Serial.print(F("[ERROR] Fallo escribiendo "));
    Serial.println(path);
    return false;
  }
  file.close();

  // Actualizar contador en index.json
  if (!writeIndexCounter(next)) {
    Serial.println(F("[WARN] Fichaje guardado pero no se pudo actualizar index.json."));
    // Continuamos: el próximo arranque recalculará a partir de archivos.
  }

  pendingCount = loadPendingCount();
  return true;
}

/**
 * Intenta sincronizar todos los fichajes pendientes con el backend.
 * Lee cada archivo /queue/NNN.json, lo envía y, si OK, lo borra.
 * Si un archivo está corrupto, se ignora y se borra para no bloquear la cola.
 * Si el envío de un fichaje falla, se detiene para mantener el orden;
 * el archivo permanece en cola para el siguiente intento.
 */
void syncQueue() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  int numbers[MAX_QUEUE_SIZE];
  int count = listQueueFiles(numbers, MAX_QUEUE_SIZE);

  if (count == 0) {
    pendingCount = 0;
    return;
  }

  Serial.print(F("Sincronizando "));
  Serial.print(count);
  Serial.println(F(" fichajes..."));

  for (int i = 0; i < count; i++) {
    char path[32];
    snprintf(path, sizeof(path), QUEUE_FILE_FMT, numbers[i]);

    File file = LittleFS.open(path, "r");
    if (!file) {
      Serial.print(F("[WARN] No se pudo abrir "));
      Serial.println(path);
      continue;
    }

    String content = file.readString();
    file.close();

    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, content);
    if (err) {
      Serial.print(F("[WARN] Archivo corrupto, saltando: "));
      Serial.println(path);
      LittleFS.remove(path);
      feedWatchdog();
      continue;
    }

    const char *uid = doc["uid"] | "";
    if (strlen(uid) == 0) {
      Serial.print(F("[WARN] UID vacío, eliminando "));
      Serial.println(path);
      LittleFS.remove(path);
      feedWatchdog();
      continue;
    }

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
      Serial.print(F("  OK: "));
      Serial.print(uid);
      Serial.print(F(" ("));
      Serial.print(path);
      Serial.println(F(")"));
      LittleFS.remove(path);
    } else {
      Serial.print(F("  FAIL: "));
      Serial.print(uid);
      Serial.print(F(" ("));
      Serial.print(path);
      Serial.print(F(", HTTP "));
      Serial.print(httpCode);
      Serial.println(F(")"));
      // Mantener orden: no procesar el resto hasta la próxima ronda
      break;
    }

    feedWatchdog();
  }

  pendingCount = loadPendingCount();
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
