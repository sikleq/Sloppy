"""Patch metadata: PATCHES list, RELEASE_HISTORY, date helpers, nav rendering."""

import datetime
import site_common as _site

PATCHES = [
    {"version": "7.41d", "date": "04.06.2026", "filename": "patches/7.41d.html"},
    {"version": "7.41c", "date": "06.05.2026", "filename": "patches/7.41c.html"},
    {"version": "7.41b", "date": "07.04.2026", "filename": "patches/7.41b.html"},
    {"version": "7.41a", "date": "28.03.2026", "filename": "patches/7.41a.html"},
    {"version": "7.41",  "date": "24.03.2026", "filename": "patches/7.41.html"},
    {"version": "7.40c", "date": "21.01.2026", "filename": "patches/7.40c.html"},
    {"version": "7.40b", "date": "23.12.2025", "filename": "patches/7.40b.html"},
    {"version": "7.40",  "date": "15.12.2025", "filename": "patches/7.40.html"},
    {"version": "7.39e", "date": "02.10.2025", "filename": "patches/7.39e.html"},
    {"version": "7.08",  "date": "01.02.2018", "filename": "patches/7.08.html"},
]

# Includes patches without HTML (e.g. 7.41a) — used only for "days between" math.
# Major-patch dates from odota/dotaconstants. Sub-patches sourced from Liquipedia
# and Fandom. Append new entries here when patches release; sorted internally.
RELEASE_HISTORY = [
    # 7.41 cycle
    {"version": "7.41d", "date": "04.06.2026"},
    {"version": "7.41c", "date": "06.05.2026"},
    {"version": "7.41b", "date": "07.04.2026"},
    {"version": "7.41a", "date": "28.03.2026"},
    {"version": "7.41",  "date": "24.03.2026"},
    # 7.40 cycle
    {"version": "7.40c", "date": "21.01.2026"},
    {"version": "7.40b", "date": "23.12.2025"},
    {"version": "7.40",  "date": "15.12.2025"},
    # 7.39 cycle
    {"version": "7.39e", "date": "02.10.2025"},
    {"version": "7.39d", "date": "05.08.2025"},
    {"version": "7.39c", "date": "24.06.2025"},
    {"version": "7.39b", "date": "29.05.2025"},
    {"version": "7.39",  "date": "21.05.2025"},
    # 7.38 cycle
    {"version": "7.38c", "date": "27.03.2025"},
    {"version": "7.38b", "date": "05.03.2025"},
    {"version": "7.38",  "date": "19.02.2025"},
    # 7.37 cycle
    {"version": "7.37e", "date": "19.11.2024"},
    {"version": "7.37d", "date": "01.10.2024"},
    {"version": "7.37c", "date": "28.08.2024"},
    {"version": "7.37b", "date": "14.08.2024"},
    {"version": "7.37",  "date": "31.07.2024"},
    # 7.36 cycle
    {"version": "7.36c", "date": "24.06.2024"},
    {"version": "7.36b", "date": "05.06.2024"},
    {"version": "7.36a", "date": "26.05.2024"},
    {"version": "7.36",  "date": "22.05.2024"},
    # 7.35 cycle
    {"version": "7.35d", "date": "21.03.2024"},
    {"version": "7.35c", "date": "21.02.2024"},
    {"version": "7.35b", "date": "21.12.2023"},
    {"version": "7.35",  "date": "14.12.2023"},
    # 7.34 cycle
    {"version": "7.34e", "date": "20.11.2023"},
    {"version": "7.34d", "date": "05.10.2023"},
    {"version": "7.34c", "date": "08.09.2023"},
    {"version": "7.34b", "date": "14.08.2023"},
    {"version": "7.34",  "date": "08.08.2023"},
    # 7.33 cycle
    {"version": "7.33e", "date": "13.07.2023"},
    {"version": "7.33d", "date": "15.06.2023"},
    {"version": "7.33c", "date": "13.05.2023"},
    {"version": "7.33b", "date": "25.04.2023"},
    {"version": "7.33",  "date": "20.04.2023"},
    # 7.32 cycle
    {"version": "7.32e", "date": "07.03.2023"},
    {"version": "7.32d", "date": "29.11.2022"},
    {"version": "7.32c", "date": "27.09.2022"},
    {"version": "7.32b", "date": "30.08.2022"},
    {"version": "7.32",  "date": "24.08.2022"},
    # 7.31 cycle
    {"version": "7.31d", "date": "08.06.2022"},
    {"version": "7.31c", "date": "04.05.2022"},
    {"version": "7.31b", "date": "28.02.2022"},
    {"version": "7.31",  "date": "23.02.2022"},
    # 7.30 cycle
    {"version": "7.30e", "date": "28.10.2021"},
    {"version": "7.30d", "date": "25.09.2021"},
    {"version": "7.30c", "date": "11.09.2021"},
    {"version": "7.30b", "date": "23.08.2021"},
    {"version": "7.30",  "date": "18.08.2021"},
    # 7.29 cycle
    {"version": "7.29d", "date": "24.05.2021"},
    {"version": "7.29c", "date": "29.04.2021"},
    {"version": "7.29b", "date": "16.04.2021"},
    {"version": "7.29",  "date": "09.04.2021"},
    # 7.28 cycle
    {"version": "7.28c", "date": "19.02.2021"},
    {"version": "7.28b", "date": "10.01.2021"},
    {"version": "7.28a", "date": "22.12.2020"},
    {"version": "7.28",  "date": "17.12.2020"},
    # 7.27 cycle
    {"version": "7.27d", "date": "26.08.2020"},
    {"version": "7.27c", "date": "17.07.2020"},
    {"version": "7.27b", "date": "15.07.2020"},
    {"version": "7.27a", "date": "04.07.2020"},
    {"version": "7.27",  "date": "28.06.2020"},
    # 7.26 cycle
    {"version": "7.26c", "date": "02.05.2020"},
    {"version": "7.26b", "date": "28.04.2020"},
    {"version": "7.26a", "date": "21.04.2020"},
    {"version": "7.26",  "date": "17.04.2020"},
    # 7.25 cycle
    {"version": "7.25c", "date": "06.04.2020"},
    {"version": "7.25b", "date": "25.03.2020"},
    {"version": "7.25a", "date": "18.03.2020"},
    {"version": "7.25",  "date": "17.03.2020"},
    # 7.24 cycle
    {"version": "7.24b", "date": "26.02.2020"},
    {"version": "7.24",  "date": "26.01.2020"},
    # 7.23 cycle
    {"version": "7.23f", "date": "07.01.2020"},
    {"version": "7.23e", "date": "14.12.2019"},
    {"version": "7.23d", "date": "11.12.2019"},
    {"version": "7.23c", "date": "06.12.2019"},
    {"version": "7.23b", "date": "29.11.2019"},
    {"version": "7.23a", "date": "27.11.2019"},
    {"version": "7.23",  "date": "26.11.2019"},
    # 7.22 cycle
    {"version": "7.22h", "date": "29.09.2019"},
    {"version": "7.22g", "date": "06.09.2019"},
    {"version": "7.22f", "date": "28.07.2019"},
    {"version": "7.22e", "date": "14.07.2019"},
    {"version": "7.22d", "date": "30.06.2019"},
    {"version": "7.22c", "date": "09.06.2019"},
    {"version": "7.22b", "date": "27.05.2019"},
    {"version": "7.22",  "date": "24.05.2019"},
    # 7.21 cycle
    {"version": "7.21d", "date": "24.03.2019"},
    {"version": "7.21c", "date": "02.03.2019"},
    {"version": "7.21b", "date": "16.02.2019"},
    {"version": "7.21",  "date": "29.01.2019"},
    # 7.20 cycle
    {"version": "7.20e", "date": "09.12.2018"},
    {"version": "7.20d", "date": "30.11.2018"},
    {"version": "7.20c", "date": "24.11.2018"},
    {"version": "7.20b", "date": "20.11.2018"},
    {"version": "7.20",  "date": "19.11.2018"},
    # 7.19 cycle
    {"version": "7.19d", "date": "12.10.2018"},
    {"version": "7.19c", "date": "14.09.2018"},
    {"version": "7.19b", "date": "01.09.2018"},
    {"version": "7.19",  "date": "29.07.2018"},
    # 7.08-7.18 (Spring Cleaning era)
    {"version": "7.18",  "date": "25.06.2018"},
    {"version": "7.17",  "date": "10.06.2018"},
    {"version": "7.16",  "date": "27.05.2018"},
    {"version": "7.15",  "date": "10.05.2018"},
    {"version": "7.14",  "date": "26.04.2018"},
    {"version": "7.13b", "date": "13.04.2018"},
    {"version": "7.13",  "date": "12.04.2018"},
    {"version": "7.12",  "date": "29.03.2018"},
    {"version": "7.11",  "date": "15.03.2018"},
    {"version": "7.10",  "date": "01.03.2018"},
    {"version": "7.09",  "date": "15.02.2018"},
    {"version": "7.08",  "date": "01.02.2018"},
]


