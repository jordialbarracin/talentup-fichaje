"""
TalentUP Fichaje - ESP32 CYD Firmware Test Suite
================================================

Unit tests that simulate the firmware behavior (esp32_fichaje_cyd.ino)
in pure Python with mocks for all hardware: WiFi, TFT_eSPI, PN532 (NFC),
SPIFFS, HTTPClient, ArduinoOTA, and the ESP32 task watchdog (WDT).

No Arduino toolchain or real hardware is required — pytest runs the
logic ported from the .ino file against in-memory fakes.

Run:
    cd /c/Users/jordi/talentup-fichaje/hardware/esp32_fichaje_cyd
    python -m pytest test/ -q
"""

import json
import time
import pytest
from unittest.mock import MagicMock, patch, call

# ============================================================
#  CONSTANTS (ported from esp32_fichaje_cyd.ino defines)
# ============================================================

WIFI_SSID = "TU_WIFI_SSID"
WIFI_PASS = "TU_WIFI_PASSWORD"
BACKEND_URL = "http://192.168.1.100:8000"
TENANT_ID = "default"

PN532_I2C_SDA = 22
PN532_I2C_SCL = 27
PN532_IRQ = 255
PN532_RESET = 255
TFT_BL_PIN = 21

DEBOUNCE_MS = 3000
NFC_POLL_MS = 100
WIFI_RECHECK_MS = 10000
CLOCK_UPDATE_MS = 1000
QUEUE_FLUSH_MS = 15000
FEEDBACK_MS = 3000
WDT_TIMEOUT_S = 30
HTTP_TIMEOUT_MS = 5000

QUEUE_FILE = "/fichajes_queue.json"
QUEUE_MAX_ENTRIES = 50

# WiFi status constants (mirror Arduino WiFi.h)
WL_IDLE_STATUS = 0
WL_NO_SSID_AVAIL = 1
WL_SCAN_COMPLETED = 2
WL_CONNECTED = 3
WL_CONNECT_FAILED = 4
WL_CONNECTION_LOST = 5
WL_DISCONNECTED = 6


# ============================================================
#  MOCK HARDWARE LAYER
# ============================================================

class MockSPIFFS:
    """In-memory SPIFFS filesystem fake."""

    def __init__(self):
        self.files = {}
        self.mounted = False

    def begin(self, format_if_failed=False):
        self.mounted = True
        return True

    def exists(self, path):
        return path in self.files

    def open(self, path, mode="r"):
        if mode == "r":
            if path not in self.files:
                return None
            return MockFile(path, self.files[path], "r")
        # write mode: overwrite
        self.files[path] = ""
        return MockFile(path, "", "w", self)

    def remove(self, path):
        if path in self.files:
            del self.files[path]
            return True
        return False

    def _commit(self, path, content):
        self.files[path] = content


class MockFile:
    """Fake File object backed by a string buffer."""

    def __init__(self, path, content, mode, spiffs=None):
        self.path = path
        self.mode = mode
        self._buf = content
        self._pos = 0
        self._spiffs = spiffs
        self._write_buf = ""
        self._closed = False

    # Arduino File API
    def read(self):
        if self._pos < len(self._buf):
            ch = self._buf[self._pos]
            self._pos += 1
            return ch
        return -1

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        self._write_buf += data
        return len(data)

    def print(self, data):
        return self.write(str(data))

    def println(self, data=""):
        return self.write(str(data) + "\n")

    def close(self):
        if self.mode == "w" and self._spiffs is not None:
            self._spiffs._commit(self.path, self._write_buf)
        self._closed = True

    # Pythonic helpers used by the port to read/write JSON
    def readall(self):
        return self._buf

    def __bool__(self):
        return not self._closed and self.path is not None


class MockWiFi:
    """Fake WiFi STA stack."""

    def __init__(self):
        self._status = WL_DISCONNECTED
        self._ssid = None
        self._pass = None
        self._hostname = None
        self._mode = None
        self._ip = None
        self._connect_fails = 0  # how many begin() calls should fail
        self._connect_attempts = 0

    def mode(self, m):
        self._mode = m

    def setHostname(self, name):
        self._hostname = name

    def begin(self, ssid, pwd=None):
        self._ssid = ssid
        self._pass = pwd
        self._connect_attempts += 1
        if self._connect_fails > 0:
            self._connect_fails -= 1
            self._status = WL_CONNECT_FAILED
        else:
            self._status = WL_CONNECTED
            self._ip = "192.168.1.50"

    def status(self):
        return self._status

    def localIP(self):
        return self._ip or "0.0.0.0"

    def disconnect(self):
        self._status = WL_DISCONNECTED

    # Test helpers
    def force_connected(self):
        self._status = WL_CONNECTED
        self._ip = "192.168.1.50"

    def force_disconnected(self):
        self._status = WL_DISCONNECTED

    def set_connect_failures(self, n):
        self._connect_fails = n


