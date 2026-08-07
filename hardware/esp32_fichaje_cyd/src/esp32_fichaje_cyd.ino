/*
 * TalentUP Fichaje - Firmware ESP32 para CYD 2432S028
 * ===================================================
 *
 * Lector NFC con pantalla TFT ILI9341 240x320 (TFT_eSPI).
 * Lee tarjetas NFC con PN532 via I2C (SDA=IO22, SCL=IO27).
 * Envia el UID al backend TalentUP Fichaje via HTTP POST.
 * Cola offline en SPIFFS cuando no hay WiFi. OTA. Watchdog.
 *
 * Hardware:
 *   CYD 2432S028 (ESP32-WROOM-32 + TFT ILI9341 + Touch XPT2046)
 *   PN532 conectado por I2C:
 *     SDA -> IO22 (CN1)
 *     SCL -> IO27 (CN1, requiere cable PicoBlade extra)
 *     VCC -> 3.3V, GND -> GND
 *   Switches PN532 en modo I2C: SW1=ON, SW2=OFF
 *
 * Configuracion via build_flags en platformio.ini:
 *   WIFI_SSID, WIFI_PASS, BACKEND_URL, TENANT_ID
 *
 * Librerias:
 *   - TFT_eSPI (display ILI9341)
 *   - Adafruit PN532 (I2C)
 *   - ArduinoJson 6.x
 *   - WiFi, HTTPClient, WiFiClientSecure (built-in)
 *   - ArduinoOTA, Update (built-in)
 *   - SPIFFS, FS (built-in)
 *   - esp_task_wdt (built-in)
 */

// ===================== CONFIG (build_flags override) =====================
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
#define TENANT_ID       "default"
#endif

// ===================== PINES =====================
// PN532 I2C en CYD: SDA=IO22, SCL=IO27 (CN1 connector)
#define PN532_I2C_SDA   22
#define PN532_I2C_SCL   27
#define PN532_IRQ       255   // No usamos IRQ, polling
#define PN532_RESET     255   // No usamos reset fisico

// TFT backlight
#define TFT_BL_PIN      21

// ===================== TEMPORIZACION =====================
#define DEBOUNCE_MS       3000    // Anti-lectura duplicada
#define NFC_POLL_MS       100     // Timeout lectura NFC
#define WIFI_RECHECK_MS   10000   // Revisar WiFi cada 10s
#define CLOCK_UPDATE_MS   1000    // Reloj cada 1s
#define QUEUE_FLUSH_MS    15000   // Intentar vaciar cola cada 15s
#define FEEDBACK_MS       3000    // Mostrar feedback 3s
#define WDT_TIMEOUT_S     30      // Watchdog 30s
#define HTTP_TIMEOUT_MS   5000    // Timeout HTTP

// ===================== COLA OFFLINE =====================
#define QUEUE_FILE        "/fichajes_queue.json"
#define QUEUE_MAX_ENTRIES 50      // Max entradas en cola

// ===================== UI COLORES (Apple HIG light, RGB565) =====================
#define COLOR_BG          TFT_WHITE     // 0xFFFF
#define COLOR_TITLE_BG    0xEF7D       // Gris muy claro (0xF7F7F7 -> RGB565)
#define COLOR_TEXT        0x18E3       // Casi negro (0x1D1D1F -> RGB565)
#define COLOR_SECONDARY   0x8410       // Gris medio (0x86868B -> RGB565)
#define COLOR_ACCENT      0x03FF       // Azul Apple (0x007AFF -> RGB565)
#define COLOR_OK          0x1B6D       // Verde Apple (0x34C759 -> RGB565)
#define COLOR_ERROR       0xF9E6       // Rojo Apple (0xFF3B30 -> RGB565)
#define COLOR_STATUS_BAR  0x73AE       // Gris claro (0xE5E5EA -> RGB565)

// ===================== INCLUDES =====================
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_PN532.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <FS.h>
#include <SPIFFS.h>
using namespace fs;
#include <ArduinoOTA.h>
#include <time.h>
#include <esp_task_wdt.h>

