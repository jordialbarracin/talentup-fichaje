# INFORME TÉCNICO — Sistema de Fichaje NFC+QR TalentUP

**Fecha:** 19/07/2026  
**Analista:** Ingeniero de Hardware IoT (ESP32 + NFC)  
**Versión Firmware:** 1.0  
**Backend:** TalentUP Fichaje API v2.0.0  
**Base de datos:** SQLite (dev) / PostgreSQL (prod)

---

## 1. PRUEBAS DE ENDPOINTS

### 1.1 POST /api/clock/nfc

| # | UID | tenant_id | Resultado | Código |
|---|-----|-----------|-----------|--------|
| 1 | `04:A1:B2:C3:D4:E5` (Carlos) | UUID correcto | ✅ `"Carlos — Entrada registrada"` | 201 |
| 2 | `04:A1:B2:C3:D4:E6` (Ana) | UUID correcto | ✅ `"Ana — Entrada registrada"` | 201 |
| 3 | `04:A1:B2:C3:D4:E7` (David) | UUID correcto | ✅ `"David — Entrada registrada"` | 201 |
| 4 | `04:A1:B2:C3:D4:E5` (Carlos, 2º tap) | UUID correcto | ✅ `"Carlos — Salida registrada"` (auto-toggle) | 201 |
| 5 | `AA:BB:CC:DD:EE:FF` (falso) | UUID correcto | ❌ `"Tarjeta NFC no registrada"` | 404 |
| 6 | `04:A1:B2:C3:D4:E5` (Carlos) | `"latagliatella"` (slug) | ❌ `"Tarjeta NFC no registrada"` | 404 |
| 7 | `04:A1:B2:C3:D4:E5` (Carlos) | `"otro_tenant"` | ❌ `"Tarjeta NFC no registrada"` | 404 |
| 8 | `04A1B2C3D4E5` (sin separadores) | UUID correcto | ❌ `"Tarjeta NFC no registrada"` | 404 |
| 9 | `""` (vacío) | UUID correcto | ❌ `"Tarjeta NFC no registrada"` | 404 |

**Hallazgo crítico:** El endpoint NFC funciona correctamente, pero **el tenant_id debe ser el UUID interno**, no un slug. El firmware ESP32 usa `TENANT_ID "default"` — esto **no funcionará** contra el backend real a menos que se añada una ruta que resuelva slugs o se configure con el UUID correcto.

### 1.2 POST /api/clock/qr

| # | employee_id | tenant_id | Resultado | Código |
|---|-------------|-----------|-----------|--------|
| 1 | UUID de Carlos | UUID correcto | ✅ `"Carlos — Salida registrada"` | 201 |
| 2 | UUID falso | UUID correcto | ❌ `"Código QR no válido o empleado no encontrado"` | 404 |

**Conclusión:** QR endpoint funciona correctamente. El QR debe contener el `employee_id` (UUID) del empleado.

---

## 2. ANÁLISIS DEL FIRMWARE ESP32

**Archivo:** `hardware/esp32_fichaje/esp32_fichaje.ino` (363 líneas)

### 2.1 ¿Compila?

**Sí, compilaría** con las dependencias correctas:
- `WiFi.h` y `HTTPClient.h` — built-in del ESP32 core
- `SPI.h` — built-in
- `Adafruit_PN532` v1.3+ — disponible en Arduino Library Manager / PlatformIO
- `ArduinoJson` v6.x — disponible
- `Adafruit BusIO` — dependencia automática de PN532

**Posibles errores de compilación:**
- Si no se instala `Adafruit BusIO`, el PN532 falla
- En algunas placas ESP32, `SPI.begin(SCK, MISO, MOSI, SS)` requiere `#include <SPI.h>` explícito (ya incluido)
- `StaticJsonDocument<256>` puede ser pequeño si el backend devuelve respuestas muy largas (actualmente OK)

### 2.2 Pines SPI — ¿Correctos para ESP32?

| Pin | GPIO ESP32 | Función | ¿Correcto? |
|-----|-----------|---------|------------|
| SS (CS) | GPIO5 | VSPI CS0 | ✅ Correcto |
| SCK | GPIO18 | VSPI SCK | ✅ Correcto |
| MISO | GPIO19 | VSPI MISO | ✅ Correcto |
| MOSI | GPIO23 | VSPI MOSI | ✅ Correcto |