def _parse_date(dmy):
    """'06.05.2026' → date(2026, 5, 6)."""
    from datetime import date as _D
    d, m, y = dmy.split('.')
    return _D(int(y), int(m), int(d))


def _patch_meta_parts(version):
    """Return (prev_part, age_part) — two short labelled strings used by the
    toolbar patch-info row.

    prev_part  →  "+29 days after 7.41b"   (empty if no previous patch)
    age_part   →  "Live 25 days"  on the newest patch,
                  "Ran 29 days"   on every older one.
    """
    from datetime import date as _D
    today = _D.today()
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] != version:
            continue
        cur_date = _parse_date(p["date"])
        prev_part = ""
        # Static words carry data-i18n so the client toggle can translate them;
        # the RU "дн." abbreviation sidesteps the 3-way Russian day plural.
        if i > 0:
            prev = sorted_releases[i - 1]
            n = (cur_date - _parse_date(prev["date"])).days
            prev_part = (f'<b>{n}</b> <span data-i18n="patch.days_after">days after</span> '
                         f'<b>{prev["version"]}</b>')
        if i < len(sorted_releases) - 1:
            nxt = sorted_releases[i + 1]
            n = (_parse_date(nxt["date"]) - cur_date).days
            age_part = (f'<span data-i18n="patch.ran">Ran:</span> <b>{n}</b> '
                        f'<span data-i18n="patch.days">days</span>')
        else:
            n = (today - cur_date).days
            unit = "day" if n == 1 else "days"
            age_part = (f'<span data-i18n="patch.live">Live:</span> <b>{n}</b> '
                        f'<span data-i18n="patch.days">{unit}</span>' if n > 0
                        else '<span data-i18n="patch.released_today">Released today</span>')
        return prev_part, age_part
    return "", ""