// ===================== OBJETOS GLOBALES =====================
TFT_eSPI tft = TFT_eSPI();

// PN532 por I2C: constructor (irq, reset, &Wire)
// Usamos IRQ=255 (no conectado), reset=255 (no conectado)
Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET, &Wire);

// ===================== ESTADO =====================
String lastUID = "";
unsigned long lastReadTime = 0;
bool pn532Ok = false;
bool wifiConnected = false;
int queueCount = 0;

unsigned long lastClockDraw = 0;
unsigned long lastWifiCheck = 0;
unsigned long lastQueueFlush = 0;
unsigned long feedbackUntil = 0;

// Estado UI
enum UiState { UI_IDLE, UI_FEEDBACK };
UiState uiState = UI_IDLE;

// Datos de feedback
String fbName = "";
String fbStatus = "";   // "in", "out", o texto de error
bool fbIsError = false;

// ===================== PROTOTIPOS =====================
void initTFT();
void initNFC();
void initSPIFFS();
void initOTA();
void initWatchdog();
void connectWiFi();
void reconnectWiFi();
void drawUI();
void drawClock();
void drawStatusBar();
void drawIdlePrompt();
void drawFeedback();
void drawBootScreen(const char *msg);
void showSuccess(const String &name, const String &status);
void showError(const String &msg);
void clearFeedback();
void processNFCTag();
void sendToBackend(const String &uid);
int  getQueueCount();
bool enqueueFichaje(const String &uid);
bool flushQueue();
bool sendOneFromQueue(int index, JsonArray &arr);
String formatUID(uint8_t *uid, uint8_t len);
void feedWdt();

// ========================================================
//  SETUP
// ========================================================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  TalentUP Fichaje - CYD 2432S028"));
  Serial.println(F("  ESP32 + TFT ILI9341 + PN532 I2C"));
  Serial.println(F("========================================"));

  // --- Watchdog (primero, antes de cualquier cosa larga) ---
  initWatchdog();
  feedWdt();

  // --- Backlight TFT ---
  pinMode(TFT_BL_PIN, OUTPUT);
  digitalWrite(TFT_BL_PIN, HIGH);
  feedWdt();

  // --- TFT ---
  initTFT();
  drawBootScreen("Iniciando...");
  feedWdt();

  // --- I2C para PN532: SDA=IO22, SCL=IO27 ---
  drawBootScreen("I2C init IO22/IO27");
  Wire.begin(PN532_I2C_SDA, PN532_I2C_SCL);
  feedWdt();

  // --- SPIFFS (cola offline) ---
  initSPIFFS();
  feedWdt();

  // --- PN532 ---
  initNFC();
  feedWdt();

  // --- WiFi ---
  drawBootScreen("Conectando WiFi...");
  connectWiFi();
  feedWdt();

  // --- OTA ---
  initOTA();
  feedWdt();

  // --- Dibujar UI inicial ---
  drawUI();
  drawClock();

  Serial.println(F("Setup completo. Listo."));
}

// ========================================================
//  LOOP
// ========================================================
void loop() {
  feedWdt();

  // --- OTA: procesar updates en background ---
  ArduinoOTA.handle();

  unsigned long now = millis();

  // --- Revisar / reconectar WiFi periodicamente ---
  if (now - lastWifiCheck > WIFI_RECHECK_MS) {
    lastWifiCheck = now;
    if (WiFi.status() != WL_CONNECTED) {
      wifiConnected = false;
      reconnectWiFi();
    } else {
      wifiConnected = true;
    }
    drawStatusBar();
  }

  // --- Intentar vaciar cola offline si hay WiFi ---
  if (wifiConnected && queueCount > 0 && (now - lastQueueFlush > QUEUE_FLUSH_MS)) {
    lastQueueFlush = now;
    Serial.println(F("[QUEUE] Intentando vaciar cola offline..."));
    flushQueue();
    drawStatusBar();
  }

  // --- Actualizar reloj en pantalla ---
  if (uiState == UI_IDLE && (now - lastClockDraw > CLOCK_UPDATE_MS)) {
    lastClockDraw = now;
    drawClock();
    drawIdlePrompt();
  }

  // --- Quitar feedback despues de FEEDBACK_MS ---
  if (uiState == UI_FEEDBACK && now > feedbackUntil) {
    clearFeedback();
    uiState = UI_IDLE;
    lastClockDraw = 0; // forzar redraw clock
  }

  // --- Leer tarjeta NFC ---
  if (pn532Ok) {
    processNFCTag();
  }

  // Pequeno yield para no saturar
  delay(20);
}

