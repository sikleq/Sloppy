"""Unit Stats, View: Waves (owner 2026-11-26: "сайт должен знать, из каких лайновых крипов состоит каждая волна на
текущий патч и показывать слева номер и состав волны, её характеристики на каждом апгрейде, чтобы нюк тоже считал";
then "waves надо по аналогии с timeline, тоже характеристики по таймингам апгрейдов суммарно с возможность не
учитывать siege unit (сделать его серым)").

One row per wave make-up (in the order it first appears), the wave sums of HP / Damage / Gold / XP at every 7:30
upgrade step like the Timeline view; steps when that make-up does not leave are dimmed. The page's script
(src/js/creeps-upgrade.js waves) sums the lane rows of the Creeps choice by the same rules as the table; a click on
a siege icon greys every siege creep and leaves it out of the sums.

The wave rules of the current patch (7.42a, server.dll 6997, read by the IDA researcher 2026-11-26, CONFIRMED_DLL):
- wave n leaves at T = 30·(n − 1) s of game time; its make-up is counted at t = T + 3 s against thresholds (t > x),
  so a wave exactly at 15:00 / 35:00 / 45:00 / 60:00 already has the extra unit;
- melee in total 3, +1 after 15:00, +1 after 45:00 (7.42 dropped the one at 30:00);
- a flagbearer when n ≥ 5 and (n odd or t > 30:00): it TAKES the place of the last melee;
- ranged 1, +1 after 35:00;
- siege when n ≥ 2 and (T a multiple of 5:00, or t > 30:00 and T a multiple of 2:30): 1, 2 after 60:00; on top.
Super / mega waves are the same units swapped one for one (the toolbar's Creeps choice).
A new patch that changes these rules: change wave_composition and its test (tests/test_unit_stats_waves.py)."""
from builders.creeps_common import esc

WAVE_EVERY_S = 30
WAVE_LOOK_AHEAD_S = 3          # the spawner counts the make-up at T + 3 s
MELEE_PLUS_AT = (900, 2700)    # 15:00, 45:00
RANGED_PLUS_AT = (2100,)       # 35:00
SIEGE_PLUS_AT = (3600,)        # 60:00
FLAG_EVERY_WAVE_AFTER = 1800   # 30:00
UPGRADE_STEP_S = 450
LAST_WAVE = 121                # 60:00
STEPS = tuple(range(9))        # 0:00 … 60:00, as the Timeline view
KINDS = (('melee', 'lane_melee', 'Melee'), ('flag', 'lane_flagbearer', 'Flagbearer'),
         ('ranged', 'lane_ranged', 'Ranged'), ('siege', 'lane_siege', 'Siege'))
WAVE_STATS = (('hp', 'HP'), ('dmg', 'Damage'), ('gold', 'Gold'), ('xp', 'XP'))


def wave_time(n):
    return WAVE_EVERY_S * (n - 1)


def wave_composition(n):
    """{'melee', 'flag', 'ranged', 'siege'} unit counts of wave n (1 = the 0:00 wave)."""
    if n < 1:
        raise ValueError(f'wave number {n}: waves start at 1')
    T = wave_time(n)
    t = T + WAVE_LOOK_AHEAD_S
    melee_all = 3 + sum(t > x for x in MELEE_PLUS_AT)
    flag = 1 if n >= 5 and (n % 2 == 1 or t > FLAG_EVERY_WAVE_AFTER) else 0
    siege_wave = n >= 2 and (T % 300 == 0 or (t > FLAG_EVERY_WAVE_AFTER and T % 150 == 0))
    return {'melee': melee_all - flag, 'flag': flag,
            'ranged': 1 + sum(t > x for x in RANGED_PLUS_AT),
            'siege': (1 + sum(t > x for x in SIEGE_PLUS_AT)) if siege_wave else 0}


def wave_step(n):
    """The creeps' upgrade step when wave n leaves (one every 7:30)."""
    return wave_time(n) // UPGRADE_STEP_S


def _clock(s):
    return f'{s // 60}:{s % 60:02d}'


def wave_kinds():
    """[(make-up dict, [wave numbers])] in the order each make-up first leaves, waves 1 … LAST_WAVE."""
    order, waves = [], {}
    for n in range(1, LAST_WAVE + 1):
        c = wave_composition(n)
        key = tuple(c[k] for k, _r, _l in KINDS)
        if key not in waves:
            order.append(c)
            waves[key] = []
        waves[key].append(n)
    return [(c, waves[tuple(c[k] for k, _r, _l in KINDS)]) for c in order]


def waves_table_html(icons):
    """The Waves table; icons = {'lane_melee': src, …}. Number cells are filled by the page's script."""
    # the Timeline view's head (owner 2026-11-26: "по дизайну, не как в timeline"): a group row (tr.cat-row /
    # th.cat-head) over the column row (tr.col-row), a 2px col-sep where a group starts
    cat = ('<th class="cat-head cat-basic" data-cat="wave" colspan="2">Wave</th>'
           + ''.join(f'<th class="cat-head" data-cat="wv-{k}" colspan="{len(STEPS)}">{esc(label)}</th>'
                     for k, label in WAVE_STATS))
    # data-cat on every column head: src/js/creeps-pinned.js recomputeCatColspans sets each group's colspan from them
    cols = ('<th class="wv-units-h" data-cat="wave">Units</th><th class="wv-when-h" data-cat="wave">Time</th>'
            + ''.join(f'<th class="wv-t{" col-sep" if i == 0 else ""}" data-cat="wv-{k}">{_clock(i * UPGRADE_STEP_S)}</th>'
                      for k, _l in WAVE_STATS for i in STEPS))
    rows = []
    for c, ns in wave_kinds():
        chips = ''.join(
            f'<span class="wv-unit" data-kind="{key}" title="{esc(label)}">'
            f'<img src="{esc(icons.get(row, ""))}" alt="{esc(label)}" loading="lazy">'
            f'<b>{c[key]}</b></span>'
            for key, row, label in KINDS if c[key])
        steps = sorted({wave_step(n) for n in ns})
        times = ', '.join(_clock(wave_time(n)) for n in ns)
        when = _clock(wave_time(ns[0])) + (f'–{_clock(wave_time(ns[-1]))}' if len(ns) > 1 else '')
        data = ' '.join(f'data-{key}="{c[key]}"' for key, _r, _l in KINDS)
        cells = ''.join(
            f'<td class="wv-{k}-{i}{" col-sep" if i == 0 else ""}{"" if i in steps else " wv-none"}"></td>'
            for k, _l in WAVE_STATS for i in STEPS)
        rows.append(f'<tr {data} data-steps="{" ".join(map(str, steps))}">'
                    f'<td class="wv-units"><div class="wv-units-in">{chips}</div></td>'
                    f'<td class="wv-when tb-tip-target" data-tooltip="{esc(times)}">{when} '
                    f'<span class="wv-count">×{len(ns)}</span></td>{cells}</tr>')
    # .creeps-table: the units table's whole look; the page's scripts take the FIRST .creeps-table (the units one)
    return (f'<table class="creeps-table waves-table"><thead><tr class="cat-row">{cat}</tr>'
            f'<tr class="col-row">{cols}</tr></thead>'
            f'<tbody>\n{chr(10).join(rows)}\n</tbody></table>\n')