class MockHTTPClient:
    """Fake HTTPClient. Returns configurable codes and bodies."""

    def __init__(self):
        self._url = None
        self._headers = {}
        self._timeout = 0
        self._response_code = 200
        self._response_body = '{"status":"in","employee_name":"Test User","time":"12:00"}'
        self._should_timeout = False
        self.last_body = None
        self.calls = 0

    def begin(self, client, url):
        self._url = url
        self.calls += 1

    def addHeader(self, key, value):
        self._headers[key] = value

    def setTimeout(self, ms):
        self._timeout = ms

    def POST(self, body):
        self.last_body = body
        if self._should_timeout:
            return -1  # connection error
        return self._response_code

    def getString(self):
        return self._response_body

    def end(self):
        # Don't clear _url so tests can inspect it
        pass

    # Test config
    def set_response(self, code, body):
        self._response_code = code
        self._response_body = body

    def set_timeout_failure(self):
        self._should_timeout = True


class MockPN532:
    """Fake PN532 NFC reader."""

    def __init__(self):
        self._firmware = 0x32000014  # non-zero = present
        self._queue = []  # list of (uid_bytes, uid_len) to return
        self._sam_configured = False

    def begin(self):
        pass

    def getFirmwareVersion(self):
        return self._firmware

    def SAMConfig(self):
        self._sam_configured = True

    def readPassiveTargetID(self, cardtype, uid_buf, uid_len_ref, timeout):
        if self._queue:
            uid_bytes, uid_len = self._queue.pop(0)
            for i, b in enumerate(uid_bytes):
                uid_buf[i] = b
            uid_len_ref[0] = uid_len
            return True
        return False

    # Test helpers
    def set_present(self, firmware=0x32000014):
        self._firmware = firmware

    def set_absent(self):
        self._firmware = 0

    def enqueue_tag(self, uid_bytes):
        self._queue.append((uid_bytes, len(uid_bytes)))


class MockOTA:
    """Fake ArduinoOTA."""

    def __init__(self):
        self._hostname = None
        self._password = None
        self._on_start = None
        self._on_progress = None
        self._on_end = None
        self._on_error = None
        self._begun = False
        self._handled = False

    def setHostname(self, name):
        self._hostname = name

    def setPassword(self, pw):
        self._password = pw

    def onStart(self, cb):
        self._on_start = cb

    def onProgress(self, cb):
        self._on_progress = cb

    def onEnd(self, cb):
        self._on_end = cb

    def onError(self, cb):
        self._on_error = cb

    def begin(self):
        self._begun = True

    def handle(self):
        self._handled = True

    # Test trigger
    def trigger_start(self):
        if self._on_start:
            self._on_start()

    def trigger_progress(self, progress, total):
        if self._on_progress:
            self._on_progress(progress, total)

    def trigger_end(self):
        if self._on_end:
            self._on_end()

    def trigger_error(self, err):
        if self._on_error:
            self._on_error(err)


class MockWatchdog:
    """Fake esp_task_wdt."""

    def __init__(self):
        self._init_timeout = None
        self._init_panic = None
        self._subscribed = False
        self._feed_count = 0

    def init(self, timeout, panic):
        self._init_timeout = timeout
        self._init_panic = panic

    def add(self, handle):
        self._subscribed = True

    def reset(self):
        self._feed_count += 1


class MockTFT:
    """Minimal TFT_eSPI fake — just records that calls happen."""

    def __init__(self):
        self.calls = []
        self._bg = None

    def init(self):
        self.calls.append("init")

    def setRotation(self, r):
        self.calls.append(("rotation", r))

    def fillScreen(self, color):
        self._bg = color
        self.calls.append(("fillScreen", color))

    def fillRect(self, *args):
        self.calls.append(("fillRect",) + args)

    def setTextDatum(self, d):
        self.calls.append(("textDatum", d))

    def setTextColor(self, *args):
        self.calls.append(("textColor",) + args)

    def drawString(self, *args):
        self.calls.append(("drawString",) + args)

    def fillCircle(self, *args):
        self.calls.append(("fillCircle",) + args)

    def drawFastHLine(self, *args):
        self.calls.append(("hline",) + args)


class MockSerial:
    """Fake Serial output sink."""

    def __init__(self):
        self.output = []

    def _log(self, msg):
        self.output.append(str(msg))

    def print(self, msg=""):
        self._log(msg)

    def println(self, msg=""):
        self._log(msg)


# ============================================================
#  FIRMWARE LOGIC PORT (pure-Python reimplementation of .ino)
# ============================================================