// ========================================================
//  INICIALIZACION
// ========================================================

void initTFT() {
  tft.init();
  tft.setRotation(1);  // Landscape 320x240
  tft.fillScreen(COLOR_BG);
  tft.setTextDatum(TL_DATUM);
  Serial.println(F("[TFT] ILI9341 inicializado (rotation 1, 320x240)"));
}

void initNFC() {
  drawBootScreen("Buscando PN532...");
  Serial.println(F("[NFC] Iniciando PN532 por I2C..."));
  Serial.print(F("[NFC] SDA=IO"));
  Serial.print(PN532_I2C_SDA);
  Serial.print(F(" SCL=IO"));
  Serial.println(PN532_I2C_SCL);

  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println(F("[NFC] ERROR: No se detecta PN532 por I2C."));
    Serial.println(F("[NFC] Revisa conexiones SDA->IO22, SCL->IO27."));
    Serial.println(F("[NFC] Switches PN532: SW1=ON, SW2=OFF (modo I2C)."));
    pn532Ok = false;
    drawBootScreen("PN532 no detectado");
    delay(2000);
    return;
  }

  pn532Ok = true;
  Serial.print(F("[NFC] PN532 OK - Chip: 0x"));
  Serial.print((versiondata >> 24) & 0xFF, HEX);
  Serial.print(F(" V"));
  Serial.println((versiondata >> 8) & 0xFF, DEC);

  nfc.SAMConfig();
  Serial.println(F("[NFC] SAMConfig OK. Esperando tarjeta..."));
}

void initSPIFFS() {
  drawBootScreen("SPIFFS init...");
  if (!SPIFFS.begin(true)) {
    Serial.println(F("[SPIFFS] ERROR: No se pudo montar."));
  } else {
    Serial.println(F("[SPIFFS] Montado OK."));
    queueCount = getQueueCount();
    Serial.print(F("[QUEUE] Entradas pendientes: "));
    Serial.println(queueCount);
  }
}

void initOTA() {
  drawBootScreen("OTA init...");
  ArduinoOTA.setHostname("talentup-fichaje-cyd");
  ArduinoOTA.setPassword("talentup2024");

  ArduinoOTA.onStart([]() {
    Serial.println(F("[OTA] Iniciando update..."));
    tft.fillScreen(COLOR_BG);
    tft.setTextColor(COLOR_ACCENT, COLOR_BG);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("Actualizando...", 160, 100, 4);
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    feedWdt();
    int pct = (progress * 100) / total;
    tft.fillRect(60, 140, 200, 20, COLOR_BG);
    tft.setTextColor(COLOR_TEXT, COLOR_BG);
    tft.setTextDatum(MC_DATUM);
    char buf[16];
    sprintf(buf, "%d%%", pct);
    tft.drawString(buf, 160, 150, 4);
  });

  ArduinoOTA.onEnd([]() {
    tft.fillScreen(COLOR_BG);
    tft.setTextColor(COLOR_OK, COLOR_BG);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("OK - Reiniciando", 160, 120, 4);
    Serial.println(F("[OTA] Completado."));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.print(F("[OTA] ERROR: "));
    Serial.println((int)error);
  });

  ArduinoOTA.begin();
  Serial.println(F("[OTA] Listo. Hostname: talentup-fichaje-cyd"));
}

void initWatchdog() {
  // ESP32 Arduino 2.0.x API: esp_task_wdt_init(timeout, panic)
  // (esp_task_wdt_config_t no existe en esta version del framework)
  esp_task_wdt_init(WDT_TIMEOUT_S, true);
  esp_task_wdt_add(NULL);
  Serial.println(F("[WDT] Watchdog iniciado (30s)."));
}

