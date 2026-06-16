# Формулы и таблицы уровней

Правила для per-level scaling, `li_formula`/`scale_pill` и сетки уровней на патч-страницах.

> Связано: для важных **игровых** формул (Assist Gold, Experience…) использовать блок `formula_change` (old→new), а не два `li` — см. `docs/formula-change.md`.

## Любой "per level" в строке → клик-формула обязательна

Если в строке упоминается per-level scaling (`X + Y per level`, `Xs − Ys per level` и т.п.) — рендерить через `li_formula(...)` (diff old vs new) или `scale_pill(...)` (новая способность без сравнения). Простой `t("MISC")` с текстовой формулой = баг.

```python
# Diff (старое → новое):
W(li_formula("Bonus Night Vision changed",
             "250 + 25 per level up", "225 + 25 per level",
             lambda L: 250 + 25*L, lambda L: 225 + 25*L,
             effective_unchanged=True))

# Новая способность (внутри ability_change new=dict(...)):
_pill, _table = scale_pill("45.75s − 0.75s per level",
                           lambda L: 45.75 - 0.75 * L,
                           levels=[1, 5, 10, 15, 20, 25, 30],
                           value_fmt="{:.2f}s")
# В desc: "Cooldown: " + _pill + ".",  tables=[_table]
```

**Сетка уровней (ПРАВИЛО):**
- **Полноширинные** таблицы (li_formula / scale_pill в обычной `li`-строке): НЕ передавать `levels=` — дефолт L1–L15, L20, L25, L30 (полная сетка) обязателен.
- Скейл каждые **X>1 уровней** («per 5 levels», «per 3 level ups»): сетка с шагом X до 30 (точки, где значение реально меняется, + L1). При смене шага old→new («per 7 → per 6 levels») — объединение точек перелома обеих формул.
- **Внутри панелей `ability_change`** (пол-ширины): компактная `levels=[1, 5, 10, 15, 20, 25, 30]` — полная сетка туда физически не влезает (`table-layout:fixed`, колонки сжимаются нечитаемо).

## li_formula с `effective_unchanged=True` → левый тег MISC

`li_formula` авто-вешает REWORK слева по умолчанию. Когда `effective_unchanged=True` — переключается на MISC (семантически нейтральная переформулировка, не структурная переработка). Глобальная строка `"Abilities that had 'per level up' scaling changed to be 'per level'"` тоже MISC, не REWORK.

## "per level up" ≠ "per level" (7.41 rename)

7.41 переименовал механику: `"Abilities that had 'per level up' scaling changed to be 'per level'"`. В `li_formula(...)` для 7.41 изменений вида `"changed from X per level up to Y per level"` — **СТАРАЯ** строка обязана содержать `"per level up"` буквально:

```python
W(li_formula("Agility Multiplier changed",
             "0.6 + 0.05 per level up",   # OLD — обязательно "up"
             "0.55 + 0.05 per level",     # NEW — без "up"
             lambda L: ..., lambda L: ...,
             effective_unchanged=True))
```

Удаление `up` из OLD-строки = семантическая ошибка (переименование механики не отражено). Обычно сочетается с `effective_unchanged=True` + `subnote("Effective values are not changed")`.

## "Effective values are not changed" → `effective_unchanged=True`

Когда патчноут говорит `"Effective values are not changed"` рядом с формульным изменением, передавать в `li_formula(...)` флаг `effective_unchanged=True`. Это подавит вводящий в заблуждение Δ% (формула может буквально различаться по числам, но Valve её перепараметризировала так, что итоговое значение в игре то же).

```python
W(li_formula("Damage changed",
             "25 + 2 per level", "23 + 2 per level",
             lambda L: 25.0 + 2.0 * L, lambda L: 23.0 + 2.0 * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
```

Если `old_fn(L) == new_fn(L)` буквально на всех уровнях (просто другая запись той же формулы), флаг не нужен — старый branch `values_unchanged` уже схлопывает в одну `value` строку автоматически.
