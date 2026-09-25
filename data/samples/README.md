# Dataset exploratório: `auth_events.csv`

130 eventos **fictícios** (domínio `LAB`, IPs em faixas reservadas para documentação e `10.0.0.0/8`) de 21 e 22/09/2026, no formato de [`docs/formato-csv.md`](../../docs/formato-csv.md). Timestamps em UTC.

Este arquivo foi criado **antes** da v1, durante o planejamento, e inclui padrões de regras que ainda estão no roadmap. Ele **não** faz parte da demonstração: serve para explorar **o que a v1 detecta e o que ela não vê**.

```powershell
.\.venv\Scripts\python.exe -m authlab analyze --input data\samples\auth_events.csv --out output\exploratorio
```

## O que a v1 detecta (configuração padrão)

| Padrão no arquivo | v1 | Por quê |
|---|---|---|
| 15 falhas de `maria.souza` a partir de `203.0.113.45` em `SRV-APP-01` | **AUTH-001** | mesma chave, ≥ 5 em 10 min |
| 12 falhas de `joao.silva` a partir de `198.51.100.23` em `SRV-RDP-01` + sucesso | **AUTH-001 + AUTH-003** | idem, com sucesso 1 min depois |
| `203.0.113.77` testando 13 contas diferentes, 1 falha cada, e entrando como `carlos.lima` | **não detecta** | a chave inclui a conta; padrão compatível com password spraying (AUTH-002, roadmap) |
| Logon RDP de `ana.pereira` às 02:31 (horário de Brasília) | **não detecta** | AUTH-004 (fora do horário) está no roadmap |
| 6 falhas de `paulo.teixeira` espaçadas 20 min | **não detecta** | ataque lento: intervalo maior que a janela (limitação conhecida) |
| 4 falhas de `felipe.martins`; 4 de `gabriela.nunes` | **não detecta** | abaixo do limiar |
| Logons de `svc_backup` de madrugada | **não detecta** | não há regra para isso; não há exceção configurada |

Resultado esperado (verificado por teste): **2 × AUTH-001 e 1 × AUTH-003**.

## Códigos de status

O arquivo usa `0xC000006A` (senha incorreta), `0xC0000064` (conta inexistente) e, em um evento de `gabriela.nunes`, `0xC0000234`. Esse último **não consta** na tabela de códigos do evento 4625 na documentação da Microsoft usada pelo projeto ([referências](../../docs/referencias.md)), por isso a ferramenta o exibe como "falha de autenticação", sem interpretação. Uma versão anterior deste README o descrevia como "conta bloqueada" sem fonte documentada, e isso foi corrigido.