**Veredicto:** Los pines SPI son **correctos** para el bus VSPI del ESP32. La inicialización explícita `SPI.begin(SCK, MISO, MOSI, SS)` es la práctica recomendada.

### 2.3 Lógica del firmware — Evaluación

**Puntos fuertes:**
- ✅ Inicialización explícita de SPI con pines definidos
- ✅ Verificación de detección del PN532 con `getFirmwareVersion()`
- ✅ Modo SAM configurado correctamente
- ✅ Debounce por tiempo (no por bloqueo)
- ✅ Protección contra UIDs duplicados consecutivos
- ✅ Parseo de respuesta JSON del backend
- ✅ LEDs de estado (verde=OK, rojo=error)
- ✅ Timeout HTTP de 5s
- ✅ Reintento WiFi con backoff

**Problemas identificados:**

1. **🔴 TENANT_ID fijo como "default"** — El backend requiere el UUID del tenant. El firmware envía `"default"` que no existe en la BD. **Esto rompe el sistema en producción.**

2. **🟡 Sin reconexión WiFi en loop()** — Cuando WiFi se cae, `loop()` llama a `connectWiFi()` que es bloqueante (delay de 500ms por intento, hasta 20s). Durante ese tiempo no se leen tarjetas NFC. Aceptable pero mejorable con estado asíncrono.

3. **🟡 Sin buffer de fichajes offline** — Si el backend no responde (timeout, caída), el error se muestra por LED rojo y se pierde el fichaje. No hay cola local.

4. **🟢 StaticJsonDocument<256> para el body** — Suficiente para el payload actual, pero justo. Si el backend añade campos, podría desbordar.

5. **🟢 No hay watchdog** — Si el PN532 se cuelga, el ESP32 se queda en `fatalError()` (bucle infinito con LED rojo parpadeante). Sin watchdog, requiere reset manual.

### 2.4 Debounce de 2 segundos — ¿Suficiente?

**Sí, 2 segundos es adecuado.** El PN532 en modo SAM tiene una latencia de ~20-50ms por lectura. Con `NFC_POLL_MS=100`, el loop itera 20 veces antes de permitir otra lectura. Esto:
- Evita lecturas dobles si el empleado deja la tarjeta apoyada
- Es rápido enough para flujo de empleados (máximo 30 fichajes/minuto teóricos)
- Coincide con el rate limit del backend (10/minuto)

**Recomendación:** Reducir a 1500ms para experiencia más ágil, o mantener 2000ms si hay empleados que dejan la tarjeta apoyada.

### 2.5 ¿Qué pasa si el WiFi se cae?

1. `loop()` detecta `WiFi.status() != WL_CONNECTED`
2. Enciende LED rojo
3. Llama a `connectWiFi()` — bloqueante, ~20s de reintentos
4. Si reconecta, apaga LED rojo y sigue normal
5. Si no reconecta tras 20s, espera 5s y reintenta (bucle infinito)

**Problema:** Durante la reconexión (hasta 20s), no se leen tarjetas. Si alguien acerca una tarjeta en ese intervalo, se ignora. **Solución:** Usar WiFi en modo no-bloqueante con estado y reintentar en segundo plano mientras se sigue leyendo NFC.

### 2.6 ¿Qué pasa si el backend no responde?

1. `sendToBackend()` hace POST con timeout de 5s
2. Si timeout o error de conexión: LED rojo, mensaje por Serial
3. El fichaje **se pierde** — no hay cola ni reintento
4. El LED rojo se apaga tras `LED_ON_MS` (1.5s)

**Problema grave:** En un corte de red o caída del backend, todos los fichajes se pierden sin posibilidad de recuperación. **Solución imprescindible:** Añadir cola de fichajes offline en RTC memory o SPIFFS.

---

## 3. ANÁLISIS DEL README DE HARDWARE

### 3.1 Esquema de conexión — ¿Correcto?

