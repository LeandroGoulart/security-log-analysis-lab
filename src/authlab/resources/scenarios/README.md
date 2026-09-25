# Cenários didáticos

Três conjuntos de dados **inteiramente fictícios e determinísticos** (domínio `LAB`, rede interna fictícia `10.20.0.0/16`, IPs externos em faixas reservadas para documentação pela RFC 5737).

| Cenário | O que exercita | Alertas esperados (config padrão) |
| --- | --- | --- |
| [01-erro-digitacao](01-erro-digitacao/README.md) | Falhas abaixo do limiar; qualidade de dados (rejeição, duplicata, IP ausente) | nenhum |
| [02-acesso-suspeito](02-acesso-suspeito/README.md) | AUTH-001 + AUTH-003 com sinais que exigem escalonamento | 1 × AUTH-001, 1 × AUTH-003 |
| [03-credencial-servico](03-credencial-servico/README.md) | Regra funcionando conforme especificado sobre atividade legítima | 1 × AUTH-001, 1 × AUTH-003 |

## Como estudar cada cenário

1. Rode a demonstração: `authlab demo` (veja o README principal).
2. Leia o `README.md` do cenário: contexto inicial e perguntas orientadoras.
3. Abra o relatório em `output/demo/<cenário>/report.html`.
4. Preencha uma cópia de [`docs/ficha-investigacao.md`](../../../../docs/ficha-investigacao.md).
5. Só então leia `contexto-investigacao.md` (informações que você "obteve" ao investigar) e reavalie.
6. Por último, compare com o `gabarito.md`.

## Arquivos de cada cenário

| Arquivo | Conteúdo |
| --- | --- |
| `events.csv` | Eventos no formato de [`docs/formato-csv.md`](../../../../docs/formato-csv.md) |
| `scenario.json` | Título, descrição e resultado esperado (usado pela demonstração e pelos testes) |
| `README.md` | Contexto inicial, perguntas orientadoras, resultado esperado |
| `contexto-investigacao.md` | Informações fictícias **externas aos eventos** (entrevistas, registros de mudança) |
| `gabarito.md` | Raciocínio, conclusão sugerida e limitações |

> As informações de `contexto-investigacao.md` **não estão nos eventos**. Elas simulam o que um analista obteria perguntando a pessoas ou consultando outros sistemas. Numa investigação real, cada uma delas precisaria de fonte e registro.
