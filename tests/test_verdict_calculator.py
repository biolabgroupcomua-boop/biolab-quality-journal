"""Тести для verdict_calculator.

Висновок OK/OUT — критична логіка, бо саме на ній стоїть рішення про
випуск партії на ринок. Тестуємо детально.
"""

from app.models.bulk_batch import VerdictEnum
from app.services.verdict_calculator import calculate_verdict


def _empty_kwargs() -> dict:
    """Базова всі-пусто конфігурація — пропускає всі перевірки → OK."""
    return {
        "ph_fact": None,
        "ph_min": None,
        "ph_max": None,
        "colloid_fact": None,
        "colloid_norm": None,
        "thermo_fact": None,
        "thermo_norm": None,
        "micro_total_fact": None,
        "micro_total_norm": None,
        "micro_yeast_fact": None,
        "micro_yeast_norm": None,
    }


def test_all_empty_returns_ok() -> None:
    """Якщо ніяких даних нема — повертаємо OK без причин."""
    result = calculate_verdict(**_empty_kwargs())
    assert result.verdict == VerdictEnum.OK
    assert result.reasons == []


def test_ph_within_range_is_ok() -> None:
    kwargs = _empty_kwargs() | {"ph_fact": 5.5, "ph_min": 5.0, "ph_max": 6.0}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_ph_at_boundary_min_is_ok() -> None:
    """Межі включні: pH = ph_min → OK."""
    kwargs = _empty_kwargs() | {"ph_fact": 5.0, "ph_min": 5.0, "ph_max": 6.0}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_ph_at_boundary_max_is_ok() -> None:
    kwargs = _empty_kwargs() | {"ph_fact": 6.0, "ph_min": 5.0, "ph_max": 6.0}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_ph_above_max_is_out() -> None:
    kwargs = _empty_kwargs() | {"ph_fact": 7.2, "ph_min": 5.0, "ph_max": 6.0}
    result = calculate_verdict(**kwargs)
    assert result.verdict == VerdictEnum.OUT
    assert len(result.reasons) == 1
    assert "pH" in result.reasons[0]


def test_ph_below_min_is_out() -> None:
    kwargs = _empty_kwargs() | {"ph_fact": 4.5, "ph_min": 5.0, "ph_max": 6.0}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OUT


def test_ph_missing_fact_skipped() -> None:
    """pH ще не вимірили — це не блокує. Можливо потім додадуть."""
    kwargs = _empty_kwargs() | {"ph_fact": None, "ph_min": 5.0, "ph_max": 6.0}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_ph_missing_norm_skipped() -> None:
    """У специфікації норми не задані — пропускаємо перевірку."""
    kwargs = _empty_kwargs() | {"ph_fact": 7.0, "ph_min": None, "ph_max": None}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_colloid_match_is_ok() -> None:
    kwargs = _empty_kwargs() | {"colloid_fact": "стабільний", "colloid_norm": "стабільний"}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_colloid_case_insensitive() -> None:
    """Порівняння без урахування регістру і зайвих пробілів."""
    kwargs = _empty_kwargs() | {"colloid_fact": "  Стабільний ", "colloid_norm": "стабільний"}
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OK


def test_colloid_mismatch_is_out() -> None:
    kwargs = _empty_kwargs() | {"colloid_fact": "нестабільний", "colloid_norm": "стабільний"}
    result = calculate_verdict(**kwargs)
    assert result.verdict == VerdictEnum.OUT
    assert "Колоїдна стабільність" in result.reasons[0]


def test_micro_yeast_mismatch_is_out() -> None:
    kwargs = _empty_kwargs() | {
        "micro_yeast_fact": "виявлено",
        "micro_yeast_norm": "не виявлено",
    }
    assert calculate_verdict(**kwargs).verdict == VerdictEnum.OUT


def test_multiple_failures_collected() -> None:
    """Якщо одразу кілька показників падають — всі причини в списку."""
    kwargs = _empty_kwargs() | {
        "ph_fact": 8.0,
        "ph_min": 5.0,
        "ph_max": 6.0,
        "colloid_fact": "нестабільний",
        "colloid_norm": "стабільний",
        "micro_total_fact": "виявлено",
        "micro_total_norm": "не виявлено",
    }
    result = calculate_verdict(**kwargs)
    assert result.verdict == VerdictEnum.OUT
    assert len(result.reasons) == 3