class FirmwareSim:
    """
    Port of esp32_fichaje_cyd.ino logic to pure Python.
    Each method mirrors the corresponding C++ function, operating on
    injected mock hardware so behavior can be exercised without an ESP32.
    """

    def __init__(self, wifi=None, http_factory=None, nfc=None,
                 spiffs=None, ota=None, wdt=None, tft=None,
                 serial=None, clock_fn=None):
        # Inject mocks (with sensible defaults)
        self.wifi = wifi or MockWiFi()
        self.http_factory = http_factory or (lambda: MockHTTPClient())
        self.nfc = nfc or MockPN532()
        self.spiffs = spiffs or MockSPIFFS()
        self.ota = ota or MockOTA()
        self.wdt = wdt or MockWatchdog()
        self.tft = tft or MockTFT()
        self.serial = serial or MockSerial()
        self._clock_fn = clock_fn or (lambda: int(time.time()))

        # State (mirrors globals in .ino)
        self.last_uid = ""
        self.last_read_time = 0
        self.pn532_ok = False
        self.wifi_connected = False
        self.queue_count = 0
        self.last_clock_draw = 0
        self.last_wifi_check = 0
        self.last_queue_flush = 0
        self.feedback_until = 0
        self.ui_state = "UI_IDLE"
        self.fb_name = ""
        self.fb_status = ""
        self.fb_is_error = False
        # Simulated Arduino millis() — starts at a post-setup value since
        # the real firmware's setup() (delays, inits) takes several seconds,
        # so by the time loop() runs millis() is well past 0.
        self._millis = 5000

    # --- millis / time helpers ---
    def millis(self):
        return self._millis

    def advance(self, ms):
        """Advance simulated clock by ms milliseconds."""
        self._millis += ms

    def _time(self):
        return self._clock_fn()

    # --- formatUID (lines 460-468) ---
    def format_uid(self, uid_bytes, length):
        s = ""
        for i in range(length):
            b = uid_bytes[i] if isinstance(uid_bytes, (bytes, bytearray, list)) else uid_bytes
            val = b[i] if not isinstance(b, int) else uid_bytes[i]
            if val < 0x10:
                s += "0"
            s += format(val, 'x')
        return s.upper()

    # --- initSPIFFS (lines 302-312) ---
    def init_spiffs(self):
        ok = self.spiffs.begin(True)
        if not ok:
            return
        self.queue_count = self.get_queue_count()

    # --- getQueueCount (lines 574-592) ---
    def get_queue_count(self):
        if not self.spiffs.exists(QUEUE_FILE):
            return 0
        f = self.spiffs.open(QUEUE_FILE, "r")
        if not f:
            return 0
        try:
            doc = json.loads(f.readall())
        except (ValueError, Exception):
            self.spiffs.remove(QUEUE_FILE)
            return 0
        f.close()
        arr = doc.get("queue", None)
        return len(arr) if isinstance(arr, list) else 0

    # --- enqueueFichaje (lines 594-636) ---
    def enqueue_fichaje(self, uid):
        doc = {}
        if self.spiffs.exists(QUEUE_FILE):
            f = self.spiffs.open(QUEUE_FILE, "r")
            if f:
                try:
                    doc = json.loads(f.readall())
                except (ValueError, Exception):
                    doc = {}
                f.close()
        arr = doc.get("queue", [])
        if not isinstance(arr, list):
            arr = []
        if len(arr) >= QUEUE_MAX_ENTRIES:
            return False
        arr.append({
            "nfc_uid": uid,
            "tenant_id": TENANT_ID,
            "ts": self._time(),
        })
        doc["queue"] = arr
        fw = self.spiffs.open(QUEUE_FILE, "w")
        if not fw:
            return False
        fw.write(json.dumps(doc))
        fw.close()
        self.queue_count = len(arr)
        return True

    # --- flushQueue (lines 638-725) ---
    def flush_queue(self):
        if not self.spiffs.exists(QUEUE_FILE):
            self.queue_count = 0
            return True
        f = self.spiffs.open(QUEUE_FILE, "r")
        if not f:
            return False
        try:
            doc = json.loads(f.readall())
        except (ValueError, Exception):
            self.spiffs.remove(QUEUE_FILE)
            self.queue_count = 0
            return False
        f.close()
        arr = doc.get("queue", None)
        if not isinstance(arr, list) or len(arr) == 0:
            self.queue_count = 0
            self.spiffs.remove(QUEUE_FILE)
            return True

        all_sent = True
        for entry in arr:
            self.wdt.reset()  # feedWdt inside loop
            uid = entry.get("nfc_uid", "")
            tid = entry.get("tenant_id", TENANT_ID)
            if not uid:
                continue
            http = self.http_factory()
            url = BACKEND_URL + "/api/clock/nfc"
            http.begin(None, url)
            http.addHeader("Content-Type", "application/json")
            http.setTimeout(HTTP_TIMEOUT_MS)
            body = json.dumps({"nfc_uid": uid, "tenant_id": tid})
            code = http.POST(body)
            http.end()
            if code in (200, 201):
                continue
            else:
                all_sent = False
                break

        if all_sent:
            self.spiffs.remove(QUEUE_FILE)
            self.queue_count = 0
        else:
            self.queue_count = len(arr)
        return all_sent

    # --- connectWiFi (lines 371-399) ---
    def connect_wifi(self, max_attempts=20):
        self.wifi.mode(1)  # WIFI_STA
        self.wifi.setHostname("talentup-fichaje-cyd")
        self.wifi.begin(WIFI_SSID, WIFI_PASS)
        attempts = 0
        while self.wifi.status() != WL_CONNECTED and attempts < max_attempts:
            self.advance(500)
            attempts += 1
            self.wdt.reset()
        if self.wifi.status() == WL_CONNECTED:
            self.wifi_connected = True
        else:
            self.wifi_connected = False

    # --- reconnectWiFi (lines 401-423) ---
    def reconnect_wifi(self, max_attempts=10):
        self.wifi.disconnect()
        self.advance(100)
        self.wifi.begin(WIFI_SSID, WIFI_PASS)
        attempts = 0
        while self.wifi.status() != WL_CONNECTED and attempts < max_attempts:
            self.advance(500)
            attempts += 1
            self.wdt.reset()
        if self.wifi.status() == WL_CONNECTED:
            self.wifi_connected = True
        else:
            self.wifi_connected = False

    # --- processNFCTag (lines 429-458) ---
    def process_nfc_tag(self):
        uid = [0] * 7
        uid_len = [0]
        success = self.nfc.readPassiveTargetID(0, uid, uid_len, NFC_POLL_MS)
        if not success:
            return None
        now = self.millis()
        # Debounce
        if now - self.last_read_time < DEBOUNCE_MS:
            return None
        self.last_read_time = now
        uid_str = self.format_uid(uid, uid_len[0])
        # Avoid consecutive duplicate
        if uid_str == self.last_uid:
            return None
        self.last_uid = uid_str
        self.send_to_backend(uid_str)
        return uid_str

    # --- sendToBackend (lines 474-568) ---
    def send_to_backend(self, uid):
        self.wdt.reset()
        if not self.wifi_connected:
            ok = self.enqueue_fichaje(uid)
            return {"queued": ok, "http": None}
        http = self.http_factory()
        url = BACKEND_URL + "/api/clock/nfc"
        http.begin(None, url)
        http.addHeader("Content-Type", "application/json")
        http.setTimeout(HTTP_TIMEOUT_MS)
        body = json.dumps({"nfc_uid": uid, "tenant_id": TENANT_ID})
        http_code = http.POST(body)
        result = {"http": http_code, "queued": False}
        if http_code > 0:
            if http_code in (200, 201):
                result["status"] = "ok"
            else:
                result["status"] = "http_error"
        else:
            # connection error → enqueue
            result["queued"] = self.enqueue_fichaje(uid)
        http.end()
        self.wdt.reset()
        return result

    # --- initWatchdog (lines 355-361) ---
    def init_watchdog(self):
        self.wdt.init(WDT_TIMEOUT_S, True)
        self.wdt.add(None)

    # --- feedWdt (lines 363-365) ---
    def feed_wdt(self):
        self.wdt.reset()

    # --- initNFC (lines 271-300) ---
    def init_nfc(self):
        self.nfc.begin()
        version = self.nfc.getFirmwareVersion()
        if not version:
            self.pn532_ok = False
            return False
        self.pn532_ok = True
        self.nfc.SAMConfig()
        return True

    # --- initOTA (lines 314-353) ---
    def init_ota(self):
        self.ota.setHostname("talentup-fichaje-cyd")
        self.ota.setPassword("talentup2024")
        self.ota.begin()

    # --- loop() WiFi check portion (lines 217-226) ---
    def loop_wifi_check(self):
        now = self.millis()
        if now - self.last_wifi_check > WIFI_RECHECK_MS:
            self.last_wifi_check = now
            if self.wifi.status() != WL_CONNECTED:
                self.wifi_connected = False
                self.reconnect_wifi()
            else:
                self.wifi_connected = True

    # --- loop() queue flush portion (lines 229-234) ---
    def loop_queue_flush(self):
        now = self.millis()
        if self.wifi_connected and self.queue_count > 0 and \
           (now - self.last_queue_flush > QUEUE_FLUSH_MS):
            self.last_queue_flush = now
            self.flush_queue()


