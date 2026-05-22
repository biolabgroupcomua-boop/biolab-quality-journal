"""Витяг трьох довідників з markdown-експорту Google Sheet.

Вхід: JSON-файл {fileContent: <markdown>} з 9 склеєних таблиць.
Вихід:
  - products_rp.csv (з вкладки "Артикули RP")
  - customers.csv + variants.csv (з вкладки "Каталог TM × ГП")
  - specifications.csv (з вкладки "Специфікації")
  - 01_dictionaries_summary.md (звіт)
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

SRC = Path(r"C:\Users\nomer\.claude\projects\c--Users-nomer-biolab-librarian\9443d36b-7a03-498f-85f1-248958bc9fa4\tool-results\mcp-claude_ai_Google_Drive-read_file_content-1779366866558.txt")
OUT_DIR = Path(r"C:\Users\nomer\biolab-quality-journal\scripts\extraction_reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# 1) Завантаження JSON та парсинг markdown-таблиць
# -----------------------------------------------------------------------------

def load_content() -> str:
    raw = SRC.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data["fileContent"]


def split_row(line: str) -> list[str]:
    """Розбити рядок markdown-таблиці `| a | b | c |` на клітинки.

    Знімаємо ескейп-послідовності `\\+` -> `+`, `\\_` -> `_`, прибираємо
    зайві пробіли. Першу/останню (порожні) пасажі видаляємо.
    """
    # Прибрати ведучий і кінцевий `|`
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [c.strip() for c in stripped.split("|")]
    # Знімаємо markdown-ескейпи
    cells = [re.sub(r"\\([+_*\-`])", r"\1", c) for c in cells]
    return cells


def is_separator(line: str) -> bool:
    """Рядок типу `| :-: | :-: | ... |` — markdown-роздільник заголовка."""
    s = line.strip()
    if not s or s.count("|") < 3:
        return False
    return bool(re.fullmatch(r"[\|\:\-\s]+", s)) and "-" in s


def parse_tables(content: str) -> list[dict]:
    """Розбити склеєний markdown на список таблиць.

    Повертає список {header: [cols], rows: [[cells]], header_line: int}.
    Таблиця = рядок-заголовок, потім роздільник, потім рядки-дані до
    першого порожнього/нерядкового рядка.
    """
    lines = content.split("\n")
    tables: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            line.strip().startswith("|")
            and i + 1 < len(lines)
            and is_separator(lines[i + 1])
        ):
            header = split_row(line)
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            tables.append({"header": header, "rows": rows, "header_line": i})
            i = j
        else:
            i += 1
    return tables


# -----------------------------------------------------------------------------
# 2) Утиліта запису CSV
# -----------------------------------------------------------------------------

def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        w.writerows(rows)


# -----------------------------------------------------------------------------
# 3) Ідентифікація потрібних таблиць
# -----------------------------------------------------------------------------

def find_table(tables: list[dict], required_cols: list[str], min_rows: int = 50) -> dict:
    """Знайти таблицю, у заголовку якої присутні ВСІ required_cols (підрядок)."""
    for t in tables:
        header_blob = " | ".join(t["header"]).lower()
        if all(rc.lower() in header_blob for rc in required_cols) and len(t["rows"]) >= min_rows:
            return t
    raise RuntimeError(f"Таблиця не знайдена за колонками: {required_cols}")


def main() -> None:
    content = load_content()
    tables = parse_tables(content)
    print(f"Розпарсено таблиць: {len(tables)}")
    for idx, t in enumerate(tables):
        print(f"  [{idx}] line {t['header_line']:5d} | {len(t['rows']):4d} rows | cols={len(t['header'])} | first col='{t['header'][0]}'")

    # --- Вкладка 4: Каталог TM x ГП ---
    # Шукаємо ТАКОЖ за точним складом заголовка (4 колонки), бо така ж назва
    # `Назва ТМ` зустрічається у вкладці "Журнал ГП v1" як префікс.
    catalog = None
    for t in tables:
        hdr_lower = [c.lower() for c in t["header"]]
        if hdr_lower == ["назва тм", "назва гп (готової продукції)", "артикул rp", "категорія"]:
            catalog = t
            break
    if catalog is None:
        catalog = find_table(tables, ["Назва ТМ", "Назва ГП", "Артикул RP", "Категорія"])
    # Колонки: trademark_name, label_name, rp_code, category
    variants_rows: list[list[str]] = []
    customers_set: set[str] = set()
    empty_variant_rows = 0
    for row in catalog["rows"]:
        # доповнюємо порожніми клітинками якщо рядок коротший за заголовок
        cells = (row + [""] * 4)[:4]
        tm, label, rp, cat = [c.strip() for c in cells]
        if not any([tm, label, rp, cat]):
            empty_variant_rows += 1
            continue
        if tm:
            customers_set.add(tm)
        variants_rows.append([tm, label, rp, cat])

    customers_rows = [[tm] for tm in sorted(customers_set, key=lambda s: s.lower())]
    write_csv(OUT_DIR / "customers.csv", ["trademark_name"], customers_rows)
    write_csv(
        OUT_DIR / "variants.csv",
        ["trademark_name", "label_name", "rp_code", "category"],
        variants_rows,
    )

    # --- Вкладка 5: Артикули RP ---
    rp_table = find_table(tables, ["Артикул", "Товар", "Категорія", "Опис"], min_rows=50)
    # Перевірка що це справді 4-колонкова таблиця, а не каталог
    if len(rp_table["header"]) != 4 or rp_table is catalog:
        # шукаємо таблицю, яка не каталог і має саме 4 колонки з потрібним заголовком
        for t in tables:
            if t is catalog:
                continue
            hdr = [c.lower() for c in t["header"]]
            if hdr == ["артикул", "товар", "категорія", "опис"]:
                rp_table = t
                break

    products_rows: list[list[str]] = []
    rp_codes: list[str] = []
    empty_rp_rows = 0
    rp_no_name: list[str] = []
    for row in rp_table["rows"]:
        cells = (row + [""] * 4)[:4]
        artikul, tovar, kat, opis = [c.strip() for c in cells]
        if not any([artikul, tovar, kat, opis]):
            empty_rp_rows += 1
            continue
        products_rows.append([artikul, tovar, kat, opis])
        if artikul:
            rp_codes.append(artikul)
        if artikul and not tovar:
            rp_no_name.append(artikul)

    write_csv(
        OUT_DIR / "products_rp.csv",
        ["Артикул", "Товар", "Категорія", "Опис"],
        products_rows,
    )

    rp_counter = Counter(rp_codes)
    duplicate_rp = [(code, n) for code, n in rp_counter.items() if n > 1]

    # --- Вкладка 6: Специфікації ---
    specs_table = find_table(tables, ["Spec_ID", "Код продукту", "Статус специфікації"], min_rows=30)
    spec_header = specs_table["header"]
    spec_rows_raw = specs_table["rows"]
    spec_rows: list[list[str]] = []
    empty_spec_rows = 0
    for row in spec_rows_raw:
        cells = (row + [""] * len(spec_header))[: len(spec_header)]
        cells = [c.strip() for c in cells]
        if not any(cells):
            empty_spec_rows += 1
            continue
        spec_rows.append(cells)

    write_csv(OUT_DIR / "specifications.csv", spec_header, spec_rows)

    # Аналіз специфікацій
    try:
        status_idx = next(
            i for i, h in enumerate(spec_header) if "статус специфікації" in h.lower()
        )
    except StopIteration:
        status_idx = None
    status_counter: Counter = Counter()
    if status_idx is not None:
        for r in spec_rows:
            status_counter[r[status_idx] or "(порожньо)"] += 1

    # -----------------------------------------------------------------------------
    # 4) MD-звіт
    # -----------------------------------------------------------------------------
    md_lines: list[str] = []
    md_lines.append("# Витяг довідників\n")
    md_lines.append(f"Джерело: `{SRC.name}`\n")
    md_lines.append(f"Дата витягу: 2026-05-21\n")

    # Products
    md_lines.append("## Products (RP-артикули)\n")
    md_lines.append(f"- Знайдено: {len(products_rows)} рядків")
    md_lines.append(f"- Унікальних RP-кодів: {len(set(rp_codes))} (всього з RP: {len(rp_codes)})")
    md_lines.append(f"- Пустих рядків (відкинуто): {empty_rp_rows}")
    md_lines.append(f"- Дублі RP-коду: {len(duplicate_rp)}")
    if duplicate_rp:
        md_lines.append("  - " + ", ".join(f"`{c}`×{n}" for c, n in duplicate_rp[:10]))
    md_lines.append(f"- RP-коди без назви товару: {len(rp_no_name)}")
    if rp_no_name:
        md_lines.append("  - " + ", ".join(f"`{c}`" for c in rp_no_name[:10]))
    md_lines.append("\n**Перші 5 рядків:**\n")
    md_lines.append("| Артикул | Товар | Категорія | Опис |")
    md_lines.append("| --- | --- | --- | --- |")
    for r in products_rows[:5]:
        md_lines.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
    md_lines.append("")

    # Customers
    md_lines.append("## Customers (ТМ-замовники)\n")
    md_lines.append(f"- Знайдено: {len(customers_rows)} унікальних ТМ")
    md_lines.append("\n**Перші 10 (alphabetical):**\n")
    for r in customers_rows[:10]:
        md_lines.append(f"- {r[0]}")
    md_lines.append("")

    # Variants
    md_lines.append("## ProductVariants (товарні позиції)\n")
    with_rp = sum(1 for r in variants_rows if r[2])
    without_rp = len(variants_rows) - with_rp
    md_lines.append(f"- Знайдено: {len(variants_rows)} рядків")
    md_lines.append(f"- З RP: {with_rp} · Без RP: {without_rp}")
    md_lines.append(f"- Пустих рядків (відкинуто): {empty_variant_rows}")
    md_lines.append("\n**Перші 10 рядків:**\n")
    md_lines.append("| ТМ | Назва ГП | RP | Категорія |")
    md_lines.append("| --- | --- | --- | --- |")
    for r in variants_rows[:10]:
        md_lines.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
    md_lines.append("")

    # Specifications
    md_lines.append("## Specifications\n")
    md_lines.append(f"- Знайдено: {len(spec_rows)} специфікацій")
    md_lines.append(f"- Пустих рядків (відкинуто): {empty_spec_rows}")
    if status_counter:
        md_lines.append("- За статусом:")
        for st, n in status_counter.most_common():
            md_lines.append(f"  - {st}: {n}")
    md_lines.append("\n**Перші 5 рядків (Spec_ID, Код продукту, Назва, Категорія, Статус):**\n")
    md_lines.append("| Spec_ID | Код | Назва | Категорія | Статус |")
    md_lines.append("| --- | --- | --- | --- | --- |")
    try:
        name_idx = next(
            i for i, h in enumerate(spec_header) if "назва з номенклатури" in h.lower()
        )
    except StopIteration:
        name_idx = 2
    try:
        cat_idx = next(i for i, h in enumerate(spec_header) if h.strip().lower() == "категорія")
    except StopIteration:
        cat_idx = 3
    for r in spec_rows[:5]:
        sp = r[0]
        cod = r[1] if len(r) > 1 else ""
        nm = r[name_idx] if len(r) > name_idx else ""
        ct = r[cat_idx] if len(r) > cat_idx else ""
        st = r[status_idx] if status_idx is not None and len(r) > status_idx else ""
        md_lines.append(
            f"| {sp} | {cod} | {nm[:60].replace('|', '/')} | {ct} | {st} |"
        )
    md_lines.append("")

    # Проблеми
    md_lines.append("## Виявлені проблеми\n")
    problems: list[str] = []

    # 1) RP-коди без назв
    if rp_no_name:
        problems.append(
            f"**RP-коди без назви товару** ({len(rp_no_name)}): "
            + ", ".join(f"`{c}`" for c in rp_no_name[:15])
        )

    # 2) Дублі RP
    if duplicate_rp:
        problems.append(
            f"**Дублі RP-кодів у Products** ({len(duplicate_rp)}): "
            + ", ".join(f"`{c}`×{n}" for c, n in duplicate_rp[:10])
        )

    # 3) Варіанти без ТМ
    variants_no_tm = sum(1 for r in variants_rows if not r[0])
    if variants_no_tm:
        problems.append(
            f"**Варіантів без trademark_name**: {variants_no_tm} рядків — не зможемо привʼязати до Customer"
        )

    # 4) Варіанти без назви ГП
    variants_no_label = sum(1 for r in variants_rows if not r[1])
    if variants_no_label:
        problems.append(f"**Варіантів без label_name**: {variants_no_label}")

    # 5) Варіанти з RP якого немає у Products
    product_rp_set = set(rp_codes)
    variant_rp_orphans = [r[2] for r in variants_rows if r[2] and r[2] not in product_rp_set]
    if variant_rp_orphans:
        unique_orphans = sorted(set(variant_rp_orphans))
        problems.append(
            f"**Variant.rp_code, якого НЕ існує у Products** ({len(variant_rp_orphans)} рядків, {len(unique_orphans)} унікальних): "
            + ", ".join(f"`{c}`" for c in unique_orphans[:15])
        )

    # 6) Спекі що посилаються на неіснуючий RP
    try:
        spec_code_idx = next(
            i for i, h in enumerate(spec_header) if "код продукту" in h.lower()
        )
        spec_orphans = [
            r[spec_code_idx]
            for r in spec_rows
            if r[spec_code_idx] and r[spec_code_idx] not in product_rp_set
        ]
        if spec_orphans:
            problems.append(
                f"**Специфікації з RP-кодом, якого немає у Products** ({len(spec_orphans)}): "
                + ", ".join(f"`{c}`" for c in spec_orphans[:10])
            )
    except StopIteration:
        pass

    # 7) Категорії — нестандартні значення
    catalog_categories = Counter(r[3] for r in variants_rows if r[3])
    problems.append(
        f"**Розподіл категорій у variants** (топ-10): "
        + ", ".join(f"`{c}`={n}" for c, n in catalog_categories.most_common(10))
    )

    if not problems:
        md_lines.append("- (нічого критичного не знайдено)")
    else:
        for p in problems:
            md_lines.append(f"- {p}")
    md_lines.append("")

    (OUT_DIR / "01_dictionaries_summary.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )

    # Підсумок у stdout (без юнікод-стрілок щоб не падати у cp1251)
    print()
    print("=== DONE ===")
    print(f"products_rp.csv     : {len(products_rows)} rows")
    print(f"customers.csv       : {len(customers_rows)} rows")
    print(f"variants.csv        : {len(variants_rows)} rows")
    print(f"specifications.csv  : {len(spec_rows)} rows")
    print(f"Report -> 01_dictionaries_summary.md")


if __name__ == "__main__":
    main()
