# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: test_terminal.spec.js >> terminal carga y teclado PIN es visible
- Location: tests\e2e\test_terminal.spec.js:3:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  locator('#screenPin')
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('#screenPin')
    14 × locator resolved to <div class="screen" id="screenPin">…</div>
       - unexpected value "hidden"

```

```yaml
- text: ⚠️ Sin conexión — 0 fichajes pendientes de sincronizar T TalentUP Configuración inicial Conecta este terminal con tu cuenta de TalentUP URL del Backend
- textbox "http://localhost:8000"
- text: Tenant ID
- textbox "uuid-del-tenant"
- button "🔗 Conectar terminal"
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test('terminal carga y teclado PIN es visible', async ({ page }) => {
  4  |   await page.goto('http://localhost:3001');
  5  | 
  6  |   // Pantalla de PIN por defecto.
> 7  |   await expect(page.locator('#screenPin')).toBeVisible();
     |                                            ^ Error: expect(locator).toBeVisible() failed
  8  |   await expect(page.locator('#pinDisplay')).toBeVisible();
  9  |   await expect(page.locator('.pin-dot')).toHaveCount(4);
  10 | 
  11 |   // Teclado numérico visible.
  12 |   const keypad = page.locator('#keypad');
  13 |   await expect(keypad).toBeVisible();
  14 | 
  15 |   // Verificamos teclas 0-9 y funciones OK/BORRAR.
  16 |   for (const key of ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) {
  17 |     await expect(keypad.locator(`button[data-key="${key}"]`)).toBeVisible();
  18 |   }
  19 |   await expect(keypad.locator('button[data-key="ok"]')).toBeVisible();
  20 |   await expect(keypad.locator('button[data-key="clear"]')).toBeVisible();
  21 | 
  22 |   // Simulamos introducir un PIN de 4 dígitos y comprobamos que los puntos se rellenan.
  23 |   await keypad.locator('button[data-key="1"]').click();
  24 |   await keypad.locator('button[data-key="2"]').click();
  25 |   await keypad.locator('button[data-key="3"]').click();
  26 |   await keypad.locator('button[data-key="4"]').click();
  27 | 
  28 |   const filledDots = page.locator('.pin-dot.filled');
  29 |   await expect(filledDots).toHaveCount(4);
  30 | });
  31 | 
```