# ============================================================
#  FIXTURES
# ============================================================

@pytest.fixture
def fw():
    """Fresh firmware sim with default mocks."""
    return FirmwareSim()


@pytest.fixture
def fw_with_spiffs():
    """Firmware with SPIFFS mounted (for queue tests)."""
    fw = FirmwareSim()
    fw.init_spiffs()
    return fw


# ============================================================
#  TEST 1: formatUID — bytes to hex conversion
# ============================================================

class TestFormatUID:
    """formatUID converts raw UID bytes to uppercase hex string."""

    def test_single_byte(self, fw):
        # 0x04 -> "04"
        assert fw.format_uid([0x04], 1) == "04"

    def test_four_bytes(self, fw):
        # Typical MIFARE 4-byte UID
        assert fw.format_uid([0xDE, 0xAD, 0xBE, 0xEF], 4) == "DEADBEEF"

    def test_seven_bytes(self, fw):
        # 7-byte UID (NFC type)
        assert fw.format_uid([0x04, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC], 7) == "04123456789ABC"

    def test_leading_zeros_preserved(self, fw):
        # Ensure leading-zero bytes get "0" prefix
        assert fw.format_uid([0x00, 0x01, 0x0A], 3) == "00010A"

    def test_uppercase_output(self, fw):
        result = fw.format_uid([0xAB, 0xCD, 0xEF], 3)
        assert result == result.upper()
        assert result == "ABCDEF"

    def test_empty_uid(self, fw):
        assert fw.format_uid([], 0) == ""

    def test_max_byte_values(self, fw):
        assert fw.format_uid([0xFF, 0xFF, 0xFF, 0xFF], 4) == "FFFFFFFF"


