"""Interpretação de campos dos eventos 4624/4625 do Windows.

Fonte: documentação da Microsoft (ver docs/referencias.md):
- Event 4624(S): An account was successfully logged on.
- Event 4625(F): An account failed to log on.

Só interpretamos códigos que constam na tabela de "Failure Information" do
evento 4625. Qualquer outro código é exibido como "falha de autenticação"
e o valor original é preservado. Não inferimos significados.
"""

from __future__ import annotations

MS_4624_URL = (
    "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/"
    "security/threat-protection/auditing/event-4624"
)
MS_4625_URL = (
    "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/"
    "security/threat-protection/auditing/event-4625"
)

EVENT_NAMES = {
    4624: "Logon bem-sucedido",
    4625: "Falha de logon",
}

# Tabela "Logon Types" (eventos 4624/4625). Nome original + tradução livre.
LOGON_TYPES = {
    0: ("System", "usado apenas pela conta System, por exemplo na inicialização"),
    2: ("Interactive", "logon local neste computador"),
    3: ("Network", "acesso a este computador pela rede (ex.: pasta compartilhada)"),
    4: ("Batch", "processo em lote executado em nome de uma conta"),
    5: ("Service", "serviço iniciado pelo Service Control Manager"),
    7: ("Unlock", "desbloqueio da estação"),
    8: ("NetworkCleartext", "logon pela rede com senha repassada sem hash ao pacote de autenticação"),
    9: ("NewCredentials", "credenciais diferentes para conexões de saída"),
    10: ("RemoteInteractive", "logon remoto via Remote Desktop / Terminal Services"),
    11: ("CachedInteractive", "logon com credenciais em cache, sem contatar o controlador de domínio"),
    12: ("CachedRemoteInteractive", "igual a RemoteInteractive; usado para auditoria interna"),
    13: ("CachedUnlock", "logon de estação"),
}

# Tabela de Status/SubStatus do evento 4625 (Microsoft). Tradução livre;
# o texto original está em docs/referencias.md.
FAILURE_CODES = {
    "0xC000005E": "não havia servidores de logon disponíveis para atender a solicitação "
                  "(segundo a Microsoft, costuma ser questão de infraestrutura/disponibilidade)",
    "0xC0000064": "nome de conta inexistente ou digitado incorretamente",
    "0xC000006A": "senha incorreta ou digitada incorretamente",
    "0xC000006D": "nome de usuário ou informação de autenticação incorretos (código genérico)",
    "0xC000006F": "logon fora do horário autorizado",
    "0xC0000070": "logon a partir de estação não autorizada",
    "0xC0000072": "conta desabilitada pelo administrador",
    "0xC000015B": "a conta não tem o tipo de logon (direito de logon) solicitado nesta máquina",
    "0xC0000192": "o serviço Netlogon não estava iniciado "
                  "(segundo a Microsoft, costuma ser questão de infraestrutura/disponibilidade)",
    "0xC0000193": "conta expirada",
    "0xC0000413": "máquina protegida por firewall de autenticação; a conta não pode autenticar nela",
}

GENERIC_STATUS = "0xC000006D"


def logon_type_label(value: int | None) -> str:
    if value is None:
        return "não informado"
    if value in LOGON_TYPES:
        name, desc = LOGON_TYPES[value]
        return f"{value} ({name}: {desc})"
    return f"{value} (tipo não documentado na tabela usada)"


def logon_type_short(value: int | None) -> str:
    if value is None:
        return "não informado"
    if value in LOGON_TYPES:
        return f"{value} ({LOGON_TYPES[value][0]})"
    return str(value)


def failure_reason(status: str | None, sub_status: str | None) -> str:
    """Interpretação conservadora de uma falha 4625.

    Regra: o SubStatus é mais específico quando o Status é o genérico
    0xC000006D. Sem código documentado, devolve "falha de autenticação".
    """
    candidates = []
    if sub_status and sub_status not in ("0x0",):
        candidates.append(sub_status)
    if status:
        candidates.append(status)
    # Preferimos um código específico (diferente do genérico) quando houver.
    for code in candidates:
        if code in FAILURE_CODES and code != GENERIC_STATUS:
            return FAILURE_CODES[code]
    for code in candidates:
        if code in FAILURE_CODES:
            return FAILURE_CODES[code]
    return "falha de autenticação (código sem interpretação documentada nesta ferramenta)"


def codes_text(status: str | None, sub_status: str | None) -> str:
    return f"Status={status or 'não informado'} / SubStatus={sub_status or 'não informado'}"