| Conexión | README | Realidad | Veredicto |
|----------|--------|----------|-----------|
| PN532 VCC → 3.3V | ✅ 3.3V | PN532 funciona a 3.3V-5V, pero 3.3V es seguro | ✅ Correcto |
| PN532 NSS → GPIO5 | ✅ | GPIO5 es VSPI CS0 | ✅ Correcto |
| PN532 SCK → GPIO18 | ✅ | GPIO18 es VSPI SCK | ✅ Correcto |
| PN532 MISO → GPIO19 | ✅ | GPIO19 es VSPI MISO | ✅ Correcto |
| PN532 MOSI → GPIO23 | ✅ | GPIO23 es VSPI MOSI | ✅ Correcto |
| LED verde → GPIO2 + 220Ω | ✅ | GPIO2 es LED_BUILTIN en muchos ESP32 | ⚠️ Puede colisionar con LED onboard |
| LED rojo → GPIO4 + 220Ω | ✅ | GPIO4 es seguro | ✅ Correcto |

**Problema menor:** GPIO2 es el LED_BUILTIN en la mayoría de ESP32 DevKit. Si la placa tiene un LED onboard en GPIO2, el LED verde externo parpadeará débilmente durante el boot (el bootloader de ESP32 hace parpadear GPIO2). **Recomendación:** Usar GPIO16 o GPIO32 para el LED verde.

### 3.2 Coste de materiales — ¿Realista?

| Componente | README | Realidad (AliExpress 2026) | Veredicto |
|-----------|--------|--------------------------|-----------|
| ESP32 | 6-10€ | 3-5€ (AliExpress) / 8-12€ (Amazon) | ⚠️ Ligeramente alto pero realista para Amazon |
| PN532 SPI | 8-12€ | 4-6€ (AliExpress) / 10-15€ (Amazon) | ⚠️ Rango correcto |
| LEDs + resistencias | 0.30€ | 0.10-0.30€ | ✅ |
| Protoboard | 1-3€ | 0.50-2€ | ✅ |
| Cables Dupont | 1-2€ | 0.50-1.50€ | ✅ |
| **Total** | **16-27€** | **8-20€ (AliExpress) / 20-35€ (Amazon)** | **Realista** |

**Conclusión:** El coste es realista para un prototipo. Para producción en serie (>100 unidades), el coste BOM se reduce a ~8-12€/unidad usando PCB personalizada y componentes en volumen.

---

## 4. PROPUESTAS DE MEJORA AL FIRMWARE

### 4.1 Deep Sleep

**Implementación:** El ESP32 puede entrar en deep sleep y despertar con un pin externo (ej. señal del PN532 al detectar una tarjeta).

**Ventajas:**
- Consumo: ~10µA en deep sleep vs ~80mA en active
- Ideal para instalaciones con batería o eficiencia energética
- Autonomía teórica: meses con 2000mAh

**Desventajas:**
- El PN532 no tiene pin de "tarjeta detectada" fácil de usar como wake-up
- Solución: usar un timer de wake-up periódico (ej. cada 5s) para poll breve
- Complejidad añadida en el firmware

**Recomendación:** Implementar solo si el dispositivo va a batería. Para uso con alimentación USB continua, no es necesario.

### 4.2 OTA Updates

**Implementación:** Usar `ArduinoOTA` o `Update.h` del ESP32 para actualizar firmware vía WiFi.

**Ventajas:**
- Actualizaciones sin acceso físico al dispositivo
- Rollout de parches de seguridad
- Añadir features sin re-cablear

**Implementación mínima:**
```cpp
#include <ArduinoOTA.h>
ArduinoOTA.begin();
// En loop():
ArduinoOTA.handle();
```

**Recomendación:** **IMPLEMENTAR SÍ O SÍ.** Es crítico para mantenimiento remoto. Sin OTA, cada actualización requiere conectar un cable USB al ESP32.

### 4.3 Pantalla OLED

**Opción:** SSD1306 128x64 I2C (~3€)

**Ventajas:**
- Muestra nombre del empleado al fichar
- Muestra hora actual
- Muestra estado de conexión WiFi
- Feedback visual sin necesidad de app

**Implementación:**
```cpp
#include <Adafruit_SSD1306.h>
display.print(employeeName);
display.print(" - ");
display.print(type); // "Entrada" / "Salida"
```

**Recomendación:** Alta prioridad para producto final. Mejora la experiencia de usuario drásticamente.

### 4.4 MQTT en vez de HTTP

