"""Captains Mode: cm_draft draws the old and new pick / ban order side by side (docs/captains-mode.md). Cut out of
elements.py (2026-11-07)."""


def cm_draft(*phases, first_label="First pick", second_label="Second pick"):
    if not phases:
        return ''
    full_old = ''.join(o for _, o, _ in phases)
    full_new = ''.join(n for _, _, n in phases)
    if len(full_new) != len(full_old):
        raise ValueError('cm_draft: old and new draft sequences differ in length')

    def _num(step, team, gr):
        side = 'cm-to-left' if team == 'first' else 'cm-to-right'
        return (f'<span class="cm-vnum {side}" '
                f'style="grid-column:2;grid-row:{gr}">{step}</span>')

    def _slot(team, kind, gr, span):
        col = 1 if team == 'first' else 3
        side = 'cm-left' if team == 'first' else 'cm-right'
        gr_v = f'{gr}/span {span}' if span > 1 else f'{gr}'
        return (f'<span class="cm-token {kind} {side}" '
                f'style="grid-column:{col};grid-row:{gr_v}"></span>')

    def _board(which):
        seq = full_old if which == 'Old' else full_new
        cells = [
            f'<span class="cm-vhead" style="grid-column:1;grid-row:1">{first_label}</span>',
            '<span class="cm-vnum cm-vnum-head" style="grid-column:2;grid-row:1"></span>',
            f'<span class="cm-vhead" style="grid-column:3;grid-row:1">{second_label}</span>',
        ]
        def _team(ch):
            return 'first' if ch in 'Ff' else 'second'
        row = 2
        i = 0
        n = len(seq)
        while i < n:
            a = seq[i]
            if a in 'fs':
                if (i + 1 < n and seq[i + 1] in 'fs'
                        and _team(seq[i + 1]) != _team(a)):
                    b = seq[i + 1]
                    cells.append(_num(i + 1, _team(a), row))
                    cells.append(_num(i + 2, _team(b), row + 1))
                    cells.append(_slot(_team(a), 'pick', row, 2))
                    cells.append(_slot(_team(b), 'pick', row, 2))
                    row += 2
                    i += 2
                else:
                    cells.append(_num(i + 1, _team(a), f'{row}/span 2'))
                    cells.append(_slot(_team(a), 'pick', row, 2))
                    row += 2
                    i += 1
            else:
                cells.append(_num(i + 1, _team(a), row))
                cells.append(_slot(_team(a), 'ban', row, 1))
                row += 1
                i += 1
        grid = f'<div class="cm-vgrid">{"".join(cells)}</div>'
        return f'<div class="cm-board">{grid}</div>'

    boards = (f'<div class="cm-boards">{_board("Old")}'
              f'<span class="cm-arrow">→</span>'
              f'{_board("New")}</div>')
    return f'<div class="cm-draft"><div class="cm-scroll">{boards}</div></div>'