def _patch_age_line(version):
    """Build the small subtitle under the release date.

    For latest patch:   "29 days after 7.41b · running for 2 days"
    For older patches:  "10 days after 7.41a · ran for 29 days"
    Returns empty string if previous patch unknown.
    """
    from datetime import date as _D
    today = _D.today()
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] != version:
            continue
        cur_date = _parse_date(p["date"])
        prev_part = ""
        if i > 0:
            prev = sorted_releases[i - 1]
            n = (cur_date - _parse_date(prev["date"])).days
            prev_part = f"{n} days after {prev['version']}"
        if i < len(sorted_releases) - 1:
            nxt = sorted_releases[i + 1]
            n = (_parse_date(nxt["date"]) - cur_date).days
            tail = f"ran for {n} days"
        else:
            n = (today - cur_date).days
            unit = "day" if n == 1 else "days"
            tail = f"running for {n} {unit}" if n > 0 else "released today"
        return f"{prev_part} · {tail}" if prev_part else tail
    return ""


def _dropdown_options_html(current_version, patch_context=False):
    """Render menu items list for the version dropdown.
    patch_context=True when rendered inside a patch page (patches/ folder) —
    links use plain 'version.html' (same directory) instead of root-relative paths."""
    items = []
    for p in PATCHES:
        cls = "version-item current" if p["version"] == current_version else "version-item"
        if p["version"] == current_version:
            href = "#"
        elif patch_context:
            href = p["version"] + ".html"
        else:
            href = p["filename"]
        items.append(
            f'<a class="{cls}" href="{href}">'
            f'<span class="vi-name">{p["version"]}</span>'
            f'<span class="vi-date">{p["date"]}</span>'
            f'</a>'
        )
    return "".join(items)


