"""Tests for predict batch helper functions and CSV validation."""

import pandas as pd
import pytest

from app.api.routes.predict_batch import (
    _normalize_header,
    _parse_interval_to_years,
    _to_bool,
    _validate_column_types,
    VALID_CATEGORICAL_VALUES,
)


class TestToBool:
    """Test _to_bool helper function."""

    def test_true_values(self):
        true_vals = ["ja", "yes", "vorhanden", "true", "1", "y", "JA", "YES"]
        for val in true_vals:
            assert _to_bool(val) is True, f"Expected True for '{val}'"

    def test_false_values(self):
        false_vals = ["nein", "no", "kein", "false", "0", "n", "NEIN", "NO"]
        for val in false_vals:
            assert _to_bool(val) is False, f"Expected False for '{val}'"

    def test_none_values(self):
        none_vals = [None, "", "nan", "none"]
        for val in none_vals:
            result = _to_bool(val)
            assert result is None or result is False, (
                f"Expected None or False for '{val}'"
            )

    def test_unknown_value_returns_none(self):
        assert _to_bool("maybe") is None
        assert _to_bool("unknown") is None


class TestParseIntervalToYears:
    """Test _parse_interval_to_years helper function."""

    def test_interval_mappings(self):
        assert _parse_interval_to_years("< 1 y") == 0.5
        assert _parse_interval_to_years("1-2 y") == 1.5
        assert _parse_interval_to_years("2-5 y") == 3.5
        assert _parse_interval_to_years("5-10 y") == 7.5
        assert _parse_interval_to_years("10-20 y") == 15.0
        assert _parse_interval_to_years("> 20 y") == 25.0

    def test_none_input(self):
        assert _parse_interval_to_years(None) is None

    def test_empty_values(self):
        assert _parse_interval_to_years("") is None
        assert _parse_interval_to_years("nan") is None
        assert _parse_interval_to_years("nicht erhoben") is None
        assert _parse_interval_to_years("unbekannt") is None
        assert _parse_interval_to_years("unbekannt/ka") is None

    def test_numeric_string(self):
        assert _parse_interval_to_years("5") == 5.0
        assert _parse_interval_to_years("10.5") == 10.5

    def test_invalid_string_returns_none(self):
        assert _parse_interval_to_years("invalid") is None


class TestNormalizeHeader:
    """Test _normalize_header helper function."""

    def test_basic_normalization(self):
        assert _normalize_header("Age") == "age"
        assert _normalize_header("  Age  ") == "age"
        assert _normalize_header("ALTER") == "alter"
        assert _normalize_header("  Alter [J]  ") == "alter [j]"

    def test_bom_removal(self):
        assert _normalize_header("\ufeffAge") == "age"
        assert _normalize_header("\ufeff\ufeffTest") == "test"
        assert _normalize_header("\ufeffAlter") == "alter"

    def test_none_input(self):
        assert _normalize_header(None) == ""

    def test_preserves_special_chars(self):
        assert _normalize_header("Alter [J]") == "alter [j]"
        assert _normalize_header("Primäre Sprache") == "primäre sprache"


class TestValidateColumnTypes:
    """Test _validate_column_types for CSV uploads."""

    def test_valid_numeric_column(self):
        df = pd.DataFrame({"Alter [J]": [25, 30, 45.5]})
        errors = _validate_column_types(df)
        assert errors == []

    def test_invalid_numeric_column(self):
        df = pd.DataFrame({"Alter [J]": [25, "abc", 45]})
        errors = _validate_column_types(df)
        assert len(errors) == 1
        assert "non-numeric" in errors[0]

    def test_valid_categorical_column(self):
        df = pd.DataFrame({"Geschlecht": ["m", "w", "d"]})
        errors = _validate_column_types(df)
        assert errors == []

    def test_invalid_categorical_column(self):
        df = pd.DataFrame({"Geschlecht": ["m", "invalid_value", "w"]})
        errors = _validate_column_types(df)
        assert len(errors) == 1
        assert "invalid values" in errors[0]

    def test_unknown_column_skipped(self):
        df = pd.DataFrame({"UnknownColumn": ["anything", "goes", "here"]})
        errors = _validate_column_types(df)
        assert errors == []

    def test_empty_dataframe(self):
        df = pd.DataFrame({"Alter [J]": pd.Series([], dtype=float)})
        errors = _validate_column_types(df)
        assert errors == []
