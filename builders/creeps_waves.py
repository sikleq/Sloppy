"""Unit Stats, View: Waves (owner 2026-11-26: "сайт должен знать, из каких лайновых крипов состоит каждая волна на
текущий патч и показывать слева номер и состав волны, её характеристики на каждом апгрейде, чтобы нюк тоже считал").

The wave rules of the current patch (7.42a, server.dll 6997, read by the IDA researcher 2026-11-26, CONFIRMED_DLL):
- wave n leaves at T = 30·(n − 1) s of game time; its make-up is counted at t = T + 3 s against thresholds (t > x),
  so a wave exactly at 15:00 / 35:00 / 45:00 / 60:00 already has the extra unit;
- melee in total 3, +1 after 15:00, +1 after 45:00 (7.42 dropped the one at 30:00);
- a flagbearer when n ≥ 5 and (n odd or t > 30:00): it TAKES the place of the last melee;
- ranged 1, +1 after 35:00;
- siege when n ≥ 2 and (T a multiple of 5:00, or t > 30:00 and T a multiple of 2:30): 1, 2 after 60:00; on top.
Super / mega waves are the same units swapped one for one (the toolbar's Creeps choice). The page's script
(src/js/creeps-upgrade.js) sums each wave's numbers at its own upgrade step from the unit rows of the table.
A new patch that changes these rules: change wave_composition and its test (tests/test_unit_stats_lane.py)."""
from builders.creeps_common import esc

WAVE_EVERY_S = 30
WAVE_LOOK_AHEAD_S = 3          # the spawner counts the make-up at T + 3 s
MELEE_PLUS_AT = (900, 2700)    # 15:00, 45:00
RANGED_PLUS_AT = (2100,)       # 35:00
SIEGE_PLUS_AT = (3600,)        # 60:00
FLAG_EVERY_WAVE_AFTER = 1800   # 30:00
UPGRADE_STEP_S = 450
LAST_WAVE = 121                # 60:00
KINDS = (('melee', 'lane_melee', 'Melee'), ('flag', 'lane_flagbearer', 'Flagbearer'),
         ('ranged', 'lane_ranged', 'Ranged'), ('siege', 'lane_siege', 'Siege'))


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


WAVE_COLS = (('wave', 'Wave'), ('time', 'Time'), ('units', 'Units'), ('step', 'Upgrade'), ('hp', 'HP'),
             ('dmg', 'Damage'), ('gold', 'Gold'), ('xp', 'XP'), ('kill', 'Nuke'))


def waves_table_html(icons):
    """The Waves table; icons = {'lane_melee': src, …}. Number cells are filled by the page's script."""
    head = ''.join(f'<th class="wv-{k}">{esc(label)}</th>' for k, label in WAVE_COLS)
    rows = []
    for n in range(1, LAST_WAVE + 1):
        c = wave_composition(n)
        chips = ''.join(
            f'<span class="wv-unit" data-kind="{key}" title="{esc(label)}">'
            f'<img src="{esc(icons.get(row, ""))}" alt="{esc(label)}" loading="lazy">'
            f'<b>{c[key]}</b></span>'
            for key, row, label in KINDS if c[key])
        data = ' '.join(f'data-{key}="{c[key]}"' for key, _r, _l in KINDS)
        rows.append(f'<tr {data} data-step="{wave_step(n)}"><td class="wv-wave">{n}</td>'
                    f'<td class="wv-time">{_clock(wave_time(n))}</td><td class="wv-units">{chips}</td>'
                    f'<td class="wv-step">{wave_step(n)}</td>'
                    + ''.join(f'<td class="wv-{k}"></td>' for k in ('hp', 'dmg', 'gold', 'xp', 'kill'))
                    + '</tr>')
    return (f'<table class="waves-table"><thead><tr>{head}</tr></thead>'
            f'<tbody>\n{chr(10).join(rows)}\n</tbody></table>\n')
