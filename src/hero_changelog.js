/** hero_changelog.js — client-side rendering for the Hero Changelog page.
 *
 *  Reads the embedded <script id="hc-data"> JSON and renders:
 *  - Sidebar: searchable hero list with icons and change counts
 *  - Main panel: chronological change log for the selected hero
 *
 *  Tag badge styles reuse the global .badge classes from styles.css.
 *  Ability icons reuse the CDN path pattern from the patch pages.
 */
(function () {
  "use strict";

  var DATA_EL = document.getElementById("hc-data");
  if (!DATA_EL) return;
  var DATA;
  try { DATA = JSON.parse(DATA_EL.textContent); } catch (e) { return; }

  var HERO_LIST = document.getElementById("hc-hero-list");
  var MAIN = document.getElementById("hc-main");
  var EMPTY = document.getElementById("hc-empty");
  var CHANGES = document.getElementById("hc-changes");
  var SEARCH = document.getElementById("hc-search");
  if (!HERO_LIST || !MAIN || !EMPTY || !CHANGES || !SEARCH) return;

  var HERO_CDN = "icons/heroes/";
  var ABIL_CDN = "icons/abilities/";
  var INNATE_ICON = "icons/misc/innate_icon.png";
  var TALENT_ICON = "icons/misc/talents.svg";
  var OTHER_ICON = "icons/other.svg";
  var MISSING_ICON = "icons/misc/missing.svg";

  var TAG_CLASSES = {
    buff: "buff-text",
    nerf: "nerf-text",
    new: "new",
    del: "del",
    rework: "rework",
    misc: "misc",
    qol: "qol",
  };
  var TAG_LABELS = {
    buff: "BUFF",
    nerf: "NERF",
    new: "NEW",
    del: "DEL",
    rework: "REWORK",
    misc: "MISC",
    qol: "QoL",
  };

  function esc(s) {
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  /** Build the badge HTML for a tag. */
  function badge(tag) {
    var cls = TAG_CLASSES[tag] || "misc";
    var label = TAG_LABELS[tag] || tag.toUpperCase();
    return '<span class="badge ' + esc(cls) + '">' + esc(label) + '</span>';
  }

  /** Build the percentage direction badge. */
  function pctBadge(change) {
    var oldV = change.old;
    var newV = change.new;
    if (oldV === undefined || newV === undefined) return "";
    var o = typeof oldV === "number" ? oldV : (Array.isArray(oldV) ? oldV[0] : null);
    var n = typeof newV === "number" ? newV : (Array.isArray(newV) ? newV[0] : null);
    if (o === null || n === null) return "";
    var diff = n - o;
    if (diff === 0) return '<span class="stat-pct flat">0%</span>';
    var isUp = diff > 0;
    if (change.lower_is_better) isUp = diff < 0;
    var pct = o !== 0 ? Math.abs(diff / o * 100).toFixed(0) : "∞";
    var cls = isUp ? "up" : "down";
    var sign = isUp ? "+" : "";
    return '<span class="stat-pct ' + cls + '">' + sign + pct + "%</span>";
  }

  /** Build one change <li> matching patch-page grid layout:
   *  badge + row-text + optional percentage badge. */
  function changeLi(change) {
    var tag = change.tag || "misc";
    var text = esc(change.text || "");
    var pct = pctBadge(change);
    return '<li>' + badge(tag) + '<span class="row-text">' + text + '</span>'
      + (pct ? '<span class="badge-group" data-overall="' + esc(tag) + '">' + pct + '</span>' : '')
      + '</li>';
  }

  /** Build an ability-block (icon + title + ul.changes) matching patch-page HTML. */
  function abilityBlock(abilityName, abilitySlug, changes) {
    var iconHtml = '';
    if (abilitySlug) {
      var src = ABIL_CDN + esc(abilitySlug) + ".png";
      iconHtml = '<div class="ability-icon-wrap">'
        + '<img decoding="async" src="' + src + '" alt="' + esc(abilityName) + '" '
        + 'class="ability-icon-img" loading="lazy" width="48" height="48" '
        + 'onerror="this.onerror=function(){this.style.display=\'none\'};'
        + 'this.src=\'' + MISSING_ICON + '\';'
        + 'this.title=\'missing icon: ' + esc(abilitySlug) + '\';">'
        + '</div>';
    } else {
      // Determine default icon from ability name
      var nameLower = abilityName.toLowerCase();
      var defaultIcon = '';
      if (nameLower === 'talents') {
        defaultIcon = TALENT_ICON;
      } else if (nameLower === 'base stats' || nameLower === 'general') {
        defaultIcon = OTHER_ICON;
      }
      if (defaultIcon) {
        iconHtml = '<div class="ability-icon-wrap">'
          + '<img decoding="async" src="' + defaultIcon + '" alt="" '
          + 'class="ability-icon-img" loading="lazy" width="48" height="48">'
          + '</div>';
      } else {
        iconHtml = '<div class="ability-icon-wrap"></div>';
      }
    }
    var lis = '';
    for (var k = 0; k < changes.length; k++) {
      lis += changeLi(changes[k]);
    }
    return '<div class="ability-block hc-abil-block">'
      + iconHtml
      + '<h4 class="ability-title">' + esc(abilityName) + '</h4>'
      + '<ul class="changes">' + lis + '</ul>'
      + '</div>';
  }

  /** Render the full change list for one hero. */
  function renderHero(hero) {
    if (!hero.patches || hero.patches.length === 0) {
      return '<div class="hc-no-data">No structured data available for this hero yet.</div>';
    }

    var html = '<div class="hc-hero-header">';
    html += '<img class="hc-hero-icon" src="' + HERO_CDN + esc(hero.icon) + '.png" '
      + 'alt="' + esc(hero.name) + '" loading="lazy">';
    html += '<div class="hc-hero-info">';
    html += '<h2 class="hc-hero-name">' + esc(hero.name) + '</h2>';
    html += '<div class="hc-hero-summary">'
      + hero.total_changes + ' changes across ' + hero.patches.length + ' patches'
      + '</div>';
    html += '</div></div>';

    // Render patches in reverse chronological order (newest first)
    var patches = hero.patches.slice().reverse();
    for (var i = 0; i < patches.length; i++) {
      var p = patches[i];
      html += '<div class="hc-patch">';
      html += '<div class="hc-patch-header">';
      html += '<span class="hc-patch-version">' + esc(p.patch) + '</span>';
      if (p.date) {
        html += '<span class="hc-patch-date">' + esc(p.date) + '</span>';
      }
      var filename = p.patch.toLowerCase().replace(/\./g, "") + ".html";
      html += '<a class="hc-patch-link" href="patches/' + esc(filename)
        + '" title="Open full patch page">↗</a>';
      html += '</div>';

      // Group changes by scope (ability name)
      var groups = {};       // scope → [change, ...]
      var groupOrder = [];   // first-seen order
      var baseChanges = [];  // scope == "base" or ""
      var talentChanges = []; // scope == "talent"
      for (var j = 0; j < p.changes.length; j++) {
        var ch = p.changes[j];
        var sc = ch.scope || "";
        if (sc === "base" || sc === "") {
          baseChanges.push(ch);
        } else if (sc === "talent") {
          talentChanges.push(ch);
        } else if (sc.indexOf("facet:") === 0) {
          // Facet changes — group under facet name
          if (!groups[sc]) { groups[sc] = []; groupOrder.push(sc); }
          groups[sc].push(ch);
        } else {
          // Ability changes
          if (!groups[sc]) { groups[sc] = []; groupOrder.push(sc); }
          groups[sc].push(ch);
        }
      }

      // Base / talent first (no icon, use subgroup-style heading)
      if (baseChanges.length) {
        html += abilityBlock("Base Stats", null, baseChanges);
      }
      if (talentChanges.length) {
        html += abilityBlock("Talents", null, talentChanges);
      }

      // Then each ability / facet group
      for (var g = 0; g < groupOrder.length; g++) {
        var gname = groupOrder[g];
        var gchanges = groups[gname];
        // Find the ability_slug from first change that has one
        var aslug = null;
        for (var c = 0; c < gchanges.length; c++) {
          if (gchanges[c].ability_slug) { aslug = gchanges[c].ability_slug; break; }
        }
        var displayName = gname.indexOf("facet:") === 0 ? gname.slice(6) : gname;
        html += abilityBlock(displayName, aslug, gchanges);
      }

      html += '</div>';
    }
    return html;
  }

  /** Populate the hero list sidebar. */
  function buildHeroList(filter) {
    var heroes = DATA.heroes || [];
    var lower = (filter || "").toLowerCase();
    var parts = [];
    for (var i = 0; i < heroes.length; i++) {
      var h = heroes[i];
      if (lower) {
        if (h.name.toLowerCase().indexOf(lower) === -1 &&
            h.slug.indexOf(lower) === -1) {
          continue;
        }
      }
      var count = h.total_changes || 0;
      var countCls = count > 0 ? "hc-hero-count" : "hc-hero-count hc-hero-zero";
      parts.push(
        '<div class="hc-hero-row" data-slug="' + esc(h.slug) + '">'
        + '<img class="hc-hero-thumb" src="' + HERO_CDN + esc(h.icon) + '.png" '
        + 'alt="" loading="lazy">'
        + '<span class="hc-hero-label">' + esc(h.name) + '</span>'
        + '<span class="' + countCls + '">' + count + '</span>'
        + '</div>'
      );
    }
    HERO_LIST.innerHTML = parts.join("");
  }

  /** Select a hero and render their changes. */
  function selectHero(slug) {
    var heroes = DATA.heroes || [];
    var hero = null;
    for (var i = 0; i < heroes.length; i++) {
      if (heroes[i].slug === slug) { hero = heroes[i]; break; }
    }
    if (!hero) return;

    // Update active row
    var rows = HERO_LIST.querySelectorAll(".hc-hero-row");
    for (var j = 0; j < rows.length; j++) {
      rows[j].classList.toggle("active", rows[j].getAttribute("data-slug") === slug);
    }

    EMPTY.hidden = true;
    CHANGES.hidden = false;
    CHANGES.innerHTML = renderHero(hero);
    // Scroll to top of main panel
    MAIN.scrollTop = 0;
  }

  // --- Init ---
  buildHeroList("");

  // Hero list click
  HERO_LIST.addEventListener("click", function (e) {
    var row = e.target.closest(".hc-hero-row");
    if (!row) return;
    selectHero(row.getAttribute("data-slug"));
  });

  // Search
  var searchTimer;
  SEARCH.addEventListener("input", function () {
    clearTimeout(searchTimer);
    var val = SEARCH.value;
    searchTimer = setTimeout(function () {
      buildHeroList(val);
    }, 150);
  });

  // Keyboard navigation in search
  SEARCH.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      SEARCH.value = "";
      buildHeroList("");
      SEARCH.blur();
      return;
    }
    if (e.key === "Enter") {
      // Select the first visible hero
      var first = HERO_LIST.querySelector(".hc-hero-row");
      if (first) selectHero(first.getAttribute("data-slug"));
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var rows = HERO_LIST.querySelectorAll(".hc-hero-row");
      if (!rows.length) return;
      var active = HERO_LIST.querySelector(".hc-hero-row.active");
      var idx = -1;
      for (var i = 0; i < rows.length; i++) {
        if (rows[i] === active) { idx = i; break; }
      }
      if (e.key === "ArrowDown") {
        idx = Math.min(idx + 1, rows.length - 1);
      } else {
        idx = Math.max(idx - 1, 0);
      }
      selectHero(rows[idx].getAttribute("data-slug"));
      rows[idx].scrollIntoView({ block: "nearest" });
    }
  });

  // URL hash deep-link: hero_changelog.html#spectre
  var hash = location.hash.replace("#", "");
  if (hash) {
    selectHero(hash);
  }

})();