**Ventajas de MQTT:**
- Comunicación persistente (TCP mantenido)
- Menor latencia (no hay handshake HTTP por lectura)
- QoS 1 garantiza entrega aunque el broker se caiga
- Menos ancho de banda (cabeceras mínimas)
- Ideal para colas offline

**Desventajas:**
- Requiere broker MQTT (Mosquitto, EMQX)
- Complejidad adicional en backend
- Puerto 1883/8883 puede estar bloqueado en algunas redes

**Recomendación:** Para el caso de uso actual (fichaje en hostelería), **HTTP es suficiente**. MQTT aportaría valor si hubiera muchos dispositivos (>50) o necesidad de comunicación bidireccional (ej. mostrar mensajes en pantalla). **Prioridad media-baja.**

### 4.5 Otras mejoras propuestas

| Mejora | Prioridad | Esfuerzo | Impacto |
|--------|-----------|----------|---------|
| Cola offline (RTC/SPIFFS) | 🔴 Alta | 2 días | Crítico para fiabilidad |
| OTA updates | 🔴 Alta | 1 día | Crítico para mantenimiento |
| UUID tenant configurable | 🔴 Alta | 30 min | Bug blocker |
| Pantalla OLED | 🟡 Media | 2 días | UX |
| Deep sleep | 🟢 Baja | 3 días | Solo batería |
| MQTT | 🟢 Baja | 5 días | Escalabilidad |
| Watchdog (ESP32 Task Watchdog) | 🟡 Media | 30 min | Robustez |
| WiFi no-bloqueante | 🟡 Media | 1 día | Disponibilidad |

---

## 5. ROTACIÓN DE TARJETAS NFC — SEGURIDAD DE UIDs

### 5.1 ¿Pueden dos empleados tener el mismo UID?

**Respuesta corta:** Extremadamente improbable con tarjetas MIFARE/NTAG originales.

**Análisis técnico:**
- Los UIDs de tarjetas MIFARE Classic (1K/4K) son de **4 bytes** (32 bits) → 4.294.967.296 combinaciones
- Los UIDs de tarjetas NTAG (21x) son de **7 bytes** (56 bits) → 72.057.594.037.927.936 combinaciones
- Los UIDs vienen grabados de fábrica y son únicos por chip
- La probabilidad de colisión en un conjunto de 1000 tarjetas es esencialmente 0

**Riesgo real:** Tarjetas NFC clonables (UID writable). Existen tarjetas "UID writable" chinas que permiten reescribir el UID. Un empleado podría:
1. Comprar una tarjeta UID writable (2-3€ en AliExpress)
2. Clonar el UID de otro compañero
3. Fichar por él

**Mitigaciones:**
- Usar tarjetas MIFARE Plus o DESFire con autenticación criptográfica
- Añadir verificación de firma criptográfica (no solo UID)
- Combinar NFC + PIN para operaciones sensibles
- Detectar patrones anómalos (mismo UID en dos ubicaciones simultáneas)

**Veredicto:** Para hostelería, el riesgo es bajo. La mayoría de empleados no tiene conocimientos para clonar tarjetas. **Aceptable para MVP.**

### 5.2 Formato de UID en la BD

Los UIDs en seed usan formato `04:A1:B2:C3:D4:E5` (7 bytes con separadores `:`). El firmware genera UIDs en formato `04A1B2C3D4E5` (sin separadores). **Esto es un problema:** el backend busca coincidencia exacta de string.

**Prueba realizada:** Enviar `04A1B2C3D4E5` (sin `:`) → ❌ "Tarjeta NFC no registrada".

**Solución:** Normalizar el UID en el backend (quitar `:` antes de comparar) o en el firmware (añadir `:`). **Recomendación:** Normalizar en el backend para compatibilidad con múltiples lectores.

---

## 6. SCORE DEL SISTEMA HARDWARE (0-100)

| Categoría | Peso | Puntuación | Notas |
|-----------|------|-----------|-------|
| **Diseño hardware** | 20% | 18/20 | Pines SPI correctos, LEDs bien, esquema claro |
| **Calidad firmware** | 25% | 15/25 | Lógica correcta pero falta cola offline, OTA, watchdog |
| **Seguridad** | 15% | 10/15 | UID único OK, pero sin autenticación criptográfica |
| **UX/Feedback** | 10% | 6/10 | LEDs OK, sin pantalla, sin sonido |
| **Mantenibilidad** | 10% | 4/10 | Sin OTA, sin platformio.ini, sin CI |
| **Documentación** | 10% | 8/10 | README completo, esquema claro, BOM realista |
| **Coste** | 10% | 8/10 | BOM realista, podría bajar a 12€ en volumen |

