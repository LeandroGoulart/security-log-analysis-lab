# Cenário 1 – Gabarito

## Fatos observados nos eventos

- 11 registros lidos: 9 válidos, 1 rejeitado, 1 duplicado removido.
- Linha 10 (`daniel.rocha`) rejeitada: `2026-09-14 08:15:00` não tem fuso. Sem fuso, não dá para saber se é 08:15 em Brasília ou em UTC, uma diferença de 3 horas. A ferramenta rejeita em vez de adivinhar.
- Linha 8 é duplicata exata da linha 7: mesmo `host`, `channel` e `event_record_id` (58214), com o mesmo conteúdo.
- `LAB\carla.mendes` em `WS-017`: 3 falhas 4625 entre 08:02:10 e 08:02:41 (horário de Brasília), `Status=0xC000006D` / `SubStatus=0xC000006A`, LogonType 2 (Interactive), origem `127.0.0.1` (localhost). Sucesso 4624 às 08:02:58.
- Pela documentação da Microsoft, `0xC000006A` corresponde a "User logon with misspelled or bad password". `0xC000006D` é um código genérico ("bad username or authentication information").
- Linha 9: sucesso de `carla.mendes` em `SRV-FILE-01` com `src_ip` = `-`. A Microsoft documenta que o preenchimento dos campos de rede depende do protocolo e do contexto de autenticação. O evento é válido, mas não é elegível para correlação.

## Por que não houve alerta

A AUTH-001 exige pelo menos 5 falhas com a mesma chave em 10 minutos. Houve 3. A ausência de alerta aqui **tem valor**: os 3 eventos 4625 foram avaliados (cobertura de 3 de 3). A AUTH-003 avaliou 5 de 6 sucessos. O sucesso não avaliado não altera a conclusão, porque nenhuma sequência atingiu a AUTH-001.

## Hipóteses

| Hipótese | A favor | Contra |
|---|---|---|
| Erro de digitação | poucas falhas, curtíssimo intervalo, logon local na estação da própria pessoa, sucesso logo depois | nenhum |
| Tentativa de adivinhar a senha | nenhum sinal: volume baixo, logon local | exigiria acesso físico à estação |

## Conclusão sugerida

**Atividade legítima (baixa prioridade), sem ação.** A confirmação da usuária e o inventário (contexto externo) reforçam a conclusão, mas mesmo sem eles o padrão não justificaria investigação adicional.

A ação útil deste cenário é de **qualidade de dados**: corrigir a origem da linha sem fuso e a duplicação antes de usar o arquivo em análises.

## Resumo para gestor

"Revisamos os acessos de segunda de manhã. Houve três tentativas de senha incorreta seguidas de acesso normal, compatíveis com erro de digitação, confirmado pela usuária. Nenhuma ação necessária. Dois registros do arquivo tinham problemas de formato e foram separados para correção."

## Limitações

- A ferramenta não sabe que `WS-017` é da Carla; essa informação veio do inventário.
- Com limiar 3 ([`docs/calibracao.md`](../../docs/calibracao.md)), este cenário gera AUTH-001 e AUTH-003. A regra estaria funcionando, mas o alerta seria ruído. Esse é o custo de um limiar baixo.