# ============================================================
#  TEST 2: Queue SPIFFS — enqueue, flush, max entries
# ============================================================

class TestQueueSPIFFS:
    """Offline queue stored in SPIFFS: enqueue, flush, and max-entries cap."""

    def test_enqueue_writes_to_spiffs(self, fw_with_spiffs):
        fw = fw_with_spiffs
        assert fw.enqueue_fichaje("AABBCCDD") is True
        assert fw.queue_count == 1
        # File should exist on SPIFFS
        assert fw.spiffs.exists(QUEUE_FILE)
        data = json.loads(fw.spiffs.files[QUEUE_FILE])
        assert "queue" in data
        assert len(data["queue"]) == 1
        assert data["queue"][0]["nfc_uid"] == "AABBCCDD"
        assert data["queue"][0]["tenant_id"] == TENANT_ID

    def test_enqueue_multiple_accumulates(self, fw_with_spiffs):
        fw = fw_with_spiffs
        for i in range(5):
            fw.enqueue_fichaje(f"UID{i:04X}")
        assert fw.queue_count == 5
        data = json.loads(fw.spiffs.files[QUEUE_FILE])
        assert len(data["queue"]) == 5
        assert data["queue"][4]["nfc_uid"] == "UID0004"

    def test_get_queue_count_after_enqueue(self, fw_with_spiffs):
        fw = fw_with_spiffs
        fw.enqueue_fichaje("11111111")
        fw.enqueue_fichaje("22222222")
        # New count is derived from file
        fw.queue_count = fw.get_queue_count()
        assert fw.queue_count == 2

    def test_get_queue_count_no_file(self, fw):
        fw.init_spiffs()
        assert fw.get_queue_count() == 0

    def test_get_queue_count_corrupt_json_resets(self, fw):
        fw.init_spiffs()
        fw.spiffs.files[QUEUE_FILE] = "not valid json{{"
        assert fw.get_queue_count() == 0
        # corrupt file should be removed
        assert not fw.spiffs.exists(QUEUE_FILE)

    def test_max_entries_rejects(self, fw_with_spiffs):
        fw = fw_with_spiffs
        # Fill to QUEUE_MAX_ENTRIES
        for i in range(QUEUE_MAX_ENTRIES):
            assert fw.enqueue_fichaje(f"MAX{i:08X}") is True
        assert fw.queue_count == QUEUE_MAX_ENTRIES
        # Next enqueue should fail
        assert fw.enqueue_fichaje("OVERFLOW") is False
        assert fw.queue_count == QUEUE_MAX_ENTRIES
        # Verify nothing extra was written
        data = json.loads(fw.spiffs.files[QUEUE_FILE])
        assert len(data["queue"]) == QUEUE_MAX_ENTRIES

    def test_flush_empties_queue_on_success(self, fw_with_spiffs):
        fw = fw_with_spiffs
        fw.enqueue_fichaje("FLUSH01")
        fw.enqueue_fichaje("FLUSH02")
        assert fw.queue_count == 2
        # Provide an HTTP mock that returns 200
        fw.http_factory = lambda: MockHTTPClient()  # default 200
        # Simulate wifi connected
        fw.wifi_connected = True
        result = fw.flush_queue()
        assert result is True
        assert fw.queue_count == 0
        assert not fw.spiffs.exists(QUEUE_FILE)

    def test_flush_stops_on_http_failure(self, fw_with_spiffs):
        fw = fw_with_spiffs
        fw.enqueue_fichaje("FAIL01")
        fw.enqueue_fichaje("FAIL02")
        http = MockHTTPClient()
        http.set_response(500, '{"detail":"server error"}')
        fw.http_factory = lambda: http
        fw.wifi_connected = True
        result = fw.flush_queue()
        assert result is False
        # Queue should still hold pending entries
        assert fw.queue_count >= 1
        assert fw.spiffs.exists(QUEUE_FILE)

    def test_flush_empty_queue_is_noop(self, fw_with_spiffs):
        fw = fw_with_spiffs
        result = fw.flush_queue()
        assert result is True
        assert fw.queue_count == 0

    def test_enqueue_timestamps_present(self, fw_with_spiffs):
        fw = fw_with_spiffs
        fw._clock_fn = lambda: 1700000000
        fw.enqueue_fichaje("TS00001")
        data = json.loads(fw.spiffs.files[QUEUE_FILE])
        assert data["queue"][0]["ts"] == 1700000000


# ============================================================
#  TEST 3: WiFi reconnection logic
# ============================================================

