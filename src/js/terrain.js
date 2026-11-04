
(function() {
  // ---- TERRAIN COMPARE (terrain.html) — swipe slider + Loupe magnifier ----
  //  - Divider moves ONLY by dragging the handle (or arrow keys).
  //  - Trees / Camps top-bar checkboxes toggle the SVG overlay layers.
  //  - "Loupe" is a MODE (top-bar button). When on, hovering the MAP (not the
  //    handle or top-bar) shows a gold magnifier following the cursor; click
  //    pins it, then sweeping the handle compares that spot old↔new inside the
  //    circle (the toggled tree/camp markers are cloned into the lens too).
  function initTerrainCompare() {
    // One slider per map pair (e.g. 7.41 and 7.40 panes both exist; hidden ones
    // are still wired so switching the picker shows a working slider).
    document.querySelectorAll('.terrain-compare').forEach(initOneTerrainCompare);
  }
  function initOneTerrainCompare(root) {
    if (!root) return;
    const stage = root.querySelector('.tc-stage');
    const handle = root.querySelector('.tc-handle');
    if (!stage || !handle) return;

    const ZOOM = parseFloat(root.dataset.zoom) || 1.9;
    const lens = root.querySelector('.tc-lens');
    const lensOld = root.querySelector('.tc-lens-old');
    const lensNew = root.querySelector('.tc-lens-new');
    const lensRim = root.querySelector('.tc-lens-rim');
    const markerSvgs = stage.querySelectorAll('.tc-markers');
    const lensOk = !!(lens && lensOld && lensNew);
    const LENS_PX = parseFloat(root.dataset.lens) || 184;
    if (root.dataset.lens) stage.style.setProperty('--lens', root.dataset.lens + 'px');

    // The page opens on 2048-px copies of the map pictures (data-small, a fifth of the bytes); an
    // image swaps to its 4096 picture (data-full) once a picture pixel would be drawn bigger than a
    // screen pixel (a big retina screen, the lens, fullscreen zoom) and never swaps back. The lens
    // images get no src until the lens is first switched on (the owner 2026-10-03: weak computers).
    const SMALL_PX = 2048;
    const baseImgs = [root.querySelector('.tc-img.tc-old'), root.querySelector('.tc-img.tc-new')];
    function fitSrc(img, cssW) {
      if (!img || !img.dataset.full || img.dataset.sharp) return;
      const sharp = cssW * (window.devicePixelRatio || 1) > SMALL_PX * 1.05;
      const want = sharp ? img.dataset.full : (img.dataset.small || img.dataset.full);
      if (sharp) img.dataset.sharp = '1';
      if (img.getAttribute('src') !== want) img.src = want;
    }
    function fitBase(cssW) { baseImgs.forEach(function(img) { fitSrc(img, cssW); }); }
    fitBase(stage.getBoundingClientRect().width);
    window.addEventListener('resize', function() { fitBase(stage.getBoundingClientRect().width); });

    let pos = parseFloat(root.dataset.pos);
    if (!isFinite(pos)) pos = 50;

    // The slider writes each split layer's clip-path (and the handle's left) itself instead of
    // changing --pos on the stage: --pos is inherited, so every move re-styled all ~6500 marker
    // shapes under the stage, hidden layers too (2026-10-03 probe, 4x CPU throttle: a drag spent
    // 13 s in style recalc, p95 frame 167 ms). The CSS var(--pos) rules stay as the no-JS default.
    const SPLIT_NEW = '.tc-new-layer, .tm-new, .tc-trees-new, .tc-camps-new, .tc-lens-new';
    const SPLIT_OLD = '.tm-old, .tc-trees-old, .tc-camps-old';
    function apply(p) {
      pos = Math.max(0, Math.min(100, p));
      const clipNew = 'inset(0 0 0 ' + pos + '%)';
      const clipOld = 'inset(0 ' + (100 - pos) + '% 0 0)';
      root.querySelectorAll(SPLIT_NEW).forEach(function(el) { el.style.clipPath = clipNew; });
      root.querySelectorAll(SPLIT_OLD).forEach(function(el) { el.style.clipPath = clipOld; });
      handle.style.left = pos + '%';
      handle.setAttribute('aria-valuenow', Math.round(pos));
    }
    apply(pos);

    // ---- divider drag: HANDLE ONLY (pointer capture isolates it) ----
    let dragging = false;
    let dragRect = null;      // stage rect cached at pointerdown — avoids getBoundingClientRect() on every pointermove
    let sliderRaf = null;
    let pendingX = 0;

    function posFromX(clientX) {
      const r = dragRect || stage.getBoundingClientRect();
      if (r.width <= 0) return pos;
      return ((clientX - r.left) / r.width) * 100;
    }
    // During drag, position the handle via transform (compositor) so the
    // browser never triggers layout for the handle's left property.
    handle.addEventListener('pointerdown', function(e) {
      dragging = true;
      dragRect = stage.getBoundingClientRect();
      stage.classList.add('is-dragging');
      if (e.pointerId != null && handle.setPointerCapture) {
        try { handle.setPointerCapture(e.pointerId); } catch (_) {}
      }
      e.preventDefault();
      e.stopPropagation();
    });
    handle.addEventListener('pointermove', function(e) {
      if (!dragging) return;
      pendingX = e.clientX;
      if (sliderRaf !== null) return;
      sliderRaf = requestAnimationFrame(function() {
        sliderRaf = null;
        apply(posFromX(pendingX));
      });
    });
    function endDrag() {
      if (!dragging) return;
      dragging = false;
      dragRect = null;
      stage.classList.remove('is-dragging');
    }
    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);
    handle.addEventListener('keydown', function(e) {
      let step = 0;
      switch (e.key) {
        case 'ArrowLeft': case 'ArrowDown': step = -2; break;
        case 'ArrowRight': case 'ArrowUp': step = 2; break;
        case 'PageDown': step = -10; break;
        case 'PageUp': step = 10; break;
        case 'Home': apply(0); e.preventDefault(); return;
        case 'End': apply(100); e.preventDefault(); return;
        default: return;
      }
      apply(pos + step);
      e.preventDefault();
    });

    // ---- magnifier lens (Zoom mode) ----
    let loupeMode = false;
    let pinned = false;
    let lensMarkers = [];          // cloned marker SVGs (trees-old/new, camps)
    let lensR = LENS_PX / 2;       // lens radius — derived from data-lens attr,
                                   // never read from DOM to avoid layout reflow
    let rafId = null;              // RAF handle for move throttling
    let pendingCx = 0, pendingCy = 0;
    function buildLensMarkers() {
      if (!lensOk || lensMarkers.length || !markerSvgs.length) return;
      markerSvgs.forEach(function(svg) {
        const clone = svg.cloneNode(true);   // keeps its clip + toggle classes
        clone.classList.add('tc-lens-markers');
        clone.removeAttribute('aria-hidden');
        lens.insertBefore(clone, lensRim || null);
        lensMarkers.push(clone);
      });
    }
    function sizeLens() {
      if (!lensOk) return;
      const w = stage.getBoundingClientRect().width * ZOOM;
      [lensOld, lensNew].concat(lensMarkers).forEach(function(el) {
        if (el) { el.style.width = w + 'px'; el.style.height = w + 'px'; }
      });
      if (loupeMode) { fitSrc(lensOld, w); fitSrc(lensNew, w); }
      // lensR is fixed (derived from data-lens); no DOM read needed here.
    }
    function placeLens(cx, cy) {
      if (!lensOk) return;
      lens.style.transform = 'translate(' + (cx - lensR) + 'px,' + (cy - lensR) + 'px)';
      const tf = 'translate(' + (lensR - cx * ZOOM) + 'px,' + (lensR - cy * ZOOM) + 'px)';
      lensOld.style.transform = tf;
      lensNew.style.transform = tf;
      lensMarkers.forEach(function(el) { el.style.transform = tf; });
    }
    // RAF-throttled wrapper: coalesces rapid pointermove events to one
    // placeLens call per animation frame, preventing layout thrashing.
    function schedulePlaceLens(cx, cy) {
      pendingCx = cx; pendingCy = cy;
      if (rafId !== null) return;
      rafId = requestAnimationFrame(function() {
        rafId = null;
        placeLens(pendingCx, pendingCy);
      });
    }
    function localXY(e) {
      const r = stage.getBoundingClientRect();
      return [e.clientX - r.left, e.clientY - r.top];
    }
    // Over the handle → no lens (so you can grab it with a normal cursor). The
    // layer toggles now live ABOVE the stage, so they never overlap the map.
    function overControls(e) {
      return !!(e.target.closest && e.target.closest('.tc-handle'));
    }
    function hideLens() { if (lensOk) lens.classList.remove('visible'); }

    if (lensOk) {
      stage.addEventListener('pointermove', function(e) {
        if (!loupeMode || pinned || dragging || e.pointerType === 'touch') return;
        if (overControls(e)) { hideLens(); return; }
        const xy = localXY(e);
        lens.classList.add('visible');
        schedulePlaceLens(xy[0], xy[1]);
      });
      stage.addEventListener('pointerleave', function() { if (!pinned) hideLens(); });
      stage.addEventListener('click', function(e) {
        if (!loupeMode || dragging || overControls(e)) return;
        const xy = localXY(e);
        pinned = !pinned;
        stage.classList.toggle('lens-pinned', pinned);
        lens.classList.add('visible');
        placeLens(xy[0], xy[1]);
      });
      window.addEventListener('resize', sizeLens);
    }

    // ---- top-bar toggle buttons (aria-pressed) ----
    function pressed(btn) { return btn.getAttribute('aria-pressed') === 'true'; }
    function setPressed(btn, on) { btn.setAttribute('aria-pressed', on ? 'true' : 'false'); }

    // Zoom (magnifier mode)
    const zoomBtn = root.querySelector('.tc-btn-zoom');
    if (zoomBtn && lensOk) {
      zoomBtn.addEventListener('click', function() {
        loupeMode = !loupeMode;
        root.classList.toggle('loupe-on', loupeMode);
        setPressed(zoomBtn, loupeMode);
        if (loupeMode) {
          buildLensMarkers();
          sizeLens();
        } else {
          pinned = false;
          stage.classList.remove('lens-pinned');
          hideLens();
        }
      });
    }

    // ---- POWER RUNE cycling: a power-rune spot can roll any of the 7 runes, so
    // while the Power layer is ON its map markers cycle through tc_rune_0..6
    // every 3s. The toolbar button keeps tc_power.png: our power-rune icon, a bunch
    // of three runes (owner 2026-10-28; it was a random rune). ----
    const RUNE_BASE = 'icons/ui/gothic/tc_rune_';
    const RUNE_COUNT = 7;
    let powerTimer = null, powerIdx = 0;
    function setRune(i) {
      const src = RUNE_BASE + i + '.png';
      root.querySelectorAll('.tm-layer-power image').forEach(function(im) {
        im.setAttribute('href', src);
        im.setAttribute('xlink:href', src);   // older SVG href
      });
    }
    function togglePowerCycle(on) {
      if (powerTimer) { clearInterval(powerTimer); powerTimer = null; }
      if (!on) return;
      setRune(powerIdx);
      powerTimer = setInterval(function() {
        powerIdx = (powerIdx + 1) % RUNE_COUNT;
        setRune(powerIdx);
      }, 3000);
    }

    // Layer toggles — both in .tc-controls-bar and .tc-fs-bar; keep in sync.
    // data-layer="all" turns every layer on (or all off when all are on already)
    // and stays pressed exactly while every layer is on.
    const layerKeys = [];
    root.querySelectorAll('.tc-controls-bar .tc-layer-btn').forEach(function(b) {
      if (b.dataset.layer !== 'all') layerKeys.push(b.dataset.layer);
    });
    function setLayer(key, on) {
      root.querySelectorAll('.tc-layer-btn[data-layer="' + key + '"]')
        .forEach(function(b) { setPressed(b, on); });
      root.classList.toggle('show-' + key, on);
      if (key === 'power') togglePowerCycle(on);
    }
    function syncAllBtn() {
      const allOn = layerKeys.length > 0 && layerKeys.every(function(k) {
        return root.classList.contains('show-' + k);
      });
      root.querySelectorAll('.tc-layer-btn[data-layer="all"]')
        .forEach(function(b) { setPressed(b, allOn); });
    }
    root.querySelectorAll('.tc-layer-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const on = !pressed(btn);
        if (btn.dataset.layer === 'all') layerKeys.forEach(function(k) { setLayer(k, on); });
        else setLayer(btn.dataset.layer, on);
        syncAllBtn();
      });
    });

    // ---- Fullscreen: pan (right-drag) + zoom (wheel) ----
    // Zoom changes stage CSS width (aspect-ratio 1:1 sets height) so the
    // browser rasterises at full res — no blurry GPU scale().
    // Pan uses absolute left/top on the stage.
    var fsBtn = root.querySelector('.tc-btn-fs');
    var fsExitBtn = root.querySelector('.tc-btn-fs-exit');
    var fsCanvas = root.querySelector('.tc-fs-canvas');
    var pane = root.closest('.terrain-map-pane');
    var fsActive = false;
    var fsPanning = false, fsPanStartX = 0, fsPanStartY = 0;
    var fsPanBaseL = 0, fsPanBaseT = 0;
    var fsBaseW = 0;
    var fsRaf = null;

    function fsGetL() { return parseFloat(stage.style.left) || 0; }
    function fsGetT() { return parseFloat(stage.style.top)  || 0; }

    // ---- Fullscreen zoom tiles: once a picture pixel would be drawn bigger than a
    // screen pixel, 512-px tiles of an 8192 picture (data-tiles-old / -new, from
    // Oldgrowth — scripts/gen/map_tiles.py) cover the visible part of each picture.
    // Only the tiles in view are fetched; the 4096 picture shows until they land. ----
    var TILE_GRID = 16, BASE_PX = 4096;
    var tileSets = [];
    [['Old', stage, '.tc-old'], ['New', root.querySelector('.tc-new-layer'), '.tc-new']].forEach(function(p) {
      var base = root.dataset['tiles' + p[0]];
      var host = p[1];
      if (!base || !host) return;
      var box = document.createElement('div');
      box.className = 'tc-tiles';
      box.style.display = 'none';
      var img = host.querySelector(p[2]);
      host.insertBefore(box, img ? img.nextSibling : host.firstChild);
      tileSets.push({ base: base, box: box, have: {} });
    });
    function updateTiles() {
      var w = parseFloat(stage.style.width) || 0;
      if (fsActive && w) fitBase(w);
      if (!tileSets.length) return;
      var on = fsActive && w * (window.devicePixelRatio || 1) > BASE_PX * 1.05;
      tileSets.forEach(function(t) { t.box.style.display = on ? '' : 'none'; });
      if (!on) return;
      var sr = stage.getBoundingClientRect(), cr = fsCanvas.getBoundingClientRect();
      var cw = sr.width / TILE_GRID, ch = sr.height / TILE_GRID;
      var c0 = Math.max(0, Math.floor((cr.left - sr.left) / cw));
      var c1 = Math.min(TILE_GRID - 1, Math.floor((cr.right - sr.left) / cw));
      var r0 = Math.max(0, Math.floor((cr.top - sr.top) / ch));
      var r1 = Math.min(TILE_GRID - 1, Math.floor((cr.bottom - sr.top) / ch));
      tileSets.forEach(function(t) {
        for (var r = r0; r <= r1; r++) {
          for (var c = c0; c <= c1; c++) {
            var k = r + '_' + c;
            if (t.have[k]) continue;
            var im = document.createElement('img');
            im.className = 'tc-tile';
            im.alt = '';
            im.draggable = false;
            im.decoding = 'async';
            im.style.left = (c * 100 / TILE_GRID) + '%';
            im.style.top = (r * 100 / TILE_GRID) + '%';
            im.src = t.base + k + '.webp';
            t.box.appendChild(im);
            t.have[k] = true;
          }
        }
      });
    }

    function fsEnter() {
      if (!pane) return;
      var req = pane.requestFullscreen || pane.webkitRequestFullscreen;
      if (req) req.call(pane);
    }
    function fsExit() {
      var ex = document.exitFullscreen || document.webkitExitFullscreen;
      if (ex) ex.call(document);
    }
    function onFullscreenChange() {
      var el = document.fullscreenElement || document.webkitFullscreenElement;
      if (el === pane) {
        if (loupeMode && zoomBtn) {
          loupeMode = false;
          root.classList.remove('loupe-on');
          setPressed(zoomBtn, false);
          pinned = false;
          stage.classList.remove('lens-pinned');
          hideLens();
        }
        pane.classList.add('tc-fs-active');
        fsActive = true;
        stage.style.transform = '';
        setTimeout(function() {
          var cr = fsCanvas.getBoundingClientRect();
          fsBaseW = cr.width;
          stage.style.width = fsBaseW + 'px';
          stage.style.left = '0px';
          stage.style.top = ((cr.height - fsBaseW) / 2) + 'px';
          updateTiles();
        }, 60);
      } else if (fsActive) {
        pane.classList.remove('tc-fs-active');
        stage.style.width = '';
        stage.style.left = '';
        stage.style.top = '';
        stage.style.transform = '';
        fsActive = false;
        updateTiles();
      }
    }
    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', onFullscreenChange);

    if (fsBtn) fsBtn.addEventListener('click', fsEnter);
    if (fsExitBtn) fsExitBtn.addEventListener('click', fsExit);

    // The fullscreen panel folds to a strip and back (the owner 2026-10-03: "opens and
    // closes"); the map keeps its place against the canvas centre as the canvas widens.
    var fspToggle = root.querySelector('.tc-fsp-toggle');
    if (fspToggle && fsCanvas) fspToggle.addEventListener('click', function() {
      var before = fsCanvas.getBoundingClientRect().width;
      var closed = root.classList.toggle('tc-fsp-closed');
      var label = closed ? 'Show the panel' : 'Hide the panel';
      fspToggle.setAttribute('aria-expanded', closed ? 'false' : 'true');
      fspToggle.setAttribute('aria-label', label);
      fspToggle.title = label;
      if (!fsActive) return;
      requestAnimationFrame(function() {
        var after = fsCanvas.getBoundingClientRect().width;
        stage.style.left = (fsGetL() + (after - before) / 2) + 'px';
        updateTiles();
      });
    });

    if (fsCanvas) {
      fsCanvas.addEventListener('contextmenu', function(e) {
        if (fsActive) e.preventDefault();
      });
      fsCanvas.addEventListener('mousedown', function(e) {
        if (e.button !== 2 || !fsActive) return;
        fsPanning = true;
        fsPanStartX = e.clientX; fsPanStartY = e.clientY;
        fsPanBaseL = fsGetL(); fsPanBaseT = fsGetT();
        fsCanvas.classList.add('is-panning');
        e.preventDefault();
      });
      window.addEventListener('mousemove', function(e) {
        if (!fsPanning) return;
        var nl = fsPanBaseL + (e.clientX - fsPanStartX);
        var nt = fsPanBaseT + (e.clientY - fsPanStartY);
        if (fsRaf) return;
        fsRaf = requestAnimationFrame(function() {
          fsRaf = null;
          stage.style.left = nl + 'px';
          stage.style.top  = nt + 'px';
          updateTiles();
        });
      });
      window.addEventListener('mouseup', function(e) {
        if (e.button === 2 && fsPanning) {
          fsPanning = false;
          fsCanvas.classList.remove('is-panning');
        }
      });
      fsCanvas.addEventListener('wheel', function(e) {
        if (!fsActive) return;
        e.preventDefault();
        var curW = parseFloat(stage.style.width) || fsBaseW;
        var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
        var newW = Math.max(fsBaseW * 0.5, Math.min(fsBaseW * 8, curW * factor));
        var ratio = newW / curW;
        var cr = fsCanvas.getBoundingClientRect();
        var mx = e.clientX - cr.left;
        var my = e.clientY - cr.top;
        var oldL = fsGetL(), oldT = fsGetT();
        stage.style.width = newW + 'px';
        stage.style.left = (mx - ratio * (mx - oldL)) + 'px';
        stage.style.top  = (my - ratio * (my - oldT)) + 'px';
        updateTiles();
      }, { passive: false });
    }
  }

  function initSubpatchPicker() {
    document.querySelectorAll('.terrain-list-pane').forEach(function(pane) {
      var ul = pane.querySelector('.terrain-list');
      if (!ul) return;
      var items = [].slice.call(ul.children);
      var topHead = pane.querySelector('.terrain-subpatch-top');
      if (!topHead) return;
      var topVer = topHead.textContent.trim();
      var groups = [];
      var cur = { ver: topVer, items: [] };
      items.forEach(function(li) {
        if (li.classList.contains('terrain-subpatch-head') && !li.classList.contains('terrain-subpatch-top')) {
          groups.push(cur);
          cur = { ver: li.textContent.trim(), items: [] };
          li.classList.add('tsp-hidden');
        } else if (!li.classList.contains('terrain-subpatch-top')) {
          cur.items.push(li);
        }
      });
      groups.push(cur);
      var idx = 0;
      var nav = document.createElement('div');
      nav.className = 'terrain-subpatch-nav';
      var btnL = document.createElement('button');
      btnL.className = 'tsp-arrow tsp-arrow-left';
      btnL.setAttribute('aria-label', 'Newer subpatch');
      // the version is a link to its patch page's terrain notes (the owner 2026-10-03: "click the patch switcher
      // to jump to that patch"); ?from= gives that page a back arrow to this one
      var label = document.createElement('a');
      label.className = 'tsp-label';
      label.textContent = topVer;
      var here = (window.location.pathname.match(/(terrain_[0-9a-z]+)\.html$/) || [])[1];
      function linkTo(ver) {
        label.href = 'patches/' + ver + '.html' + (here ? '?from=' + here : '') + '#terrain';
        label.setAttribute('aria-label', 'Patch ' + ver + ' notes');
      }
      var btnR = document.createElement('button');
      btnR.className = 'tsp-arrow tsp-arrow-right';
      btnR.setAttribute('aria-label', 'Older subpatch');
      nav.appendChild(btnL);
      nav.appendChild(label);
      nav.appendChild(btnR);
      topHead.replaceWith(nav);
      function show(i) {
        idx = i;
        groups.forEach(function(g, gi) {
          var vis = (gi === i);
          g.items.forEach(function(li) {
            if (vis) li.classList.remove('tsp-hidden');
            else li.classList.add('tsp-hidden');
          });
        });
        label.textContent = groups[i].ver;
        linkTo(groups[i].ver);
        // At the ends the arrows step to the neighbouring map page (newer / older terrain
        // pair from the header's version menu) instead of going dead.
        btnL.disabled = (i === 0 && !newerPage);
        btnR.disabled = (i === groups.length - 1 && !olderPage);
        btnL.title = (i === 0 && newerPage) ? 'Go to ' + newerPage.label : '';
        btnR.title = (i === groups.length - 1 && olderPage) ? 'Go to ' + olderPage.label : '';
      }
      // Terrain pages, newest first, as listed in the header version menu.
      var pages = [].slice.call(document.querySelectorAll('.version-dropdown .version-menu a.version-item'));
      var curPage = pages.findIndex(function(a) { return a.classList.contains('current'); });
      function pageAt(k) {
        var a = (curPage >= 0 && k >= 0 && k < pages.length) ? pages[k] : null;
        return a ? { href: a.getAttribute('href'), label: a.textContent.trim() } : null;
      }
      var newerPage = pageAt(curPage - 1);
      var olderPage = pageAt(curPage + 1);
      show(0);
      btnL.addEventListener('click', function() {
        if (idx > 0) show(idx - 1);
        else if (newerPage) window.location.href = newerPage.href;
      });
      btnR.addEventListener('click', function() {
        if (idx < groups.length - 1) show(idx + 1);
        else if (olderPage) window.location.href = olderPage.href;
      });
    });
  }

  // "Changed in the map file" chips: pressed, the changed places are outlined on the map —
  // removed on the old side, added on the new side, moved on both (.tm-hl-<key>, the stage's
  // and the lens's copies alike). A chip turns its map layer on, and its outlines show only
  // while that layer is on (the owner: "taking the Trees filter into account"). The
  // moved / removed / added switches hide a kind of outline (.hl-hide-<kind> on the map).
  function initChangeHighlights() {
    const root = document.querySelector('.terrain-compare');
    if (!root) return;
    // the chips and switches exist twice — under the list and in the fullscreen panel — and
    // every copy of one key / kind shows the same state
    const chips = document.querySelectorAll('.tf-chip-btn[data-hl]');
    function setAll(selector, on) {
      document.querySelectorAll(selector).forEach(function(b) {
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }
    function layerOn(layer) {
      return !layer || root.classList.contains('show-' + layer);
    }
    function refresh() {
      const dim = {}, done = {};
      chips.forEach(function(btn) {
        if (done[btn.dataset.hl]) return;
        done[btn.dataset.hl] = true;
        const on = btn.getAttribute('aria-pressed') === 'true' && layerOn(btn.dataset.layer);
        root.querySelectorAll('.tm-hl-' + btn.dataset.hl).forEach(function(svg) {
          svg.classList.toggle('tm-hl-on', on);
        });
        if (btn.dataset.layer) dim[btn.dataset.layer] = dim[btn.dataset.layer] || on;
      });
      // the layer's own markers step back while its changes are outlined (a green "added"
      // outline would melt into the green tree squares)
      Object.keys(dim).forEach(function(layer) {
        root.querySelectorAll('.tm-layer-' + layer).forEach(function(svg) {
          svg.classList.toggle('tm-dim', dim[layer]);
        });
      });
    }
    // A layer a chip switched on goes off again with the last pressed chip of that layer; one the viewer had on
    // (or touched since) stays (the owner 2026-10-03).
    const autoLayers = {};
    let chipClick = false;
    function pressLayer(layer) {
      const layerBtn = root.querySelector('.tc-controls-bar .tc-layer-btn[data-layer="' + layer + '"]');
      if (!layerBtn) return;
      chipClick = true;
      layerBtn.click();                           // goes through the bar, so its button shows its state
      chipClick = false;
    }
    function layerChipsOn(layer) {
      return Array.prototype.some.call(chips, function(c) {
        return c.dataset.layer === layer && c.getAttribute('aria-pressed') === 'true';
      });
    }
    chips.forEach(function(btn) {
      btn.addEventListener('click', function() {
        const on = btn.getAttribute('aria-pressed') !== 'true';
        setAll('.tf-chip-btn[data-hl="' + btn.dataset.hl + '"]', on);
        const layer = btn.dataset.layer;
        if (layer && on && !layerOn(layer)) {
          pressLayer(layer);
          autoLayers[layer] = true;
        } else if (layer && !on && autoLayers[layer] && !layerChipsOn(layer)) {
          delete autoLayers[layer];
          if (layerOn(layer)) pressLayer(layer);
        }
        refresh();
      });
    });
    // the bar's own layer buttons (and "All") change what the pressed chips may show; a click by the viewer makes
    // the layer theirs
    root.querySelectorAll('.tc-layer-btn').forEach(function(b) {
      b.addEventListener('click', function() {
        if (!chipClick) {
          if (b.dataset.layer && b.dataset.layer !== 'all') delete autoLayers[b.dataset.layer];
          else Object.keys(autoLayers).forEach(function(k) { delete autoLayers[k]; });
        }
        refresh();
      });
    });
    document.querySelectorAll('.tf-kind[data-kind]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const on = btn.getAttribute('aria-pressed') !== 'true';
        setAll('.tf-kind[data-kind="' + btn.dataset.kind + '"]', on);
        root.classList.toggle('hl-hide-' + btn.dataset.kind, !on);
      });
    });
  }

  // Heights: each height a switch (the owner 2026-10-05: "click 0, 128 … to turn those layers on and off").
  // .hband-off-<k> on the map hides band k; the switches exist twice (under the list, in the fullscreen panel) and
  // stay in step. With the Heights layer off, a click turns it on showing just that height.
  function initHeightBands() {
    const root = document.querySelector('.terrain-compare');
    const btns = document.querySelectorAll('.tf-hband[data-hband]');
    if (!root || !btns.length) return;
    function setBand(k, on) {
      document.querySelectorAll('.tf-hband[data-hband="' + k + '"]').forEach(function(b) {
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      root.classList.toggle('hband-off-' + k, !on);
    }
    btns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        const k = btn.dataset.hband;
        if (!root.classList.contains('show-heights')) {
          btns.forEach(function(b) { setBand(b.dataset.hband, b.dataset.hband === k); });
          const layerBtn = root.querySelector('.tc-controls-bar .tc-layer-btn[data-layer="heights"]');
          if (layerBtn) layerBtn.click();
          return;
        }
        setBand(k, btn.getAttribute('aria-pressed') !== 'true');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTerrainCompare();
      initSubpatchPicker();
      initChangeHighlights();
      initHeightBands();
    });
  } else {
    initTerrainCompare();
    initSubpatchPicker();
    initChangeHighlights();
    initHeightBands();
  }
})();