def _render_top_nav(active="changelogs", current_version=None, date=None, patch_context=False, centre_tabs=True):
    """Render the top nav by delegating to site_common.render_top_nav. This
    wrapper builds the patch-page version picker (prev/next arrows + version
    dropdown + release-info) and passes it as picker_html; the shared module
    owns the tab list and the flat-tab placeholder."""
    latest_href = (PATCHES[0]['version'] + ".html" if patch_context
                   else PATCHES[0]['filename']) if PATCHES else "#"

    picker_html = None
    show_picker = (active == "changelogs"
                   and current_version is not None and date is not None)
    if show_picker:
        age_line = _patch_age_line(current_version)
        age_html = f'<span class="patch-age">{age_line}</span>' if age_line else ''
        options = _dropdown_options_html(current_version, patch_context=patch_context)
        # Prev/Next arrows flanking the version button — let the user
        # walk one step backward / forward through the patch list
        # without opening the dropdown. PATCHES is sorted newest-first,
        # so older = idx+1 (left arrow) and newer = idx-1 (right arrow).
        idx = next((i for i, p in enumerate(PATCHES) if p["version"] == current_version), None)
        older = PATCHES[idx + 1] if idx is not None and idx + 1 < len(PATCHES) else None
        newer = PATCHES[idx - 1] if idx is not None and idx - 1 >= 0 else None

        def _nav_arrow(target, direction):
            # Direction-modifier class drives the clip-path arrow shape
            # in CSS. The element renders without any text glyph — the
            # block itself is the arrow.
            dir_cls = 'is-prev' if direction == 'Older' else 'is-next'
            if target:
                return (f'<a class="version-nav-arrow {dir_cls}" '
                        f'href="{target["filename"].split("/")[-1]}" '
                        f'title="{direction}: {target["version"]} ({target["date"]})" '
                        f'aria-label="{direction} patch: {target["version"]}"></a>')
            return (f'<span class="version-nav-arrow {dir_cls} is-disabled" '
                    f'aria-hidden="true"></span>')

        prev_arrow = _nav_arrow(older, "Older")
        next_arrow = _nav_arrow(newer, "Newer")

        # Patch info (date + age) was previously in this header block — it has
        # moved to the .toolbar below so the header stays compact. Only the
        # arrows + version dropdown remain on the right.
        picker_html = f'''
    <div class="nav-context nav-context-picker">
      <div class="version-picker">
        {prev_arrow}
        <div class="version-dropdown">
          <button class="version" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Select patch version" data-i18n-aria-label="patch.select_version">
            {current_version} <span class="version-chev">▾</span>
          </button>
          <div class="version-menu" role="menu">
            {options}
          </div>
        </div>
        {next_arrow}
      </div>
    </div>'''

    return _site.render_top_nav(active, latest_href,
                                patch_context=patch_context,
                                picker_html=picker_html,
                                centre_tabs=centre_tabs)


def _current_version():
    """Return version string of the most recently released patch."""
    if not RELEASE_HISTORY:
        return None
    return sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))[-1]["version"]


def _prev_patch_version(version):
    """Return the version string of the patch before `version` in RELEASE_HISTORY,
    or None if `version` is the oldest."""
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] == version:
            return sorted_releases[i - 1]["version"] if i > 0 else None
    return None


def _next_patch_version(version):
    """Return the version string of the patch after `version` in RELEASE_HISTORY,
    or None if `version` is the newest."""
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] == version:
            return sorted_releases[i + 1]["version"] if i + 1 < len(sorted_releases) else None
    return None


def _patch_index(version):
    """Return 0-based index of `version` in PATCHES (newest-first), or None."""
    for i, p in enumerate(PATCHES):
        if p["version"] == version:
            return i
    return None
