# Формат данных и API хелперов

## Valve KV формат (patchnotes_english.txt)

```
"DOTA_Patch_7_41c_item_blink_1"    "Blink Dagger cooldown from 14 to 12"
"DOTA_Patch_7_41c_axe_1"           "Base armor increased from 2 to 4"
"DOTA_Patch_7_41c_axe_axe_berserkers_call_1"  "Duration from 2.6/2.8/3/3.2 to 3/3.1/3.2/3.3"
"DOTA_Patch_7_41c_General_Roshan_Title"        "Roshan"
```

Формат ключа: `DOTA_Patch_<ver>_<entity_key>_<index>`

## Badge хелперы (patch/badges.py)

### `b(old, new, l=False)` — числовой бейдж
```python
b(100, 80)           # simple: 80→100 = +25% buff
b(100, 80, l=True)   # l=True = меньше лучше (cooldown): 80 это buff
b([100, 110, 120], [110, 120, 130])  # per-level значения
```

### `br(old_min, old_max, new_min, new_max, l=False)` — range бейдж
```python
br(45, 51, 47, 53)   # range: midpoint comparison
```

### `bf(old_fn, new_fn, formula_text, levels=None, l=False, ...)` — формульный бейдж
Возвращает `(trigger, badge, table)` — раскрывающаяся таблица по уровням.
```python
trigger, badge, table = bf(
    lambda L: 10 + 2*L,          # old formula
    lambda L: 8 + 2*L,           # new formula
    "8% + 2% per level"           # отображаемый текст
)
W(li("Max damage decreased", badge, extra=table))
```

### `t(tag)` — текстовый тег
```python
t("BUFF")    # зелёный
t("NERF")    # красный
t("REWORK")  # синий
t("MISC")    # серый
t("QoL")     # жёлтый
t("NEW")     # фиолетовый (считается как buff для фильтра)
```

## HTML-хелперы

```python
section("Hero Updates")        # <h2> разделитель
hero_header("Anti-Mage")       # блок с картинкой героя из CDN
item_header("Blink Dagger")    # блок с картинкой предмета
ability("Mana Void")           # <h4> название способности
subgroup("Talents")            # <h4> подгруппа
plain_header("Roshan")         # блок без картинки
ul_open() / ul_close()         # обёртка списка изменений
li("Mana cost", b(100, 80, l=True))   # строка изменения с бейджем
subnote("Available at level 6")       # дополнительная заметка
li_formula(prefix, old_formula, new_formula, old_fn, new_fn)  # формульная строка
```

## `l=True` — когда использовать

| Всегда l=True | Никогда l=True |
|---|---|
| cooldown | damage |
| mana cost / manacost | heal |
| cast point | range |
| channel time | duration (обычно) |
| gold cost | HP |
| recharge time | move speed |
| penalty | strength/agi/int |

## Исправление неверных тегов

`generate_patch_code_v2.py` угадывает тег по тексту и прав ~80% времени.
Отдельной таблицы переопределений нет — правки вносятся руками в
сгенерированном `content/p<version>.py`: меняешь вызов `t(...)` / `b(...)` прямо в
строке (например `t("BUFF")` → `t("NERF")`, убрать бейдж у нейтрального
уточнения, или добавить `l=True` cost-строке). Ревьюь скаффолд перед сохранением.