void feedWdt() {
  esp_task_wdt_reset();
}

// ========================================================
//  WIFI
// ========================================================

void connectWiFi() {
  Serial.print(F("[WiFi] Conectando a: "));
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.setHostname("talentup-fichaje-cyd");
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
    feedWdt();
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.print(F("[WiFi] Conectado. IP: "));
    Serial.println(WiFi.localIP());
    // Configurar NTP para hora real
    configTzTime("CET-1CEST,M3.5.0,M10.5.0", "pool.ntp.org", "time.nist.gov");
  } else {
    wifiConnected = false;
    Serial.println();
    Serial.println(F("[WiFi] No conectado. Modo offline (cola activa)."));
  }
}

void reconnectWiFi() {
  Serial.println(F("[WiFi] Reconectando..."));
  WiFi.disconnect();
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 10) {
    delay(500);
    attempts++;
    feedWdt();
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.print(F("[WiFi] Reconectado. IP: "));
    Serial.println(WiFi.localIP());
    configTzTime("CET-1CEST,M3.5.0,M10.5.0", "pool.ntp.org", "time.nist.gov");
  } else {
    wifiConnected = false;
    Serial.println(F("[WiFi] Sigue desconectado."));
  }
}

// ========================================================
//  NFC
// ========================================================

void processNFCTag() {
  uint8_t uid[7];
  uint8_t uidLength;

  boolean success = nfc.readPassiveTargetID(
    PN532_MIFARE_ISO14443A, uid, &uidLength, NFC_POLL_MS
  );

  if (!success) return;

  // Debounce
  unsigned long now = millis();
  if (now - lastReadTime < DEBOUNCE_MS) return;
  lastReadTime = now;

  // Formatear UID
  String uidStr = formatUID(uid, uidLength);

  // Evitar lectura duplicada consecutiva
  if (uidStr == lastUID) return;
  lastUID = uidStr;

  Serial.println(F("----------------------------------------"));
  Serial.print(F("[NFC] Tarjeta: UID="));
  Serial.println(uidStr);
  Serial.println(F("----------------------------------------"));

  // Enviar al backend
  sendToBackend(uidStr);
}

String formatUID(uint8_t *uid, uint8_t len) {
  String s = "";
  for (uint8_t i = 0; i < len; i++) {
    if (uid[i] < 0x10) s += "0";
    s += String(uid[i], HEX);
  }
  s.toUpperCase();
  return s;
}

// ========================================================
//  BACKEND
// ========================================================

void sendToBackend(const String &uid) {
  feedWdt();

  if (!wifiConnected) {
    Serial.println(F("[HTTP] Sin WiFi. Encolando fichaje..."));
    if (enqueueFichaje(uid)) {
      showSuccess("Offline", "queued");
    } else {
      showError("Cola llena");
    }
    return;
  }

  HTTPClient http;
  WiFiClient client;
  String url = String(BACKEND_URL) + "/api/clock/nfc";

  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(HTTP_TIMEOUT_MS);

  // Body JSON
  StaticJsonDocument<256> doc;
  doc["nfc_uid"] = uid;
  doc["tenant_id"] = TENANT_ID;

  String jsonBody;
  serializeJson(doc, jsonBody);

  Serial.print(F("[HTTP] POST "));
  Serial.println(url);
  Serial.print(F("[HTTP] Body: "));
  Serial.println(jsonBody);

  int httpCode = http.POST(jsonBody);

  if (httpCode > 0) {
    String response = http.getString();
    response.trim();
    Serial.print(F("[HTTP] Response "));
    Serial.print(httpCode);
    Serial.print(F(": "));
    Serial.println(response);

    if (httpCode == 200 || httpCode == 201) {
      // Parsear respuesta
      StaticJsonDocument<512> respDoc;
      DeserializationError err = deserializeJson(respDoc, response);

      if (!err) {
        const char *status  = respDoc["status"] | "";
        const char *name    = respDoc["employee_name"] | "";
        const char *time    = respDoc["time"] | "";

        if (strlen(status) > 0 && (strcmp(status, "in") == 0 || strcmp(status, "out") == 0)) {
          String displayName = strlen(name) > 0 ? String(name) : "Empleado";
          showSuccess(displayName, String(status));
        } else {
          showError("Respuesta invalida");
        }
      } else {
        // No es JSON, pero HTTP OK
        showError("No JSON");
      }
    } else {
      // Error HTTP 4xx/5xx
      StaticJsonDocument<256> errDoc;
      DeserializationError err2 = deserializeJson(errDoc, response);
      String errMsg;
      if (!err2 && errDoc["message"].is<const char*>()) {
        errMsg = errDoc["message"].as<const char*>();
      } else if (!err2 && errDoc["detail"].is<const char*>()) {
        errMsg = errDoc["detail"].as<const char*>();
      } else {
        char codeBuf[8];
        sprintf(codeBuf, "HTTP %d", httpCode);
        errMsg = String(codeBuf);
      }
      showError(errMsg);
    }
  } else {
    // Error de conexion - encolar
    Serial.print(F("[HTTP] Error conexion. Encolando... ("));
    Serial.print(httpCode);
    Serial.println(F(")"));
    if (enqueueFichaje(uid)) {
      showSuccess("Offline", "queued");
    } else {
      showError("Sin conexion");
    }
  }

  http.end();
  feedWdt();
}

