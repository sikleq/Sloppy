# Архитектура Sloppy

## Схема данных

```
data/patchnotes_english.txt   (Valve KV)
        ↓
generate_patch_code.py        (парсер → Python-код)
        ↓
_generated_p_<version>.py     (промежуточный файл, ревьюится вручную)
        ↓
build_patch.py                (интегрируется вручную + CSS + JS + хелперы)
        ↓
7.41c.html                    (финальный сайт)
```

## build_patch.py — содержимое

Файл построен по секциям сверху вниз:

| Секция | Что делает |
|---|---|
| CDN-константы | URL для картинок героев/предметов/способностей |
| HERO_SLUG / ITEM_SLUG | Маппинг отображаемых имён → CDN-слаги |
| Градиент-хелперы | `gradient_class()`, `b()`, `br()`, `bf()`, `t()` |
| HTML-хелперы | `hero_header()`, `item_header()`, `section()`, `ability()`, `li()`, `subnote()` |
| CSS (строка) | Весь CSS сайта в Python-строке `CSS = """..."""` |
| JS (строка) | Весь JS сайта в Python-строке `SCRIPT = """..."""` |
| Scaffold | `W()` writer, HTML-обёртка, nav, фильтры |
| Контент патча | Секции General / Items / Heroes с вызовами хелперов |

## generate_patch_code.py — как работает

1. Читает `data/patchnotes_english.txt`
2. Ищет строки вида `"DOTA_Patch_7_41c_<ключ>" "<значение>"`
3. `parse_key()` — разбирает ключ на тип (герой/предмет/general/etc.) и entity
4. `parse_value_change()` — пытается извлечь "from X to Y", формулу, range, или угадывает тег
5. Выдаёт Python-строки типа `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))`
6. Пишет в `_generated_p_<version>.py`

## Как CSS и JS попадают в HTML

В конце `build_patch.py` есть функция-scaffold которая:
- пишет `<style>{CSS}</style>` напрямую в HTML
- пишет `<script>{SCRIPT}</script>` напрямую в HTML

Поэтому `styles.css` и `scripts.js` в репо — **отдельные standalone файлы** (для других страниц типа index.html), не связаны с генерируемыми патч-страницами.
