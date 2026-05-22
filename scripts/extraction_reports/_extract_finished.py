# -*- coding: utf-8 -*-
"""Витяг 7-ї вкладки "Журнал ГП повний" з JSON-файлу і запис у CSV."""
import json
import csv
import re
from collections import Counter
from pathlib import Path

SRC = Path(r"C:\Users\nomer\.claude\projects\c--Users-nomer-biolab-librarian\9443d36b-7a03-498f-85f1-248958bc9fa4\tool-results\mcp-claude_ai_Google_Drive-read_file_content-1779366866558.txt")
OUT_CSV = Path(r"c:\Users\nomer\biolab-quality-journal\scripts\extraction_reports\finished_batches.csv")
OUT_MD = Path(r"c:\Users\nomer\biolab-quality-journal\scripts\extraction_reports\03_finished_summary.md")

# Колонки CSV (англ)
CSV_COLS = [
    "date_filling", "batch_number_gp", "date_bulk_prepared", "batch_number_bulk",
    "date_aroma_added", "trademark_name", "label_name", "quantity_units",
    "volume", "notes", "packaging_type", "allowed_for_shipment",
]

# Заголовки джерела (для пошуку межі)
HEADER_MARKERS = [
    "Дата фасування",
    "Номер партії ГП",
    "Дата приготування",
]


