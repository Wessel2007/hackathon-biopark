import { chromium } from 'playwright';
import path from 'path';
import os from 'os';

const BASE = 'http://localhost:5173';
const EMAIL = 'aquilaaws@gmail.com';
const PASS  = 'biopark2025';
const SS    = (name) => path.join(os.tmpdir(), `verify_${name}.png`);

async function run() {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  // ── 1. Clear storage, go directly to /reports without any token
  await ctx.clearCookies();
  await page.goto(BASE + '/reports');
  await page.waitForLoadState('networkidle');
  let url = page.url();
  console.log('1. /reports without token → redirected to:', url);
  await page.screenshot({ path: SS('01_no_token') });

  // ── 2. Perform main login to get base token
  await page.goto(BASE + '/login');
  await page.waitForLoadState('networkidle');
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL(BASE + '/');
  console.log('2. Main login OK → on Dashboard at:', page.url());

  // ── 3. Try navigating to /reports with only main token (no reports_token)
  await page.goto(BASE + '/reports');
  await page.waitForLoadState('networkidle');
  url = page.url();
  console.log('3. /reports with main token only → redirected to:', url);
  await page.screenshot({ path: SS('03_main_token_only') });

  // ── 4. Check the reports-login page renders correctly
  const heading = await page.locator('h1').first().textContent();
  console.log('4. Reports login heading:', heading);
  const sectionLabel = await page.locator('.font-mono').first().textContent();
  console.log('4. Section label:', sectionLabel);
  await page.screenshot({ path: SS('04_reports_login_page') });

  // ── 5. Try wrong credentials on reports-login
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', 'wrongpassword');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
  const errorMsg = await page.locator('.bg-red-50').textContent().catch(() => null);
  console.log('5. Wrong credentials error shown:', errorMsg?.trim());
  await page.screenshot({ path: SS('05_wrong_creds') });

  // ── 6. Now login with correct credentials on reports-login
  await page.fill('input[type="password"]', PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL(BASE + '/reports', { timeout: 8000 });
  console.log('6. Correct credentials → redirected to:', page.url());
  await page.screenshot({ path: SS('06_reports_loaded') });

  // ── 7. Confirm reports page shows dashboard content
  const reportsTitle = await page.locator('h1').first().textContent().catch(() => '(not found)');
  console.log('7. Reports page title:', reportsTitle);

  // ── 8. Check localStorage has both tokens
  const mainToken    = await page.evaluate(() => localStorage.getItem('token'));
  const reportsToken = await page.evaluate(() => localStorage.getItem('reports_token'));
  console.log('8. main token present:', !!mainToken);
  console.log('8. reports_token present:', !!reportsToken);

  // ── 9. Navigate back to dashboard and logout — reports_token should be cleared
  await page.goto(BASE + '/');
  await page.waitForLoadState('networkidle');
  const logoutBtn = await page.locator('button[title="Sair"]');
  await logoutBtn.click();
  await page.waitForURL(BASE + '/login');
  const mainAfter    = await page.evaluate(() => localStorage.getItem('token'));
  const reportsAfter = await page.evaluate(() => localStorage.getItem('reports_token'));
  console.log('9. After logout → main token cleared:', mainAfter === null);
  console.log('9. After logout → reports_token cleared:', reportsAfter === null);
  console.log('9. Redirected to:', page.url());
  await page.screenshot({ path: SS('09_after_logout') });

  // ── 10. "Voltar aos protocolos" link on reports-login (re-login to get there again)
  await page.goto(BASE + '/login');
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL(BASE + '/');
  await page.goto(BASE + '/reports-login');
  await page.waitForLoadState('networkidle');
  const backBtn = await page.getByText('← Voltar aos protocolos');
  await backBtn.click();
  await page.waitForURL(BASE + '/');
  console.log('10. "Voltar aos protocolos" → navigated to:', page.url());

  await browser.close();

  console.log('\n=== SCREENSHOTS ===');
  for (const n of ['01_no_token','03_main_token_only','04_reports_login_page','05_wrong_creds','06_reports_loaded','09_after_logout']) {
    console.log(SS(n));
  }
}

run().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
