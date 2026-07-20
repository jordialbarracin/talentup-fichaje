const { test, expect } = require('@playwright/test');

test('terminal carga y teclado PIN es visible', async ({ page }) => {
  await page.goto('http://localhost:3001');

  // Pantalla de PIN por defecto.
  await expect(page.locator('#screenPin')).toBeVisible();
  await expect(page.locator('#pinDisplay')).toBeVisible();
  await expect(page.locator('.pin-dot')).toHaveCount(4);

  // Teclado numérico visible.
  const keypad = page.locator('#keypad');
  await expect(keypad).toBeVisible();

  // Verificamos teclas 0-9 y funciones OK/BORRAR.
  for (const key of ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) {
    await expect(keypad.locator(`button[data-key="${key}"]`)).toBeVisible();
  }
  await expect(keypad.locator('button[data-key="ok"]')).toBeVisible();
  await expect(keypad.locator('button[data-key="clear"]')).toBeVisible();

  // Simulamos introducir un PIN de 4 dígitos y comprobamos que los puntos se rellenan.
  await keypad.locator('button[data-key="1"]').click();
  await keypad.locator('button[data-key="2"]').click();
  await keypad.locator('button[data-key="3"]').click();
  await keypad.locator('button[data-key="4"]').click();

  const filledDots = page.locator('.pin-dot.filled');
  await expect(filledDots).toHaveCount(4);
});
