# -*- coding: utf-8 -*-
"""Витяг реєстру паспортів якості (вкладка 3) з JSON-дампу Google Sheet."""

import json
import csv
import re
from pathlib import Path
from collections import Counter

SRC = Path(r"C:\Users\nomer\.claude\projects\c--Users-nomer-biolab-librarian\9443d36b-7a03-498f-85f1-248958bc9fa4\tool-results\mcp-claude_ai_Google_Drive-read_file_content-1779366866558.txt")
OUT_DIR = Path(r"c:\Users\nomer\biolab-quality-journal\scripts\extraction_reports")
CSV_PATH = OUT_DIR / "quality_certificates.csv"
MD_PATH = OUT_DIR / "04_certificates_summary.md"

# Колонки CSV (англ)
COLUMNS = [
    "serial_no",
    "batch_number_gp",
    "date_mfg",
    "trademark_name",
    "product_name",
    "rp_code",
    "volume_fasuvannia",
    "batch_number_bulk",
    "date_expiry",
    "verdict",
    "passport_no",
    "generated_at",
    "status",
    "pdf_link",
]


def load_content() -> str:
    raw = SRC.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "fileContent" in obj:
            return obj["fileContent"]
    except json.JSONDecodeError:
        pass
    return raw


def find_sheet3(content: str) -> str:
    """Виокремлюємо текст 3-ї вкладки (Реєстр паспортів).

    У дампі немає заголовків вкладок — є лише підряд markdown-таблиці.
    Реєстр паспортів — це таблиця, чий header містить '№ партії ГП'.
    Закінчується на першому рядку, що не починається з '|'.
    """
    header_idx = content.find("№ партії ГП")
    if header_idx == -1:
        raise SystemExit("Не знайдено заголовок реєстру (№ партії ГП)")
    line_start = content.rfind("\n", 0, header_idx) + 1
    tail = content[line_start:]
    lines = tail.splitlines()
    # збираємо суцільний блок таблиці (рядки з '|')
    block: list[str] = []
    for ln in lines:
        if ln.startswith("|"):
            block.append(ln)
        else:
            if block:
                break
    return "\n".join(block)


def extract_link(cell: str) -> tuple[str, str]:
    """З markdown-комірки витягуємо (видимий_текст, url або '')."""
    cell = cell.strip()
    # формат [text](url)
    m = re.match(r"^\[(?P<text>[^\]]*)\]\((?P<url>[^)]+)\)$", cell)
    if m:
        return m.group("text").strip(), m.group("url").strip()
    return cell, ""


def parse_table(sheet_text: str) -> list[list[str]]:
    """Парсимо markdown-таблицю в список рядків (без заголовка/divider)."""
    rows: list[list[str]] = []
    header_seen = False
    divider_seen = False
    for raw_line in sheet_text.splitlines():
        line = raw_line.rstrip()
        if not line.startswith("|"):
            # таблиця могла закінчитись
            if header_seen and divider_seen and rows:
                # рядок не з таблиці після того як ми вже почали — пропускаємо, але не вихід
                # подальші рядки таблиці теж починаються з |, тому просто continue
                pass
            continue
        # розбиваємо комірки
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        # divider (---|---|...) або вирівнювальний (:-:, :--, --:, :---:, тощо)
        if parts and all(re.fullmatch(r":?-+:?", p) for p in parts if p):
            divider_seen = True
            continue
        if not header_seen:
            # перевіримо чи це заголовок реєстру
            joined = " | ".join(parts).lower()
            if "№ партії гп" in joined or "паспорт" in joined and "статус" in joined:
                header_seen = True
                continue
            # це може бути ще не наша таблиця — пропускаємо
            continue
        # це рядок даних
        rows.append(parts)
    return rows