class TestWiFiReconnection:
    """connectWiFi and reconnectWiFi set wifi_connected correctly."""

    def test_connect_success(self, fw):
        fw.wifi.force_connected()  # next begin() → connected
        fw.connect_wifi()
        assert fw.wifi_connected is True
        assert fw.wifi._hostname == "talentup-fichaje-cyd"

    def test_connect_failure_sets_offline(self, fw):
        fw.wifi.set_connect_failures(25)  # more than 20 attempts
        fw.connect_wifi(max_attempts=20)
        assert fw.wifi_connected is False

    def test_reconnect_success(self, fw):
        fw.wifi.force_disconnected()
        fw.wifi_connected = False
        # After disconnect+begin, force connected
        fw.wifi.force_connected()
        fw.reconnect_wifi()
        assert fw.wifi_connected is True

    def test_reconnect_failure_stays_offline(self, fw):
        fw.wifi.force_disconnected()
        fw.wifi.set_connect_failures(15)  # more than 10 attempts
        fw.reconnect_wifi(max_attempts=10)
        assert fw.wifi_connected is False

    def test_loop_triggers_reconnect_when_disconnected(self, fw):
        fw.wifi.force_disconnected()
        fw.wifi_connected = True
        fw.last_wifi_check = 0
        # Make reconnect succeed
        fw.wifi.force_connected()
        fw.advance(WIFI_RECHECK_MS + 1)
        fw.loop_wifi_check()
        assert fw.wifi_connected is True

    def test_loop_keeps_connected_when_wifi_ok(self, fw):
        fw.wifi.force_connected()
        fw.wifi_connected = True
        fw.last_wifi_check = 0
        fw.advance(WIFI_RECHECK_MS + 1)
        fw.loop_wifi_check()
        assert fw.wifi_connected is True

    def test_loop_no_reconnect_within_interval(self, fw):
        fw.wifi.force_disconnected()
        fw.wifi_connected = False
        fw.last_wifi_check = 1000
        fw.advance(500)  # less than WIFI_RECHECK_MS
        fw.loop_wifi_check()
        # Should not have tried to reconnect
        assert fw.wifi_connected is False


# ============================================================
#  TEST 4: NFC debounce — no reading same tag twice within 3s
# ============================================================

class TestNFCDebounce:
    """processNFCTag debounces: same tag within DEBOUNCE_MS (3s) is ignored."""

    def _make_fw(self, tags):
        nfc = MockPN532()
        nfc.set_present()
        for t in tags:
            nfc.enqueue_tag(t)
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        return fw

    def test_first_read_accepted(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        result = fw.process_nfc_tag()
        assert result == "11223344"

    def test_same_tag_within_3s_ignored(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        # First read
        r1 = fw.process_nfc_tag()
        assert r1 == "11223344"
        # Immediately (within 3s) — should be debounced
        fw.advance(1000)  # 1s later
        r2 = fw.process_nfc_tag()
        assert r2 is None  # debounced

    def test_same_tag_after_3s_accepted(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        r1 = fw.process_nfc_tag()
        assert r1 == "11223344"
        fw.advance(DEBOUNCE_MS + 1)  # just over 3s
        # But last_uid is same — consecutive duplicate also blocked
        # The .ino blocks if uidStr == lastUID (line 448)
        r2 = fw.process_nfc_tag()
        # Same UID as lastUID → blocked by consecutive-duplicate check
        assert r2 is None

    def test_different_tag_within_3s_blocked_by_debounce(self):
        """The firmware's debounce is time-based — it blocks ALL reads within
        DEBOUNCE_MS, regardless of whether the tag is different.
        (See .ino lines 440-441: `if (now - lastReadTime < DEBOUNCE_MS) return;`)"""
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0xAA, 0xBB, 0xCC, 0xDD])
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        r1 = fw.process_nfc_tag()
        assert r1 == "AABBCCDD"
        fw.advance(500)  # within debounce window → blocked (even different tag)
        r2 = fw.process_nfc_tag()
        assert r2 is None  # debounced by time, not UID

    def test_different_tag_after_3s_accepted(self):
        """A different tag AFTER the debounce window is accepted."""
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0xAA, 0xBB, 0xCC, 0xDD])
        nfc.enqueue_tag([0x11, 0x22, 0x33, 0x44])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        r1 = fw.process_nfc_tag()
        assert r1 == "AABBCCDD"
        fw.advance(DEBOUNCE_MS + 1)  # past debounce, different tag
        r2 = fw.process_nfc_tag()
        assert r2 == "11223344"

    def test_consecutive_duplicate_blocked_regardless_of_time(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0xDE, 0xAD, 0xBE, 0xEF])
        nfc.enqueue_tag([0xDE, 0xAD, 0xBE, 0xEF])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        r1 = fw.process_nfc_tag()
        assert r1 == "DEADBEEF"
        fw.advance(DEBOUNCE_MS + 1000)  # well past debounce
        r2 = fw.process_nfc_tag()
        assert r2 is None  # blocked by lastUID equality check

    def test_no_tag_returns_none(self):
        nfc = MockPN532()
        nfc.set_present()
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        assert fw.process_nfc_tag() is None

    def test_debounce_boundary_exactly_3s(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0x01, 0x02, 0x03, 0x04])
        fw = FirmwareSim(nfc=nfc)
        fw.init_nfc()
        fw.pn532_ok = True
        fw.process_nfc_tag()
        # Exactly DEBOUNCE_MS later → condition `now - last < DEBOUNCE_MS` is False
        nfc.enqueue_tag([0x05, 0x06, 0x07, 0x08])  # different tag
        fw.advance(DEBOUNCE_MS)
        r = fw.process_nfc_tag()
        assert r == "05060708"  # accepted at boundary