// ========================================================
//  COLA OFFLINE (SPIFFS)
// ========================================================

int getQueueCount() {
  if (!SPIFFS.exists(QUEUE_FILE)) return 0;

  File f = SPIFFS.open(QUEUE_FILE, "r");
  if (!f) return 0;

  StaticJsonDocument<4096> doc;
  DeserializationError err = deserializeJson(doc, f);
  f.close();

  if (err) {
    Serial.println(F("[QUEUE] Error leyendo cola. Reset."));
    SPIFFS.remove(QUEUE_FILE);
    return 0;
  }

  JsonArray arr = doc["queue"].as<JsonArray>();
  return arr.isNull() ? 0 : arr.size();
}

bool enqueueFichaje(const String &uid) {
  // Leer cola existente
  StaticJsonDocument<4096> doc;
  JsonArray arr;

  if (SPIFFS.exists(QUEUE_FILE)) {
    File fr = SPIFFS.open(QUEUE_FILE, "r");
    if (fr) {
      DeserializationError err = deserializeJson(doc, fr);
      fr.close();
      if (err) {
        doc.clear();
      }
    }
  }

  arr = doc["queue"].to<JsonArray>();
  if (arr.size() >= QUEUE_MAX_ENTRIES) {
    Serial.println(F("[QUEUE] Cola llena. Descartando."));
    return false;
  }

  // Crear entrada
  JsonObject entry = arr.createNestedObject();
  entry["nfc_uid"] = uid;
  entry["tenant_id"] = TENANT_ID;
  entry["ts"] = (uint32_t)time(nullptr);

  // Escribir
  File fw = SPIFFS.open(QUEUE_FILE, "w");
  if (!fw) {
    Serial.println(F("[QUEUE] Error escribiendo."));
    return false;
  }

  serializeJson(doc, fw);
  fw.close();

  queueCount = arr.size();
  Serial.print(F("[QUEUE] Encolado. Total: "));
  Serial.println(queueCount);
  return true;
}

