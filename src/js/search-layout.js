
// ---------------------------------------------------------------------
// INPUTS: every text field of the site takes English only (patch search 2026-09-26, the whole site
// 2026-10-24: Cyrillic broke the pixel fonts). A Russian-layout letter becomes the English letter on
// the same key ("ыуфк" -> "sear"), anything else non-ASCII is dropped. Fixed in the CAPTURE phase, so
// the field's own input listeners (filters, search) already see the English text.
// ---------------------------------------------------------------------
var SITE_RU = 'йцукенгшщзхъфывапролджэячсмитьбюё', SITE_EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`";
function siteToEnglish(s) {
  var out = '';
  for (var i = 0; i < s.length; i++) {
    var ch = s[i], low = ch.toLowerCase(), k = SITE_RU.indexOf(low);
    if (k >= 0) ch = ch === low ? SITE_EN[k] : SITE_EN[k].toUpperCase();
    if (ch >= ' ' && ch <= '~') out += ch;
  }
  return out;
}
(function () {
  var TEXTLIKE = { text: 1, search: 1, url: 1, email: 1, tel: 1, '': 1 };
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (!t || !(t.tagName === 'TEXTAREA' || (t.tagName === 'INPUT' && TEXTLIKE[(t.getAttribute('type') || '').toLowerCase()]))) return;
    var v = t.value, fixed = siteToEnglish(v);
    if (fixed === v) return;
    var pos = (t.selectionStart || 0) - (v.length - fixed.length);
    t.value = fixed;
    try { t.setSelectionRange(pos, pos); } catch (err) {}
  }, true);
})();