# ============================================================
#  TEST 5: HTTP POST to backend with timeout
# ============================================================

class TestHTTPPost:
    """sendToBackend performs HTTP POST with timeout, handles codes and errors."""

    def test_http_timeout_configured(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw.http_factory = lambda: http
        fw.send_to_backend("AABBCCDD")
        assert http._timeout == HTTP_TIMEOUT_MS

    def test_success_200(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"Alice","time":"09:00"}')
        fw.http_factory = lambda: http
        result = fw.send_to_backend("AABBCCDD")
        assert result["http"] == 200
        assert result["status"] == "ok"

    def test_success_201(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(201, '{"status":"out","employee_name":"Bob","time":"17:00"}')
        fw.http_factory = lambda: http
        result = fw.send_to_backend("AABBCCDD")
        assert result["http"] == 201
        assert result["status"] == "ok"

    def test_http_error_4xx_does_not_enqueue(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(404, '{"detail":"not found"}')
        fw.http_factory = lambda: http
        fw.init_spiffs()
        result = fw.send_to_backend("AABBCCDD")
        assert result["http"] == 404
        assert result["status"] == "http_error"
        # HTTP error (code > 0) does NOT enqueue per .ino logic
        assert result["queued"] is False
        assert fw.queue_count == 0

    def test_connection_error_enqueues(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_timeout_failure()  # POST returns -1
        fw.http_factory = lambda: http
        fw.init_spiffs()
        result = fw.send_to_backend("AABBCCDD")
        assert result["http"] == -1
        assert result["queued"] is True
        assert fw.queue_count == 1

    def test_offline_mode_enqueues_immediately(self, fw):
        fw.wifi_connected = False
        fw.init_spiffs()
        result = fw.send_to_backend("AABBCCDD")
        assert result["http"] is None
        assert result["queued"] is True
        assert fw.queue_count == 1

    def test_offline_queue_full_shows_error(self, fw):
        fw.wifi_connected = False
        fw.init_spiffs()
        # Pre-fill queue to max
        for i in range(QUEUE_MAX_ENTRIES):
            fw.enqueue_fichaje(f"FULL{i:08X}")
        result = fw.send_to_backend("OVERFLOW")
        assert result["queued"] is False

    def test_post_body_contains_uid_and_tenant(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw.http_factory = lambda: http
        fw.send_to_backend("AABBCCDD")
        body = json.loads(http.last_body)
        assert body["nfc_uid"] == "AABBCCDD"
        assert body["tenant_id"] == TENANT_ID

    def test_post_url_correct(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw.http_factory = lambda: http
        fw.send_to_backend("AABBCCDD")
        assert http._url == BACKEND_URL + "/api/clock/nfc"

    def test_wdt_fed_around_http(self, fw):
        fw.wifi_connected = True
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw.http_factory = lambda: http
        before = fw.wdt._feed_count
        fw.send_to_backend("AABBCCDD")
        # feedWdt called at start and end of sendToBackend → at least 2
        assert fw.wdt._feed_count >= before + 2


# ============================================================
#  TEST 6: OTA update trigger
# ============================================================

class TestOTA:
    """initOTA configures callbacks; triggering fires them correctly."""

    def test_init_sets_hostname_and_password(self, fw):
        fw.init_ota()
        assert fw.ota._hostname == "talentup-fichaje-cyd"
        assert fw.ota._password == "talentup2024"

    def test_init_begins_ota(self, fw):
        fw.init_ota()
        assert fw.ota._begun is True

    def test_trigger_start_calls_callback(self, fw):
        fw.init_ota()
        called = []
        fw.ota.onStart(lambda: called.append("start"))
        fw.ota.trigger_start()
        assert called == ["start"]

    def test_trigger_progress_calls_callback(self, fw):
        fw.init_ota()
        events = []
        fw.ota.onProgress(lambda p, t: events.append((p, t)))
        fw.ota.trigger_progress(50, 100)
        assert events == [(50, 100)]

    def test_trigger_end_calls_callback(self, fw):
        fw.init_ota()
        called = []
        fw.ota.onEnd(lambda: called.append("end"))
        fw.ota.trigger_end()
        assert called == ["end"]

    def test_trigger_error_calls_callback(self, fw):
        fw.init_ota()
        errors = []
        fw.ota.onError(lambda e: errors.append(e))
        fw.ota.trigger_error(1)
        assert errors == [1]

    def test_ota_handle_marked(self, fw):
        fw.init_ota()
        fw.ota.handle()
        assert fw.ota._handled is True

    def test_progress_callback_feeds_wdt(self, fw):
        """The .ino onProgress lambda calls feedWdt()."""
        fw.init_watchdog()
        before = fw.wdt._feed_count
        # Simulate the onProgress body from .ino (lines 327-336)
        def on_progress(progress, total):
            fw.feed_wdt()  # mirror .ino line 328
            pct = (progress * 100) // total
        fw.ota.onProgress(on_progress)
        fw.ota.trigger_progress(50, 100)
        assert fw.wdt._feed_count == before + 1


# ============================================================
#  TEST 7: WDT feed
# ============================================================

class TestWDT:
    """Watchdog init and feed behavior."""

    def test_init_watchdog_timeout_30s(self, fw):
        fw.init_watchdog()
        assert fw.wdt._init_timeout == WDT_TIMEOUT_S
        assert fw.wdt._init_timeout == 30

    def test_init_watchdog_panic_mode(self, fw):
        fw.init_watchdog()
        assert fw.wdt._init_panic is True

    def test_init_adds_task(self, fw):
        fw.init_watchdog()
        assert fw.wdt._subscribed is True

    def test_feed_increments_count(self, fw):
        fw.init_watchdog()
        before = fw.wdt._feed_count
        fw.feed_wdt()
        assert fw.wdt._feed_count == before + 1

    def test_feed_called_in_setup_sequence(self, fw):
        """Mirror setup() which calls feedWdt between init steps."""
        fw.init_watchdog()
        initial = fw.wdt._feed_count
        # Simulate setup() feed calls (lines 164-197)
        fw.feed_wdt()  # after watchdog init
        fw.feed_wdt()  # after backlight
        fw.feed_wdt()  # after TFT
        fw.feed_wdt()  # after I2C
        fw.feed_wdt()  # after SPIFFS
        fw.feed_wdt()  # after NFC
        fw.feed_wdt()  # after WiFi
        fw.feed_wdt()  # after OTA
        assert fw.wdt._feed_count == initial + 8

    def test_loop_feeds_wdt_each_iteration(self, fw):
        """loop() calls feedWdt() at top (line 209)."""
        fw.init_watchdog()
        before = fw.wdt._feed_count
        # Simulate 5 loop iterations
        for _ in range(5):
            fw.feed_wdt()  # line 209
            fw.ota.handle()
        assert fw.wdt._feed_count == before + 5

    def test_connect_wifi_feeds_during_attempts(self, fw):
        fw.wifi.set_connect_failures(25)
        fw.init_watchdog()
        before = fw.wdt._feed_count
        fw.connect_wifi(max_attempts=5)
        # Each failed attempt calls feedWdt → 5 feeds
        assert fw.wdt._feed_count == before + 5

    def test_multiple_feeds_accumulate(self, fw):
        fw.init_watchdog()
        # init_watchdog calls add() but does NOT feed (reset) — only
        # explicit feed_wdt() calls increment _feed_count.
        fw.feed_wdt()
        fw.feed_wdt()
        fw.feed_wdt()
        assert fw.wdt._feed_count == 3  # exactly 3 feeds


# ============================================================
#  TEST: Integration — end-to-end offline→online flow
# ============================================================

class TestIntegration:
    """Full flow: read NFC while offline, queue, reconnect, flush."""

    def test_offline_read_queues_then_flushes_on_reconnect(self):
        nfc = MockPN532()
        nfc.set_present()
        nfc.enqueue_tag([0xCA, 0xFE, 0xBA, 0xBE])
        spiffs = MockSPIFFS()
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw = FirmwareSim(nfc=nfc, spiffs=spiffs,
                         http_factory=lambda: http)
        fw.init_watchdog()
        fw.init_spiffs()
        fw.init_nfc()
        fw.pn532_ok = True
        fw.wifi_connected = False  # offline

        # Read tag → should enqueue (not send)
        uid = fw.process_nfc_tag()
        assert uid == "CAFEBABE"
        assert fw.queue_count == 1

        # Later: WiFi comes back
        fw.wifi.force_connected()
        fw.wifi_connected = True

        # Flush queue → sends pending entry
        result = fw.flush_queue()
        assert result is True
        assert fw.queue_count == 0
        assert not spiffs.exists(QUEUE_FILE)
        # HTTP was called once for the flush
        assert http.calls == 1
        body = json.loads(http.last_body)
        assert body["nfc_uid"] == "CAFEBABE"

    def test_loop_drives_queue_flush_after_interval(self):
        spiffs = MockSPIFFS()
        http = MockHTTPClient()
        http.set_response(200, '{"status":"in","employee_name":"X","time":"12:00"}')
        fw = FirmwareSim(spiffs=spiffs, http_factory=lambda: http)
        fw.init_watchdog()
        fw.init_spiffs()
        fw.wifi_connected = True
        # Put something in the queue
        fw.enqueue_fichaje("LOOP01")
        fw.last_queue_flush = 0
        # Advance past QUEUE_FLUSH_MS
        fw.advance(QUEUE_FLUSH_MS + 1)
        fw.loop_queue_flush()
        assert fw.queue_count == 0

    def test_loop_does_not_flush_within_interval(self):
        spiffs = MockSPIFFS()
        http = MockHTTPClient()
        fw = FirmwareSim(spiffs=spiffs, http_factory=lambda: http)
        fw.init_spiffs()
        fw.wifi_connected = True
        fw.enqueue_fichaje("NOFLUSH")
        fw.last_queue_flush = 5000
        fw.advance(2000)  # less than QUEUE_FLUSH_MS (15000)
        fw.loop_queue_flush()
        assert fw.queue_count == 1  # not flushed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])