bool flushQueue() {
  if (!SPIFFS.exists(QUEUE_FILE)) {
    queueCount = 0;
    return true;
  }

  File fr = SPIFFS.open(QUEUE_FILE, "r");
  if (!fr) return false;

  StaticJsonDocument<4096> doc;
  DeserializationError err = deserializeJson(doc, fr);
  fr.close();

  if (err) {
    Serial.println(F("[QUEUE] Error deserializando. Borrando."));
    SPIFFS.remove(QUEUE_FILE);
    queueCount = 0;
    return false;
  }

  JsonArray arr = doc["queue"].as<JsonArray>();
  if (arr.isNull() || arr.size() == 0) {
    queueCount = 0;
    SPIFFS.remove(QUEUE_FILE);
    return true;
  }

  // Intentar enviar cada entrada; si falla alguna, paramos
  bool allSent = true;
  for (int i = 0; i < arr.size(); i++) {
    feedWdt();

    JsonObject entry = arr[i];
    const char *uid = entry["nfc_uid"] | "";
    const char *tid = entry["tenant_id"] | TENANT_ID;

    if (strlen(uid) == 0) continue;

    HTTPClient http;
    WiFiClient client;
    String url = String(BACKEND_URL) + "/api/clock/nfc";

    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    StaticJsonDocument<256> reqDoc;
    reqDoc["nfc_uid"] = uid;
    reqDoc["tenant_id"] = tid;

    String body;
    serializeJson(reqDoc, body);

    Serial.print(F("[QUEUE] Enviando pendiente UID="));
    Serial.println(uid);

    int code = http.POST(body);
    http.end();

    if (code == 200 || code == 201) {
      Serial.println(F("[QUEUE] OK, enviada."));
    } else {
      Serial.print(F("[QUEUE] Fallo (HTTP "));
      Serial.print(code);
      Serial.println(F("). Parando flush."));
      allSent = false;
      break;
    }

    delay(100); // No saturar backend
  }

  if (allSent) {
    SPIFFS.remove(QUEUE_FILE);
    queueCount = 0;
    Serial.println(F("[QUEUE] Cola vaciada completamente."));
  } else {
    // Reescribir cola con las entradas que faltan
    // (no implementamos compactacion parcial aqui: se reintentara)
    // Simplificacion: mantener archivo tal cual
    queueCount = arr.size();
    Serial.print(F("[QUEUE] Quedan "));
    Serial.print(queueCount);
    Serial.println(F(" pendientes."));
  }

  return allSent;
}

// ========================================================
//  UI / DISPLAY
// ========================================================

void drawBootScreen(const char *msg) {
  tft.fillScreen(COLOR_BG);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.drawString("TalentUP Fichaje", 160, 90, 4);
  tft.setTextColor(COLOR_SECONDARY, COLOR_BG);
  tft.drawString(msg, 160, 140, 2);
  tft.setTextDatum(TL_DATUM);
}

