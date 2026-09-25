# Referências

## Documentação oficial da Microsoft (consultada em 25/09/2026)

- **4624(S): An account was successfully logged on**:
  https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624
- **4625(F): An account failed to log on**:
  https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625
- **NTSTATUS Values** (citada na página do 4625 para outros códigos):
  https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55

## O que foi extraído e como é usado

### Códigos de falha (tabela "Failure Information" do evento 4625)

A ferramenta interpreta **apenas** estes códigos. Qualquer outro aparece como "falha de autenticação", com o código preservado.

| Código | Texto original da Microsoft |
|---|---|
| `0xC000005E` | There are currently no logon servers available to service the logon request. |
| `0xC0000064` | User logon with misspelled or bad user account |
| `0xC000006A` | User logon with misspelled or bad password |
| `0xC000006D` | This is either due to a bad username or authentication information |
| `0xC000006F` | User logon outside authorized hours |
| `0xC0000070` | User logon from unauthorized workstation |
| `0xC0000072` | User logon to account disabled by administrator |
| `0xC000015B` | The user has not been granted the requested logon type (aka logon right) at this machine |
| `0xC0000192` | An attempt was made to logon, but the Netlogon service was not started |
| `0xC0000193` | User logon with expired account |
| `0xC0000413` | Logon Failure: The machine you are logging onto is protected by an authentication firewall. The specified account is not allowed to authenticate to the machine |

Quando o Status é o genérico `0xC000006D` e o SubStatus traz um código específico da tabela, a interpretação usa o SubStatus. Essa escolha é do projeto, não uma regra da Microsoft.

Outros códigos que aparecem em ambientes reais (por exemplo, relacionados a bloqueio de conta ou senha expirada) **não estão nessa tabela** e, por isso, não são interpretados. Consulte a página NTSTATUS Values antes de interpretá-los manualmente.

### Tipos de logon (tabela "Logon Types")

0 System · 2 Interactive · 3 Network · 4 Batch · 5 Service · 7 Unlock · 8 NetworkCleartext · 9 NewCredentials · 10 RemoteInteractive · 11 CachedInteractive · 12 CachedRemoteInteractive · 13 CachedUnlock

### Campos de rede

- **Source Network Address (`IpAddress`)**: "IP address of machine from which logon attempt was performed". Pode vir como IPv6 ou `::ffff:IPv4`. `::1` e `127.0.0.1` significam localhost.
- O preenchimento dos campos de rede depende do protocolo e do contexto de autenticação. Por isso a ferramenta trata `-` e vazio como ausência explícita.

### EventRecordID

As páginas consultadas mostram `EventRecordID` apenas no exemplo XML, sem garantia de unicidade. A estratégia do projeto (identificador por host + canal + EventRecordID) é uma **premissa documentada** em [decisoes.md](decisoes.md), não uma afirmação da Microsoft.

### Recomendação usada no cenário 3

Da seção de recomendações do 4625: "We recommend monitoring all 4625 events for service accounts, because these accounts should not be locked out or prevented from functioning."

## Outras referências

- MITRE ATT&CK T1110.001 (Password Guessing): https://attack.mitre.org/techniques/T1110/001/
- MITRE ATT&CK T1078 (Valid Accounts): https://attack.mitre.org/techniques/T1078/
- RFC 5737, faixas de IPv4 reservadas para documentação, usadas nos dados fictícios: https://www.rfc-editor.org/rfc/rfc5737
