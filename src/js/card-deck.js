
// ---- OLD -> NEW CARD AS A DECK (owner 2026-11-09, patch/card_deck.py): a click on the card's patch tab puts the one
// under it on top, in the same place; another brings the new one back. Only the tab: a click anywhere on the card
// fought the card's own buttons (a [?], a formula's levels, a fold) — owner 2026-11-10: "карточка теперь кликабельная,
// непонятно как сделать, чтобы всё норм было" -> "да, ярлык".
// The swap as a hand moving a card (owner: "слишком резкая, сам эффект выглядит бедно"): the top card slides out to the
// right with a slight tilt, the one under it rises from the steps into its place, the first goes under, the steps
// again. ----
(function() {
  const MS = 520;
  const UNDER_AT = 234;                           // ms: the card pulled out is at its far end and goes under (45%)
  const OUT = 'cubic-bezier(0.3, 0, 0.2, 1)';     // a hand pulls the card: starts at once, slows at the far end
  const BACK = 'cubic-bezier(0.4, 0, 0.6, 1)';    // and pushes it back under the deck
  const RISE = 'cubic-bezier(0.2, 0, 0, 1)';      // the card under it comes up and settles
  const still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function settle(deck, shown, hidden) {
    hidden.classList.add('deck-hid');
    [deck, shown, hidden].forEach(el => { el.style.zIndex = ''; el.style.minHeight = ''; });
    deck.classList.remove('deck-moving');
    // the card's height changed: its lines, and the folds the hidden side could not measure — only these, not a
    // whole-page resize (a long frame at the end of every swap)
    if (window.sloppyDrawConnectors) window.sloppyDrawConnectors();
    if (window.sloppyFoldSmall) window.sloppyFoldSmall();
  }

  function swap(deck) {
    if (deck.classList.contains('deck-moving')) return;
    const oldPane = deck.querySelector(':scope > .ability-change-old');
    const newPane = deck.querySelector(':scope > .ability-change-new');
    if (!oldPane || !newPane) return;
    const toOld = !deck.classList.contains('deck-old');
    const shown = toOld ? oldPane : newPane;
    const hidden = toOld ? newPane : oldPane;
    const h0 = deck.getBoundingClientRect().height;
    const r = hidden.getBoundingClientRect();
    deck.classList.toggle('deck-old', toOld);
    shown.classList.remove('deck-hid');
    // the keyboard stays on the deck: the tab pressed goes away with its card, the other card's tab takes the focus
    const fromTab = hidden.contains(document.activeElement);
    const tab = shown.querySelector('.deck-tab');
    if (fromTab && tab) tab.focus({ preventScroll: true });
    // its folds measured now, not after it rose (they opened with a jump at the end, and its height was wrong)
    if (window.sloppyFoldSmall) window.sloppyFoldSmall();
    if (still || !shown.animate) { settle(deck, shown, hidden); return; }
    deck.classList.add('deck-moving');
    const h1 = shown.getBoundingClientRect().height;
    // out to the right as far as the empty half lets it; with no room there (a phone) a little to the left: past the
    // right edge the page grew wider for a moment (Sonnet 2026-11-09: 391px in a 375px screen), past the left it does not
    const free = document.documentElement.clientWidth - r.right - 12;
    const out = free >= 40
      ? `translate(${Math.round(Math.min(r.width * 0.55, free))}px, -8px) rotate(2deg)`
      : 'translate(-24px, -8px) rotate(-2deg)';
    // Smooth on a long page (owner 2026-11-09: "очень лагает … особенно у Solar Guardian"): only transform and opacity
    // move, the browser's compositor runs them. The deck's height animated made it lay out the whole page every frame,
    // and z-index in the same keyframes kept the whole move off the compositor: the deck takes the taller height once
    // at the start (the card coming up never lies over the rows below, 7.38 Fire Dragon) and its own at the end; the
    // cards change places in depth by a timer.
    deck.style.minHeight = Math.max(h0, h1) + 'px';
    hidden.style.zIndex = '3';
    shown.style.zIndex = '2';
    // each phase its own curve, the whole on a straight clock: out (slows at the far end), under, back to the steps
    const move = hidden.animate([
      { transform: 'none', opacity: 1, easing: OUT },
      { transform: out, opacity: 1, offset: 0.45, easing: BACK },
      { transform: 'translate(6px, 6px)', opacity: 0.3 },
    ], { duration: MS, easing: 'linear' });
    shown.animate([
      { transform: 'translate(6px, 6px)', easing: RISE },
      { transform: 'translate(-3px, -1px)', offset: 0.6, easing: RISE },
      { transform: 'none' },
    ], { duration: MS, easing: 'linear' });
    const under = setTimeout(() => { hidden.style.zIndex = '1'; }, UNDER_AT);
    // once, on the animation's end — or a little after it if the browser holds that back (a tab in the background):
    // a deck left "moving" took no more clicks
    let done = false;
    const end = () => { if (!done) { done = true; clearTimeout(under); settle(deck, shown, hidden); } };
    move.onfinish = end;
    move.oncancel = end;
    setTimeout(end, MS + 250);
  }

  document.addEventListener('click', (e) => {
    const t = e.target;
    if (!t.closest) return;
    const deck = t.closest('.ability-change.is-deck');
    if (!deck) return;
    // the patch tab is the deck's button: a click, Enter or Space on it (code review 2026-11-09: no way to swap
    // without a mouse)
    if (t.closest('.deck-tab')) swap(deck);
  });
})();
