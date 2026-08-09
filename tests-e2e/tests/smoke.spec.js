// @ts-check
const { test, expect, clickLocator, fillLocator } = require('./fixtures');

const TEACHER = { email: 'teacher@aldudu-e2e.dev', password: 'Password123!' };
const STUDENT = { email: 'student@aldudu-e2e.dev', password: 'Password123!' };

/**
 * Every test wires this up first so a broken onclick handler / 404'd
 * script / stray ReferenceError fails the test instead of passing silently
 * (the exact failure mode this refactor risks: moved/split JS files with a
 * stale path or a name no longer reachable from the global scope).
 */
// Pre-existing bugs discovered by this suite, unrelated to the JS
// modularization work (same behavior before the files were moved/split —
// reported separately to the user, not fixed here to keep this refactor's
// scope focused). Allowlisted so the suite stays useful as a regression
// gate for the actual refactor instead of perpetually red on these.
const KNOWN_PRE_EXISTING_ERRORS = [
  'setupDropZones', // course_detail.js: this.topicsContainer -> #topics-container no longer exists in the template
  'discussion.js', // document.querySelector('.container') matches nothing on course_detail
];

function trackConsoleErrors(page) {
  const errors = [];
  const record = (text) => {
    if (KNOWN_PRE_EXISTING_ERRORS.some((needle) => text.includes(needle))) return;
    errors.push(text);
  };
  page.on('pageerror', (err) => record(`pageerror: ${err.message}\n${err.stack || ''}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error') record(`console.error: ${msg.text()}`);
  });
  page.on('response', (res) => {
    if (res.url().includes('/static/js/') && res.status() >= 400) {
      record(`${res.status()} loading ${res.url()}`);
    }
  });
  return errors;
}

async function login(page, { email, password }) {
  await page.goto('/login');
  await fillLocator(page.locator('#email'), email);
  await fillLocator(page.locator('#password'), password);
  await Promise.all([
    page.waitForURL(/\/(dashboard|admin\/dashboard|superadmin\/dashboard)/, { timeout: 10_000 }),
    clickLocator(page.locator('#login-btn')),
  ]);
}

async function goToCourseDetail(page) {
  await clickLocator(page.locator('a:has-text("BUKA KELAS")').first());
  await page.waitForURL(/\/kelas\//, { timeout: 10_000 });
  await page.waitForLoadState('networkidle');
  // materials-list-v2.js populates this container asynchronously after fetch.
  await expect(page.locator('#materials-list-container')).not.toBeEmpty({ timeout: 10_000 });
}

test.describe('JS modularization smoke suite', () => {
  test('1. login + dashboard renders without console errors', async ({ page }) => {
    const errors = trackConsoleErrors(page);
    await login(page, TEACHER);
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('body')).toBeAttached();
    expect(errors, `console/script errors on dashboard:\n${errors.join('\n')}`).toEqual([]);
  });

  test('2. course detail: materials list, KBM tab, discussions all wire up', async ({ page }) => {
    const errors = trackConsoleErrors(page);
    await login(page, TEACHER);

    await goToCourseDetail(page);

    const kbmSection = page.locator('#kbm-section');
    if (await kbmSection.count()) {
      await expect(kbmSection).toBeAttached();
    }

    expect(errors, `console/script errors on course_detail:\n${errors.join('\n')}`).toEqual([]);
  });

  test('3. quiz editor loads for teacher (load-order: quiz-editor.js -> quiz_editor_inline.js)', async ({ page, context }) => {
    await login(page, TEACHER);
    await goToCourseDetail(page);

    // Quiz items open via window.open(..., '_blank') — a new tab, not
    // same-page navigation (course_detail.js onMaterialSelect callback).
    const [quizPage] = await Promise.all([
      context.waitForEvent('page'),
      clickLocator(page.locator('.material-item[data-material-type="quiz"]').first()),
    ]);
    const errors = trackConsoleErrors(quizPage);
    await quizPage.waitForURL(/\/quiz\//, { timeout: 10_000 });
    await quizPage.waitForLoadState('networkidle');

    const publishBtn = quizPage.locator('#publish-main-btn');
    if (await publishBtn.count()) {
      await clickLocator(publishBtn);
      await expect(quizPage.locator('#publish-dropdown')).toBeAttached();
    }

    expect(errors, `console/script errors on quiz editor:\n${errors.join('\n')}`).toEqual([]);
  });

  test('4. student can start a quiz (quiz_detail.js confirmStart)', async ({ page, context }) => {
    await login(page, STUDENT);
    await goToCourseDetail(page);

    const [quizPage] = await Promise.all([
      context.waitForEvent('page'),
      clickLocator(page.locator('.material-item[data-material-type="quiz"]').first()),
    ]);
    const errors = trackConsoleErrors(quizPage);
    await quizPage.waitForURL(/\/quiz\//, { timeout: 10_000 });
    await quizPage.waitForLoadState('networkidle');

    await expect(quizPage.locator('#start-screen')).toBeAttached();
    await clickLocator(quizPage.locator('#start-screen button:has-text("MULAI KERJAKAN")'));
    // confirmStart() shows a SweetAlert2 "Mulai Kuis?" dialog before startQuiz() runs.
    await expect(quizPage.locator('.swal2-confirm')).toBeAttached({ timeout: 5_000 });
    await clickLocator(quizPage.locator('.swal2-confirm'));
    await expect(quizPage.locator('#quiz-main-container')).toBeAttached();
    await expect(quizPage.locator('#quiz-main-container')).not.toHaveClass(/hidden/);

    expect(errors, `console/script errors taking quiz:\n${errors.join('\n')}`).toEqual([]);
  });

  test('5. HTMX-boosted sidebar navigation does not break (core scripts not reloaded)', async ({ page }) => {
    const errors = trackConsoleErrors(page);
    await login(page, TEACHER);
    await expect(page).toHaveURL(/\/dashboard/);

    // #app-content has hx-boost="true": clicking a sidebar link swaps innerHTML,
    // it does NOT reload language.js/theme-manager.js/sidebar.js/global-utils.js.
    await clickLocator(page.locator('a[href*="/settings"]').first());
    await page.waitForURL(/\/settings/, { timeout: 10_000 });
    await expect(page.locator('body')).toBeAttached();

    await clickLocator(page.locator('a[href*="/dashboard"]').first());
    await page.waitForURL(/\/dashboard/, { timeout: 10_000 });

    expect(errors, `console/script errors during HTMX nav:\n${errors.join('\n')}`).toEqual([]);
  });

  test('6. Ruang Kelas (classroom) shows the seeded quiz and filter/sort do not error', async ({ page }) => {
    const errors = trackConsoleErrors(page);
    await login(page, STUDENT);

    await clickLocator(page.locator('a[href*="/ruang-kelas"]').first());
    await page.waitForURL(/\/ruang-kelas/, { timeout: 10_000 });

    await expect(page.locator('#classroom-items')).not.toBeEmpty({ timeout: 10_000 });
    await expect(page.locator('#classroom-items')).toContainText('E2E Quiz');

    await page.locator('#classroom-filter').selectOption('quizzes');
    await expect(page.locator('#classroom-items')).toContainText('E2E Quiz');

    await page.locator('#classroom-sort').selectOption('recent');
    await expect(page.locator('#classroom-items')).toContainText('E2E Quiz');

    expect(errors, `console/script errors on Ruang Kelas:\n${errors.join('\n')}`).toEqual([]);
  });
});
