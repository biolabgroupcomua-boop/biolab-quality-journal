"""Обчислення висновку OK/OUT по варці.

Логіка: порівнюємо факт-показники з нормами специфікації. Якщо хоч одна
перевірка падає — OUT, інакше OK. Повертаємо також список причин для UI.

Автоматично перевіряємо:
- pH (числова перевірка діапазону)
- Колоїдна стабільність (текстова рівність)
- Термостабільність (текстова рівність)
- Загальне мікробіологічне число (текстова рівність)
- Дріжджі та плісняви (текстова рівність)

НЕ перевіряємо автоматично:
- В'язкість — норма рядкова ("S3V12 Cp=5000-8000 mPas"), парсити нестабільно
- Густина — норма рядкова ("0,9-1,0 г/мл")
- Зовнішній вигляд, колір, запах — органолептика на око технолога

Це залізне правило з CLAUDE.md розділ "Залізні правила обробки даних".
"""

from dataclasses import dataclass

from app.models.bulk_batch import VerdictEnum


@dataclass(frozen=True)
class VerdictResult:
    """Результат обчислення висновку.

    Attributes:
        verdict: OK або OUT.
        reasons: Перелік причин чому OUT (порожній якщо OK).
    """

    verdict: VerdictEnum
    reasons: list[str]


def calculate_verdict(
    *,
    ph_fact: float | None,
    ph_min: float | None,
    ph_max: float | None,
    colloid_fact: str | None,
    colloid_norm: str | None,
    thermo_fact: str | None,
    thermo_norm: str | None,
    micro_total_fact: str | None,
    micro_total_norm: str | None,
    micro_yeast_fact: str | None,
    micro_yeast_norm: str | None,
) -> VerdictResult:
    """Обчислити висновок OK/OUT по парах (факт, норма).

    Якщо норма або факт відсутні для якогось показника — пропускаємо його
    (не блокує висновок). Це навмисно: не всі показники вимірюються для
    кожного продукту, і не всі норми задані в специфікації.
    """
    reasons: list[str] = []

    # числова перевірка pH діапазону
    if ph_fact is not None and ph_min is not None and ph_max is not None:
        if not (ph_min <= ph_fact <= ph_max):
            reasons.append(f"pH факт {ph_fact} поза нормою [{ph_min}; {ph_max}]")

    # текстові перевірки — case-insensitive і з обрізанням пробілів
    text_checks = [
        ("Колоїдна стабільність", colloid_fact, colloid_norm),
        ("Термостабільність", thermo_fact, thermo_norm),
        ("Мікробіологія (загальна)", micro_total_fact, micro_total_norm),
        ("Мікробіологія (дріжджі)", micro_yeast_fact, micro_yeast_norm),
    ]
    for label, fact, norm in text_checks:
        if fact and norm and _normalize_text(fact) != _normalize_text(norm):
            reasons.append(f"{label}: факт {fact!r} ≠ норма {norm!r}")

    verdict = VerdictEnum.OUT if reasons else VerdictEnum.OK
    return VerdictResult(verdict=verdict, reasons=reasons)


def _normalize_text(value: str) -> str:
    """Нормалізація текстового показника для порівняння: lowercase + trim."""
    return value.strip().lower()
