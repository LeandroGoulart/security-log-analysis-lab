"""Configuração inválida gera mensagens compreensíveis."""

import copy

import pytest

from authlab.config import ConfigError, load_config, parse_config

from conftest import ROOT

VALID = {
    "display": {"timezone_label": "Teste", "utc_offset": "-03:00"},
    "rules": {
        "AUTH-001": {"enabled": True, "threshold": 5, "window_minutes": 10},
        "AUTH-003": {"enabled": True, "success_within_minutes": 30},
    },
}


def mutate(path, value):
    data = copy.deepcopy(VALID)
    target = data
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return data


def test_shipped_config_is_valid():
    cfg = load_config(ROOT / "config" / "rules.yaml")
    assert cfg.auth001.threshold >= 2


@pytest.mark.parametrize("path,value,message", [
    (("rules", "AUTH-001", "threshold"), 0, "entre 2 e"),
    (("rules", "AUTH-001", "threshold"), "cinco", "número inteiro"),
    (("rules", "AUTH-001", "threshold"), True, "número inteiro"),
    (("rules", "AUTH-001", "window_minutes"), -1, "entre 1 e"),
    (("rules", "AUTH-003", "success_within_minutes"), 2.5, "número inteiro"),
    (("rules", "AUTH-001", "enabled"), "sim", "true ou false"),
    (("rules", "AUTH-001", "threshold"), KeyError, "faltam os campos obrigatórios: threshold"),
    (("rules", "AUTH-001", "treshold"), 5, "campos desconhecidos: treshold"),
    (("display", "utc_offset"), "-3", r"\+HH:MM"),
    (("rules",), [], "mapeamento"),
])
def test_invalid_values_are_explained(path, value, message):
    with pytest.raises(ConfigError, match=message):
        parse_config(mutate(path, value))


def test_auth003_requires_auth001():
    data = mutate(("rules", "AUTH-001", "enabled"), False)
    with pytest.raises(ConfigError, match="depende de AUTH-001"):
        parse_config(data)


def test_missing_file_and_invalid_yaml(tmp_path):
    with pytest.raises(ConfigError, match="não encontrado"):
        load_config(tmp_path / "x.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("rules: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML válido"):
        load_config(bad)