def main():
    raw = SRC.read_text(encoding="utf-8")
    # Файл — JSON {fileContent: string}
    try:
        data = json.loads(raw)
        content = data.get("fileContent", raw)
    except json.JSONDecodeError:
        content = raw

    # Знайдемо всі рядки markdown-таблиць
    lines = content.split("\n")

    # Знаходимо заголовок ГП-таблиці. З _inspect_out.txt відомо:
    # header_line = 1184, наступний table-separator = 1394 (початок наступної таблиці).
    # Дані: lines[1186..1393], але треба брати тільки 12-колонкові рядки.
    h_idx = None
    for i, line in enumerate(lines):
        if all(m in line for m in HEADER_MARKERS) and "Артикул" in line and line.count("|") >= 12:
            h_idx = i
            break
    if h_idx is None:
        raise SystemExit("Не знайдено заголовок 7-ї таблиці")
    print(f"Заголовок ГП-таблиці: рядок {h_idx}")

    # Знайдемо кінець — наступний рядок-роздільник (---|---|---) ПІСЛЯ нашого
    # (наш роздільник на h_idx+1). Або перший рядок з аномальною кількістю |.
    end_idx = len(lines)
    for j in range(h_idx + 2, len(lines)):
        ln = lines[j]
        # роздільник наступної таблиці
        stripped = ln.strip()
        if re.fullmatch(r"[\|\:\-\s]+", stripped) and stripped.count("|") >= 3 and "-" in stripped:
            # це нова таблиця — кінець нашої тут (заголовок попередній рядок)
            # відкочуємось на 1 — наш заголовок не повинен потрапити
            end_idx = j - 1
            # Можливо попередній — порожній або заголовок нової таблиці; відріжемо консервативно
            # знайдемо останній рядок, що починається з |
            while end_idx > h_idx + 2 and not lines[end_idx - 1].strip().startswith("|"):
                end_idx -= 1
            break

    print(f"Кінець ГП-таблиці: рядок {end_idx} (довжина даних {end_idx - h_idx - 2})")

    # Парсимо рядки таблиці
    header_line = lines[h_idx]
    sep_line = lines[h_idx + 1]
    data_lines = lines[h_idx + 2:end_idx]

    # Заголовок (для перевірки)
    headers_src = [h.strip() for h in header_line.strip().strip("|").split("|")]
    print(f"\nЗаголовки джерела ({len(headers_src)}): {headers_src}")

    rows = []
    for ln in data_lines:
        if not ln.startswith("|"):
            continue
        # розділяємо по |
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        # Доповнимо до 12 колонок
        while len(parts) < 12:
            parts.append("")
        if len(parts) > 12:
            # Об'єднаємо зайві в notes (10-у колонку)? Краще обрізати з логом
            print(f"WARN: рядок має {len(parts)} клітинок, обрізаю: {ln[:120]}")
            parts = parts[:12]
        # Пропустимо повністю порожній рядок
        if all(p == "" for p in parts):
            continue
        rows.append(parts)

    print(f"\nЗапарсено рядків даних: {len(rows)}")

    # Запис у CSV (UTF-8 BOM)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_COLS)
        for r in rows:
            writer.writerow(r)
    print(f"CSV записано: {OUT_CSV}")

    # ---- Аналіз для звіту ----
    n = len(rows)

    # Період (роки) і листопад 2025
    # date_filling — формат US M/D/YYYY (через Google Sheets locale)
    # batch_number_gp — формат UA DD/MM/YY (як писали закупівельники)
    years = []
    nov_2025 = 0
    nov_2025_rows = []
    for r in rows:
        d_fill = r[0]   # date_filling
        b_gp = r[1]     # batch_number_gp
        found_nov25 = False
        # 1) date_filling як M/D/YYYY
        m_fill = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$", d_fill)
        if m_fill:
            mo, da, yr = m_fill.groups()
            if len(yr) == 2:
                yr = "20" + yr
            years.append(yr)
            if yr == "2025" and mo.lstrip("0") == "11":
                found_nov25 = True
        # 2) batch_number_gp як DD/MM/YY (формат "04/11/24")
        m_b = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})", b_gp)
        if m_b:
            da, mo, yr = m_b.groups()
            if len(yr) == 2:
                yr = "20" + yr
            years.append(yr)
            if yr == "2025" and mo.lstrip("0") == "11":
                found_nov25 = True
        if found_nov25:
            nov_2025 += 1
            nov_2025_rows.append(r)

    if years:
        period = f"{min(years)} → {max(years)}"
    else:
        period = "?"

    # Унікальні ТМ (колонка trademark_name, індекс 5)
    tms = [r[5] for r in rows if r[5]]
    tm_counter = Counter(tms)

    # Унікальні типи тари (індекс 10)
    pack = [r[10] for r in rows if r[10]]
    pack_counter = Counter(pack)

    # Статус дозволу (індекс 11)
    allowed_yes = sum(1 for r in rows if r[11].strip().lower() in ("дозволено", "так", "yes", "+"))
    allowed_other = n - allowed_yes

    # Без bulk (індекс 3)
    no_bulk = sum(1 for r in rows if not r[3].strip())

    # Дублі номера партії ГП (індекс 1)
    gp_counter = Counter(r[1] for r in rows if r[1].strip())
    dup_gp = {k: v for k, v in gp_counter.items() if v > 1}

    # Без об'єму/кількості
    no_vol = sum(1 for r in rows if not r[8].strip() and not r[7].strip())

    # Порожні ключові поля (партія ГП, артикул/ТМ, назва)
    empty_key_examples = []
    empty_key = 0
    for r in rows:
        if not r[1].strip() or not r[5].strip() or not r[6].strip():
            empty_key += 1
            if len(empty_key_examples) < 5:
                empty_key_examples.append(r)

    # Перші 5 рядків CSV-превʼю
    preview_lines = [",".join(CSV_COLS)]
    for r in rows[:5]:
        # для превʼю — простий join
        preview_lines.append(",".join(f'"{c}"' if "," in c else c for c in r))

    # ---- Запис звіту ----
    md = []
    md.append("# Витяг журналу ГП\n")
    md.append("## Загалом")
    md.append(f"- Партій ГП: {n}")
    md.append(f"- Період: {period}")
    md.append(f"- Унікальних ТМ (з колонки яка названа \"Артикул\"): {len(tm_counter)}")
    md.append(f"- Унікальних типів тари: {len(pack_counter)}")
    md.append(f"- Партій ГП за листопад 2025: {nov_2025}\n")

    md.append("## За ТМ-замовниками (топ-10)")
    md.append("| ТМ | Партій |")
    md.append("|---|---|")
    for tm, cnt in tm_counter.most_common(10):
        md.append(f"| {tm} | {cnt} |")
    md.append("")

    md.append("## За типами тари")
    md.append("| Тип | Партій |")
    md.append("|---|---|")
    for p, cnt in pack_counter.most_common():
        md.append(f"| {p} | {cnt} |")
    md.append("")

    md.append("## За статусом дозволу")
    md.append(f"- дозволено: {allowed_yes}")
    md.append(f"- порожньо/інше: {allowed_other}\n")

    md.append("## Проблеми")
    md.append(f"- Партій без посилання на bulk-варку: {no_bulk}")
    if dup_gp:
        examples = ", ".join(f"{k} ({v}x)" for k, v in list(dup_gp.items())[:5])
        md.append(f"- Дублі № партії ГП: {len(dup_gp)} (приклади: {examples})")
    else:
        md.append("- Дублі № партії ГП: 0")
    md.append(f"- Партій без об'єму/кількості: {no_vol}")
    md.append(f"- Партій з порожніми ключовими полями: {empty_key}")
    if empty_key_examples:
        md.append("  Приклади:")
        for ex in empty_key_examples:
            md.append(f"  - GP={ex[1]!r}, TM={ex[5]!r}, label={ex[6]!r}")
    md.append("")

    md.append("## Перші 5 рядків CSV (превʼю)")
    md.append("```")
    md.extend(preview_lines)
    md.append("```")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"MD записано: {OUT_MD}")

    # Final summary для агента
    print("\n=== SUMMARY ===")
    print(f"CSV: {OUT_CSV}")
    print(f"MD:  {OUT_MD}")
    print(f"Партій ГП: {n}")
    print(f"Листопад 2025: {nov_2025}")


if __name__ == "__main__":
    main()