def normalize_row(parts: list[str]) -> dict:
    # дозаповнимо/обріжемо до 14 колонок
    if len(parts) < 14:
        parts = parts + [""] * (14 - len(parts))
    elif len(parts) > 14:
        # склеїмо хвіст у останню колонку (бувають коми/труби у тексті)
        parts = parts[:13] + [" | ".join(parts[13:])]

    (
        serial_no,
        batch_gp,
        date_mfg,
        tm,
        product,
        rp,
        volume,
        batch_bulk,
        date_expiry,
        verdict,
        passport_no,
        generated_at,
        status,
        pdf_cell,
    ) = parts

    # прибираємо емоджі ✅/✓ з статусу, лишаємо лише текстову частину
    status_clean = status.replace("✅", "").replace("✓", "")
    status_clean = re.sub(r"\s+", " ", status_clean).strip()

    text, url = extract_link(pdf_cell)
    pdf_link = url if url else text

    return {
        "serial_no": serial_no,
        "batch_number_gp": batch_gp,
        "date_mfg": date_mfg,
        "trademark_name": tm,
        "product_name": product,
        "rp_code": rp,
        "volume_fasuvannia": volume,
        "batch_number_bulk": batch_bulk,
        "date_expiry": date_expiry,
        "verdict": verdict,
        "passport_no": passport_no,
        "generated_at": generated_at,
        "status": status_clean,
        "pdf_link": pdf_link,
    }


def write_csv(rows: list[dict]) -> None:
    # UTF-8 BOM, кома, лапки навколо рядків з комами (за замовч QUOTE_MINIMAL)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def year_from_mfg(s: str) -> str | None:
    s = s.strip()
    m = re.search(r"(\d{4})", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{2})\b", s[-3:])  # 2-значний рік у хвості
    if m:
        return "20" + m.group(1)
    return None


def is_november_2025(date_mfg: str) -> bool:
    s = date_mfg.strip()
    # формати: dd.mm.yyyy або dd/mm/yy(...) або dd/mm/yyyy
    m = re.match(r"^\s*(\d{1,2})[./](\d{1,2})[./](\d{2,4})", s)
    if not m:
        return False
    _d, mo, y = m.groups()
    if len(y) == 2:
        y = "20" + y
    return mo.lstrip("0") == "11" and y == "2025"


def passport_format(p: str) -> str:
    p = p.strip()
    if re.match(r"^ПУ-\d{2}/\d{2}/\d{2}\(\d+\)$", p):
        return "short"
    if re.match(r"^ПУ-\d{2}/\d{2}/\d{4}\(\d+\)$", p):
        return "long"
    return "other"