void drawUI() {
  tft.fillScreen(COLOR_BG);

  // --- Top bar ---
  tft.fillRect(0, 0, 320, 40, COLOR_TITLE_BG);
  tft.drawFastHLine(0, 40, 320, COLOR_STATUS_BAR);
  tft.setTextColor(COLOR_TEXT, COLOR_TITLE_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString("TalentUP Fichaje", 160, 10, 2);
  tft.setTextDatum(TL_DATUM);

  // --- Status bar (debajo del top bar) ---
  drawStatusBar();

  // --- Clock area (centro) ---
  drawClock();

  // --- Bottom prompt ---
  drawIdlePrompt();

  uiState = UI_IDLE;
}

void drawClock() {
  // Area del reloj: y=70 a y=170, centro x=160
  tft.fillRect(10, 70, 300, 100, COLOR_BG);

  time_t now = time(nullptr);
  struct tm *tinfo = localtime(&now);
  char timeStr[12];
  sprintf(timeStr, "%02d:%02d:%02d", tinfo->tm_hour, tinfo->tm_min, tinfo->tm_sec);

  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString(timeStr, 160, 100, 4);  // Font 4 = grande
  tft.setTextDatum(TL_DATUM);

  // Fecha pequeña debajo
  char dateStr[24];
  sprintf(dateStr, "%02d/%02d/%04d", tinfo->tm_mday, tinfo->tm_min == 0 ? tinfo->tm_min : tinfo->tm_mon + 1, tinfo->tm_year + 1900);
  sprintf(dateStr, "%02d/%02d/%04d", tinfo->tm_mday, tinfo->tm_mon + 1, tinfo->tm_year + 1900);
  tft.setTextColor(COLOR_SECONDARY, COLOR_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString(dateStr, 160, 150, 2);
  tft.setTextDatum(TL_DATUM);
}

void drawStatusBar() {
  // Barra y=42 a y=62
  tft.fillRect(0, 42, 320, 20, COLOR_BG);

  // WiFi status
  String wifiStr;
  if (wifiConnected) {
    wifiStr = "WiFi: OK";
    tft.setTextColor(COLOR_OK, COLOR_BG);
  } else {
    wifiStr = "WiFi: OFF";
    tft.setTextColor(COLOR_ERROR, COLOR_BG);
  }
  tft.setTextDatum(TL_DATUM);
  tft.drawString(wifiStr, 10, 45, 2);

  // NFC status
  String nfcStr = pn532Ok ? "NFC: OK" : "NFC: OFF";
  tft.setTextColor(pn532Ok ? COLOR_OK : COLOR_ERROR, COLOR_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString(nfcStr, 160, 45, 2);

  // Queue status
  if (queueCount > 0) {
    char qBuf[16];
    sprintf(qBuf, "Cola: %d", queueCount);
    tft.setTextColor(COLOR_ACCENT, COLOR_BG);
    tft.setTextDatum(TR_DATUM);
    tft.drawString(qBuf, 310, 45, 2);
  }

  tft.setTextDatum(TL_DATUM);
}

void drawIdlePrompt() {
  // Bottom area: y=180 a y=240
  tft.fillRect(0, 180, 320, 60, COLOR_BG);

  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString("Acerca tu tarjeta", 160, 195, 2);

  tft.setTextColor(COLOR_SECONDARY, COLOR_BG);
  tft.drawString("para fichar", 160, 215, 2);

  tft.setTextDatum(TL_DATUM);
}

void showSuccess(const String &name, const String &status) {
  fbName = name;
  fbStatus = status;
  fbIsError = false;
  uiState = UI_FEEDBACK;
  feedbackUntil = millis() + FEEDBACK_MS;
  drawFeedback();
}

void showError(const String &msg) {
  fbName = "";
  fbStatus = msg;
  fbIsError = true;
  uiState = UI_FEEDBACK;
  feedbackUntil = millis() + FEEDBACK_MS;
  drawFeedback();
}

void drawFeedback() {
  // Limpiar area central + inferior
  tft.fillRect(0, 65, 320, 175, COLOR_BG);

  uint16_t circleColor = fbIsError ? COLOR_ERROR : COLOR_OK;

  // Circulo grande en centro
  int cx = 160, cy = 130, r = 35;
  tft.fillCircle(cx, cy, r, circleColor);

  // Simbolo dentro del circulo
  if (fbIsError) {
    // X blanca
    tft.setTextColor(TFT_WHITE, circleColor);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("X", cx, cy, 4);
  } else {
    // Checkmark (V) blanca
    tft.setTextColor(TFT_WHITE, circleColor);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("OK", cx, cy, 4);
  }

  // Texto debajo del circulo
  if (fbIsError) {
    tft.setTextColor(COLOR_ERROR, COLOR_BG);
    tft.setTextDatum(TC_DATUM);
    // Truncar si muy largo
    String msg = fbStatus;
    if (msg.length() > 20) msg = msg.substring(0, 20);
    tft.drawString(msg, 160, 185, 2);
  } else {
    // Nombre del empleado
    tft.setTextColor(COLOR_TEXT, COLOR_BG);
    tft.setTextDatum(TC_DATUM);
    String name = fbName;
    if (name.length() > 18) name = name.substring(0, 18);
    tft.drawString(name, 160, 180, 2);

    // IN / OUT
    String statusText;
    if (fbStatus == "in") statusText = "ENTRADA";
    else if (fbStatus == "out") statusText = "SALIDA";
    else if (fbStatus == "queued") statusText = "ENCOLADO";
    else statusText = fbStatus;

    uint16_t statusColor = (fbStatus == "in") ? COLOR_OK : (fbStatus == "out") ? COLOR_ACCENT : COLOR_SECONDARY;
    tft.setTextColor(statusColor, COLOR_BG);
    tft.drawString(statusText, 160, 205, 2);
  }

  tft.setTextDatum(TL_DATUM);
}

void clearFeedback() {
  // Redibujar UI completa (top bar + status + clock + prompt)
  drawUI();
}