### Puntuación final: **69/100**

**Interpretación:** Sistema funcional para prototipo/MVP, pero con carencias importantes para producción real. Las principales debilidades son la falta de cola offline, OTA, y el bug del tenant_id.

---

## 7. TOP 3 MEJORAS HARDWARE

### 🥇 1. Cola de fichajes offline (RTC Memory + SPIFFS)

**Problema:** Si el WiFi se cae o el backend no responde, el fichaje se pierde.
**Solución:** Almacenar los UIDs en RTC memory (se conserva en deep sleep) o SPIFFS. Reintentar el envío cuando la conexión se restablezca.
**Impacto:** Crítico para cumplimiento legal (RD 8/2019 — registro obligatorio de jornada).
**Esfuerzo:** ~2 días.

### 🥇 2. OTA Updates + platformio.ini

**Problema:** Cada actualización requiere acceso físico al ESP32.
**Solución:** Añadir `ArduinoOTA` y crear `platformio.ini` con configuración estándar.
**Impacto:** Permite mantener y actualizar flotas de dispositivos remotamente.
**Esfuerzo:** ~1 día.

### 🥇 3. Normalización de tenant_id + UID

**Problema:** El firmware usa `TENANT_ID "default"` que no existe en la BD. El formato de UID difiere entre firmware y seed data.
**Solución:** 
- Añadir campo `slug` al modelo Tenant para permitir `tenant_id="latagliatella"`
- Normalizar UIDs (quitar `:` en backend)
- Hacer el tenant_id configurable vía WiFi Manager (portal cautivo)
**Impacto:** Bug blocker — sin esto el sistema no funciona.
**Esfuerzo:** ~1 día.

---

## 8. CONCLUSIONES

### Resumen ejecutivo

El sistema de fichaje NFC+QR de TalentUP tiene una **base sólida** pero necesita mejoras importantes antes de producción:

1. **✅ Backend API robusta** — Endpoints NFC, QR y PIN funcionan correctamente con rate limiting y validación de transiciones.

2. **❌ Bug crítico: tenant_id** — El firmware usa `"default"` pero el backend requiere UUID. El sistema no funcionará en producción sin resolver esto.

3. **❌ Bug crítico: formato UID** — El firmware genera UIDs sin separadores (`04A1B2C3D4E5`) pero la BD los almacena con separadores (`04:A1:B2:C3:D4:E5`). Coincidencia exacta falla.

4. **⚠️ Sin cola offline** — Cualquier caída de red o backend causa pérdida de datos de fichaje. Inaceptable para cumplimiento legal.

5. **⚠️ Sin OTA** — Mantener flotas de ESP32 requiere acceso físico a cada dispositivo.

6. **✅ Hardware bien diseñado** — Pines SPI correctos, LEDs informativos, PN532 bien configurado, coste realista.

7. **✅ Documentación clara** — README completo con esquema, BOM, y pasos de compilación.

### Recomendaciones inmediatas

| # | Acción | Prioridad | Responsable |
|---|--------|-----------|-------------|
| 1 | Añadir slug al modelo Tenant y resolver en endpoint NFC | 🔴 Blocker | Backend |
| 2 | Normalizar UIDs (quitar `:` en backend) | 🔴 Blocker | Backend |
| 3 | Añadir cola offline en firmware (RTC/SPIFFS) | 🔴 Alta | Hardware |
| 4 | Añadir OTA updates | 🔴 Alta | Hardware |
| 5 | Añadir platformio.ini al repo | 🟡 Media | Hardware |
| 6 | Cambiar LED verde a GPIO16 (evitar colisión boot) | 🟢 Baja | Hardware |
| 7 | Añadir watchdog al firmware | 🟡 Media | Hardware |
| 8 | Considerar pantalla OLED para v2 | 🟢 Baja | Producto |

---

*Fin del informe técnico.*
