# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Teste pentru helper-ele de pagină ale ``ScreenshotCase``.

Helper-ele primesc o pagină Playwright, deci le verificăm pe pagini HTML sintetice care
imită structura Odoo 20 (notebook, bara formularului, raport cu grilă virtuală) — fără
server Odoo și fără să scrie capturi. Se sar dacă Playwright sau Chrome lipsesc.
"""

import unittest

from odoo.tests import BaseCase, tagged

from .screenshot_case import ScreenshotCase

#: formular cu un buton „Journal Items" în bara de sus (în afara notebook-ului) și un
#: notebook cu tab-urile în RO, ca în capturile fișelor
FORM_HTML = """
<div class="o_form_view">
  <div class="o-form-buttonbox">
    <a class="nav-link oe_stat_button" onclick="window.decoy = 1">Journal Items</a>
  </div>
  <div class="o_notebook">
    <div class="o_notebook_headers"><ul class="nav nav-tabs">
      <li class="nav-item"><button class="nav-link active" name="lines">Linii factură</button></li>
      <li class="nav-item"><button class="nav-link" name="aml_tab">Elemente jurnal</button></li>
    </ul></div>
  </div>
</div>
<script>
  document.querySelectorAll('.o_notebook .nav-link').forEach((b) => b.addEventListener('click', () => {
    setTimeout(() => {
      document.querySelectorAll('.o_notebook .nav-link').forEach((o) => o.classList.remove('active'));
      b.classList.add('active');
    }, 50);
  }));
</script>
"""

#: raport cu grilă virtuală: randează doar liniile care încap în ``window.innerHeight``,
#: ca ``account_reports`` 20.0; liniile părinte pornesc pliate și se desfac asincron
REPORT_HTML = """
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; }
  .o_content { height: 100%; overflow: auto; }
  tr { height: 100px; }
</style>
<div class="o_content"><table><tbody id="grid"></tbody></table></div>
<script>
  const lines = [];
  for (let i = 0; i < 30; i++) {
    lines.push({ id: 'p' + i, foldable: true, unfolded: false, level: 0 });
  }
  window.unfoldCount = 0;
  function render() {
    const visible = Math.ceil(window.innerHeight / 100);
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    lines.slice(0, visible).forEach((line) => {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.className = 'line_name';
      td.textContent = line.id;
      if (line.foldable) {
        const i = document.createElement('i');
        i.dataset.id = 'btn_foldable';
        i.dataset.icon = line.unfolded ? 'arrow_drop_down' : 'arrow_right';
        td.prepend(i);
        td.addEventListener('click', () => setTimeout(() => {
          if (line.unfolded) { return; }
          line.unfolded = true;
          window.unfoldCount++;
          lines.splice(lines.indexOf(line) + 1, 0, { id: line.id + '.1', foldable: false, level: 1 });
          render();
        }, 30));
      }
      tr.appendChild(td);
      grid.appendChild(tr);
    });
    // spațiul liniilor nerandate, ca bara de derulare să reflecte tot raportul
    const pad = document.createElement('tr');
    pad.style.height = (Math.max(lines.length - visible, 0) * 100) + 'px';
    grid.appendChild(pad);
  }
  window.addEventListener('resize', render);
  render();
</script>
"""


@tagged("-at_install", "post_install")
class TestScreenshotCaseHelpers(BaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415
        except ImportError as exc:
            raise unittest.SkipTest("playwright nu este instalat") from exc
        cls._pw = sync_playwright().start()
        try:
            cls._browser = cls._pw.chromium.launch(channel="chrome", headless=True)
        except Exception as exc:  # noqa: BLE001 - fără Chrome de sistem testele nu au sens
            cls._pw.stop()
            raise unittest.SkipTest(f"Chrome indisponibil pentru Playwright: {exc}") from exc
        cls.addClassCleanup(cls._pw.stop)
        cls.addClassCleanup(cls._browser.close)

    def _page(self, html, height=800):
        ctx = self._browser.new_context(viewport={"width": 1000, "height": height})
        self.addCleanup(ctx.close)
        page = ctx.new_page()
        page.set_content(html)
        return page

    def test_click_tab_ignores_form_buttons(self):
        """„Journal Items" activează tab-ul RO al notebook-ului, nu butonul omonim din bara formularului."""
        page = self._page(FORM_HTML)
        self.assertTrue(ScreenshotCase.click_notebook_tab(page, "Journal Items"))
        self.assertEqual(page.evaluate("document.querySelector('.o_notebook .nav-link.active').name"), "aml_tab")
        self.assertIsNone(page.evaluate("window.decoy ?? null"), "s-a dat click pe butonul din afara notebook-ului")

    def test_click_tab_ro_label(self):
        """Eticheta RO dată direct funcționează la fel."""
        page = self._page(FORM_HTML)
        self.assertTrue(ScreenshotCase.click_notebook_tab(page, "Elemente jurnal"))
        self.assertEqual(page.evaluate("document.querySelector('.o_notebook .nav-link.active').name"), "aml_tab")

    def test_click_tab_missing_warns(self):
        """Un tab inexistent nu mai trece tăcut: întoarce False și lasă un WARNING."""
        page = self._page(FORM_HTML)
        logger = "odoo.addons.deltatech_doc_screenshots.tests.screenshot_case"
        with self.assertLogs(logger, level="WARNING"):
            self.assertFalse(ScreenshotCase.click_notebook_tab(page, "Other Info", timeout=500))

    def test_render_full_report(self):
        """Viewport-ul crește până încape tot raportul, deci grila randează toate liniile."""
        page = self._page(REPORT_HTML)
        self.assertEqual(page.locator("td.line_name").count(), 8)
        height = ScreenshotCase.render_full_report(page, settle=100)
        self.assertGreaterEqual(height, 3000)
        self.assertEqual(page.locator("td.line_name").count(), 30)

    def test_render_full_report_capped(self):
        """``max_height`` plafonează creșterea viewport-ului."""
        page = self._page(REPORT_HTML)
        self.assertEqual(ScreenshotCase.render_full_report(page, max_height=1500, settle=100), 1500)

    def test_unfold_report_all_lines(self):
        """Se desfac și liniile de sub ecran; viewport-ul revine la dimensiunea inițială."""
        page = self._page(REPORT_HTML)
        self.assertEqual(ScreenshotCase.unfold_report(page), 30)
        self.assertEqual(page.evaluate("window.unfoldCount"), 30)
        self.assertEqual(page.viewport_size["height"], 800)

    def test_unfold_report_keep_viewport(self):
        """Cu ``keep_viewport=True`` raportul rămâne randat integral pentru captură."""
        page = self._page(REPORT_HTML)
        ScreenshotCase.unfold_report(page, keep_viewport=True)
        self.assertEqual(page.locator("td.line_name").count(), 60)
        self.assertGreaterEqual(page.viewport_size["height"], 6000)
