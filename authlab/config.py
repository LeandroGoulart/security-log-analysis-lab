"""Leitura e validação de config/rules.yaml.

Toda configuração inválida gera ConfigError com mensagem em português,
indicando o campo e o valor esperado. Nenhum valor tem padrão implícito:
o arquivo precisa declarar tudo, para que o analista saiba o que foi usado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True)
class Auth001Config:
    enabled: bool
    threshold: int
    window_minutes: int

    @property
    def window(self) -> timedelta:
        return timedelta(minutes=self.window_minutes)


@dataclass(frozen=True)
class Auth003Config:
    enabled: bool
    success_within_minutes: int

    @property
    def interval(self) -> timedelta:
        return timedelta(minutes=self.success_within_minutes)


@dataclass(frozen=True)
class Config:
    display_timezone_label: str
    display_utc_offset: str
    auth001: Auth001Config
    auth003: Auth003Config
    source_path: str = ""

    @property
    def display_tz(self) -> timezone:
        sign = 1 if self.display_utc_offset[0] == "+" else -1
        hours, minutes = self.display_utc_offset[1:].split(":")
        return timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))


_OFFSET_RE = re.compile(r"^[+-](0\d|1[0-4]):[0-5]\d$")


def _require_mapping(value, where: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"'{where}' deve ser um bloco de chaves (mapeamento YAML).")
    return value


def _check_keys(block: dict, allowed: set[str], where: str) -> None:
    missing = sorted(allowed - block.keys())
    unknown = sorted(block.keys() - allowed)
    if missing:
        raise ConfigError(f"Em '{where}', faltam os campos obrigatórios: {', '.join(missing)}.")
    if unknown:
        raise ConfigError(
            f"Em '{where}', campos desconhecidos: {', '.join(map(str, unknown))}. "
            "Verifique erros de digitação."
        )


def _bool(value, where: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"'{where}' deve ser true ou false (recebido: {value!r}).")
    return value


def _int(value, where: str, minimum: int, maximum: int) -> int:
    # bool é subclasse de int em Python; rejeitamos explicitamente.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"'{where}' deve ser um número inteiro (recebido: {value!r}).")
    if not minimum <= value <= maximum:
        raise ConfigError(
            f"'{where}' deve estar entre {minimum} e {maximum} (recebido: {value})."
        )
    return value


def parse_config(data, source_path: str = "") -> Config:
    root = _require_mapping(data, "raiz do arquivo")
    _check_keys(root, {"display", "rules"}, "raiz do arquivo")

    display = _require_mapping(root["display"], "display")
    _check_keys(display, {"timezone_label", "utc_offset"}, "display")
    label = display["timezone_label"]
    if not isinstance(label, str) or not label.strip():
        raise ConfigError("'display.timezone_label' deve ser um texto não vazio.")
    offset = display["utc_offset"]
    if not isinstance(offset, str) or not _OFFSET_RE.match(offset):
        raise ConfigError(
            "'display.utc_offset' deve seguir o formato +HH:MM ou -HH:MM, entre aspas "
            f"(ex.: \"-03:00\"). Recebido: {offset!r}."
        )

    rules = _require_mapping(root["rules"], "rules")
    _check_keys(rules, {"AUTH-001", "AUTH-003"}, "rules")

    r1 = _require_mapping(rules["AUTH-001"], "rules.AUTH-001")
    _check_keys(r1, {"enabled", "threshold", "window_minutes"}, "rules.AUTH-001")
    a1 = Auth001Config(
        enabled=_bool(r1["enabled"], "rules.AUTH-001.enabled"),
        threshold=_int(r1["threshold"], "rules.AUTH-001.threshold", 2, 10_000),
        window_minutes=_int(r1["window_minutes"], "rules.AUTH-001.window_minutes", 1, 1440),
    )

    r3 = _require_mapping(rules["AUTH-003"], "rules.AUTH-003")
    _check_keys(r3, {"enabled", "success_within_minutes"}, "rules.AUTH-003")
    a3 = Auth003Config(
        enabled=_bool(r3["enabled"], "rules.AUTH-003.enabled"),
        success_within_minutes=_int(
            r3["success_within_minutes"], "rules.AUTH-003.success_within_minutes", 1, 1440
        ),
    )
    if a3.enabled and not a1.enabled:
        raise ConfigError(
            "AUTH-003 depende de AUTH-001: habilite AUTH-001 ou desabilite AUTH-003."
        )

    return Config(
        display_timezone_label=label.strip(),
        display_utc_offset=offset,
        auth001=a1,
        auth003=a3,
        source_path=source_path,
    )


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Arquivo de configuração não encontrado: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} não é um YAML válido: {exc}") from exc
    # Caminho exibido no relatório: relativo, para não expor a estrutura de pastas local.
    try:
        shown = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        shown = path.name
    return parse_config(data, source_path=shown)
