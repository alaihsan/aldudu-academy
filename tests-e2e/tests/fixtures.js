// @ts-check
const base = require('@playwright/test');
const fs = require('fs');
const path = require('path');

/**
 * base.html loads Tailwind/HTMX/SweetAlert2/SortableJS/DOMPurify/Google Fonts
 * from public CDNs via blocking (non-defer/async) <script>/<link> tags. Most
 * environments (a real dev machine, normal CI) can reach those hosts fine —
 * by default this suite lets those requests through unmodified, exactly
 * matching production.
 *
 * Set E2E_OFFLINE=1 to run without internet access to those CDNs (e.g. this
 * sandbox's restricted egress policy): a blocked *synchronous* <script src>
 * stalls HTML parsing until the connection attempt times out, so offline
 * mode fulfills HTMX/SweetAlert2/SortableJS/DOMPurify from local npm-vendored
 * copies pinned to the same versions, stubs the Tailwind Play CDN script
 * (no npm equivalent exists — real utility CSS won't be generated, so specs
 * use force:true instead of relying on visual layout), and drops Google
 * Fonts. None of this runs unless E2E_OFFLINE=1 is set.
 */
const OFFLINE = process.env.E2E_OFFLINE === '1';
// Glob patterns (not exact URLs): some pages pin a different CDN version
// than base.html (e.g. quiz_editor.html loads sortablejs@1.15.0, base.html
// loads 1.15.2) — matching on version would silently miss those requests.
const VENDOR = {
  'https://cdn.jsdelivr.net/npm/htmx.org@*/dist/htmx.min.js':
    require.resolve('htmx.org/dist/htmx.min.js'),
  'https://cdn.jsdelivr.net/npm/sweetalert2@*':
    require.resolve('sweetalert2/dist/sweetalert2.all.min.js'),
  'https://cdn.jsdelivr.net/npm/sortablejs@*/Sortable.min.js':
    require.resolve('sortablejs/Sortable.min.js'),
  // chart.js's package.json "exports" map blocks any require.resolve() of a
  // subpath (dist/ or package.json) directly — resolve its main ESM entry
  // instead and derive the UMD build's path from that directory.
  'https://cdn.jsdelivr.net/npm/chart.js':
    path.join(path.dirname(require.resolve('chart.js')), 'chart.umd.js'),
  'https://cdnjs.cloudflare.com/ajax/libs/dompurify/*/purify.min.js':
    require.resolve('dompurify/dist/purify.min.js'),
};

// No npm-published equivalent of the Tailwind Play CDN runtime exists; stub
// just enough (`window.tailwind.config`) that inline config scripts don't
// throw. Real utility CSS won't be generated — acceptable since this suite
// checks DOM/JS behavior, not visual styling.
const TAILWIND_STUB = 'window.tailwind = { config: function () {} };';

const test = base.test.extend({
  // Registered on the context (not just the initial page) so popup tabs
  // opened via window.open (e.g. clicking a quiz card) inherit the same
  // interception — a per-page route wouldn't apply to those new tabs.
  context: async ({ context }, use) => {
    if (OFFLINE) {
      for (const [url, filePath] of Object.entries(VENDOR)) {
        await context.route(url, (route) =>
          route.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(filePath, 'utf-8') })
        );
      }
      // No real utility CSS without the live CDN, so layout collapses
      // (heights/spacing come entirely from Tailwind classes on this site).
      // Specs use force:true for interactions in this mode instead of
      // depending on visual geometry.
      await context.route('https://cdn.tailwindcss.com/**', (route) =>
        route.fulfill({ contentType: 'application/javascript', body: TAILWIND_STUB })
      );
      // fulfill (not abort) so the browser doesn't log a spurious
      // net::ERR_FAILED console.error for an intentionally-skipped request.
      await context.route('https://fonts.googleapis.com/**', (route) =>
        route.fulfill({ contentType: 'text/css', body: '' })
      );
      await context.route('https://fonts.gstatic.com/**', (route) => route.fulfill({ status: 204, body: '' }));
    }
    await use(context);
  },
});

// Locator.evaluate() runs the callback directly against the matched element
// with no actionability checks at all (unlike click()/fill(), which still
// require a resolvable position even under force:true) — the only reliable
// way to drive the DOM in offline mode, where the missing Tailwind CSS
// collapses layout heights to 0.
async function clickLocator(locator) {
  if (OFFLINE) {
    await locator.evaluate((el) => el.click());
  } else {
    await locator.click();
  }
}

async function fillLocator(locator, value) {
  if (OFFLINE) {
    await locator.evaluate((el, v) => {
      el.value = v;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }, value);
  } else {
    await locator.fill(value);
  }
}

module.exports = { test, expect: base.expect, OFFLINE, clickLocator, fillLocator };
