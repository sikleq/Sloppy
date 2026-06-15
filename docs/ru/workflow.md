# Воркфлоу: добавить новый патч

## Шаг 1 — Получить данные Valve

1. Скачать KV-файл патчноутов от Valve (обычно есть на GitHub или Dota 2 VPK)
2. Положить в `data/patchnotes_english.txt` (заменив или добавив новую версию)
3. При наличии русского перевода — в `data/patchnotes_russian.txt`

## Шаг 2 — Сгенерировать шаблон кода

```bash
python generate_patch_code_v2.py 7.42
```

Читает кэш датафида (`data/7.42_datafeed.json`) и создаёт `_generated_p_7.42_v2.py` — Python-код с вызовами `W(li(...))`, `W(hero_header(...))` и т.д. на хелперах `patch/`.

Что нужно проверить в сгенерированном файле:
- Теги (BUFF/NERF/REWORK) — автодетект ошибается ~10-20% случаев
- `l=True` флаги — проверить для cooldown/mana cost строк
- Формульные изменения — `bf()` вызовы требуют правильных лямбд
- Новые герои/предметы которых нет в словарях

## Шаг 3 — Сохранить как content-модуль

1. Отревьюить и поправить `_generated_p_7.42_v2.py`
2. Сохранить тело как `content/p742.py`, обернув в `def build():`
3. Зарегистрировать в `builders/patch.py`:
   ```python
   import content.p742
   # в __main__ (от старых к новым):
   content.p742.build()
   ```

## Шаг 4 — Добавить новых героев/предметы (если есть)

Новый герой / предмет — добавить маппинг имя → engine-слаг в `patch/images.py`:
```python
# patch/images.py: HERO_SLUG
"New Hero": "new_hero_slug",

# patch/images.py: ITEM_SLUG
"New Item": "new_item_slug",
```
(`generate_patch_code_v2.py` резолвит имена из `data/herolist.json` / `data/itemlist.json` — отдельный маппинг генератору не нужен.)

## Шаг 5 — Собрать и проверить

```bash
python builders/patch.py
```

Открыть `patches/7.42.html` в браузере и проверить:
- Фильтры (BUFF / NERF / ALL) работают
- Формульные таблицы раскрываются
- Картинки героев/предметов загружаются (CDN URL)
- Нет Python ошибок при запуске

## Шаг 6 — Деплой

Запушить в `main` — CI (`.github/workflows/build.yml`) прогонит тесты и `builders/patch.py` (+ остальные билдеры) и задеплоит на GitHub Pages.

## Типичные ошибки

| Ошибка | Причина |
|---|---|
| `KeyError` в `t()` | Неизвестный тег — проверь значение, переданное в `t(...)` (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL) |
| Картинка 404 | Неверный slug в HERO_SLUG/ITEM_SLUG, проверь CDN |
| Фильтр не работает | Забыл `data-tag` атрибут в `li()`, проверь бейдж |
| Таблица не раскрывается | `bf()` не вернул table в `extra=table` |