def main() -> None:
    content = load_content()
    sheet3 = find_sheet3(content)
    raw_rows = parse_table(sheet3)
    rows = [normalize_row(r) for r in raw_rows]

    # фільтруємо повністю порожні / "Тут будуть з'являтись..." підказки
    rows = [
        r for r in rows
        if r["passport_no"].strip() or r["batch_number_gp"].strip()
    ]

    write_csv(rows)

    # ----- статистика для звіту -----
    total = len(rows)

    years = [y for r in rows if (y := year_from_mfg(r["date_mfg"]))]
    period = ""
    if years:
        period = f"{min(years)} → {max(years)}"

    tms = {r["trademark_name"].strip() for r in rows if r["trademark_name"].strip()}
    rps = {r["rp_code"].strip() for r in rows if r["rp_code"].strip()}

    nov_2025 = [r for r in rows if is_november_2025(r["date_mfg"])]

    verdict_counter = Counter()
    for r in rows:
        v = r["verdict"].strip().upper()
        if v == "OK":
            verdict_counter["OK"] += 1
        elif v == "OUT":
            verdict_counter["OUT"] += 1
        elif v:
            verdict_counter[f"OTHER:{v}"] += 1
        else:
            verdict_counter["EMPTY"] += 1

    status_counter = Counter(r["status"].strip().lower() for r in rows)

    format_counter = Counter(passport_format(r["passport_no"]) for r in rows)
    other_passport_examples = [r["passport_no"] for r in rows if passport_format(r["passport_no"]) == "other"][:5]

    no_bulk = [r for r in rows if not r["batch_number_bulk"].strip()]
    out_examples = [
        f"{r['passport_no']} ({r['product_name']}, партія {r['batch_number_gp']})"
        for r in rows if r["verdict"].strip().upper() == "OUT"
    ][:10]
    out_count = sum(1 for r in rows if r["verdict"].strip().upper() == "OUT")
    no_pdf = [r for r in rows if not r["pdf_link"].strip() or r["pdf_link"].strip().lower() in {"-", "—"}]
    empty_tm = [r for r in rows if not r["trademark_name"].strip()]

    # перші 5 рядків CSV (превʼю)
    preview_lines = []
    with CSV_PATH.open("r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i >= 6:
                break
            preview_lines.append(line.rstrip("\n"))

    md = []
    md.append("# Витяг реєстру паспортів якості\n")
    md.append("## Загалом")
    md.append(f"- Згенерованих паспортів: {total}")
    md.append(f"- Період: {period}")
    md.append(f"- Унікальних ТМ: {len(tms)}")
    md.append(f"- Унікальних RP: {len(rps)}")
    md.append(f"- Паспортів за листопад 2025: {len(nov_2025)}\n")

    md.append("## За висновком")
    md.append(f"- OK: {verdict_counter.get('OK', 0)}")
    md.append(f"- OUT: {verdict_counter.get('OUT', 0)}")
    other_total = sum(v for k, v in verdict_counter.items() if k not in ("OK", "OUT"))
    md.append(f"- Інше: {other_total}")
    if other_total:
        md.append("  - розбивка:")
        for k, v in verdict_counter.items():
            if k not in ("OK", "OUT"):
                md.append(f"    - `{k}`: {v}")
    md.append("")

    md.append("## За статусом")
    sozdano = sum(v for k, v in status_counter.items() if "створено" in k)
    md.append(f"- створено: {sozdano}")
    other_statuses = [(k, v) for k, v in status_counter.items() if "створено" not in k]
    other_status_total = sum(v for _, v in other_statuses)
    md.append(f"- відкликано/інше: {other_status_total}")
    if other_statuses:
        for k, v in other_statuses:
            md.append(f"  - `{k or '(пусто)'}`: {v}")
    md.append("")

    md.append("## За форматом № паспорта")
    md.append(f"- `ПУ-DD/MM/YY(NN)`: {format_counter.get('short', 0)}")
    md.append(f"- `ПУ-DD/MM/YYYY(NN)`: {format_counter.get('long', 0)}")
    md.append(f"- інше: {format_counter.get('other', 0)}" + (
        f" (приклади: {', '.join(other_passport_examples)})" if other_passport_examples else ""
    ))
    md.append("")

    md.append("## Проблеми")
    md.append(f"- Паспорти без посилання на партію bulk: {len(no_bulk)}")
    md.append(f"- Паспорти OUT (теоретично не можна випускати, але в журналі є — чому?): {out_count}")
    if out_examples:
        md.append("  - приклади:")
        for ex in out_examples:
            md.append(f"    - {ex}")
    md.append(f"- Паспорти з відсутнім PDF-посиланням: {len(no_pdf)}")
    md.append(f"- Паспорти з порожнім ТМ: {len(empty_tm)}")
    md.append("")

    md.append("## Перші 5 рядків CSV (превʼю)")
    md.append("```")
    md.extend(preview_lines)
    md.append("```")

    MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")

    # короткий лог у консоль для агента
    print(f"CSV: {CSV_PATH}")
    print(f"MD : {MD_PATH}")
    print(f"rows: {total}")
    print(f"OUT: {out_count}")
    print(f"NOV2025: {len(nov_2025)}")
    print(f"no_bulk: {len(no_bulk)}")
    print(f"no_pdf: {len(no_pdf)}")
    print(f"empty_tm: {len(empty_tm)}")


if __name__ == "__main__":
    main()
