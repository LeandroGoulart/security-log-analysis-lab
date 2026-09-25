# Especificação das regras (v1)

Parâmetros em [`config/rules.yaml`](../config/rules.yaml). Os valores padrão (5 falhas, 10 min, 30 min) são **didáticos**.

## Chave de correlação

As duas regras correlacionam eventos pela mesma chave:

```
(domain, user, src_ip, host)
```

- `domain`, `user` e `host` são comparados sem diferenciar maiúsculas e minúsculas. O `src_ip` usa a forma canônica.
- **Elegibilidade:** o evento precisa ter `domain`, `user` e `src_ip` (IP informado mas inválido já é rejeitado na validação). Eventos sem algum desses campos **não são avaliados** e aparecem contados por motivo no relatório. Eles nunca são agrupados como "origem desconhecida": juntar todas as origens ausentes criaria uma origem fictícia e alertas falsos.
- **O que a chave não cobre:** tentativas distribuídas entre várias origens (mesma conta, IPs diferentes), entre várias contas (mesma origem, contas diferentes, padrão compatível com password spraying) ou entre vários destinos. Isso é uma escolha do MVP, e a AUTH-002 está no roadmap.

## AUTH-001: Falhas repetidas de autenticação

**Dispara quando** há pelo menos `threshold` eventos 4625 elegíveis com a mesma chave em que `último − primeiro ≤ window_minutes`.

| Aspecto | Definição |
|---|---|
| Limite da janela | **Inclusivo**: falhas exatamente a `window_minutes` de distância entram |
| Ordem | Eventos ordenados por (timestamp UTC, EventRecordID quando houver, `event_uid`). A posição da linha no arquivo não influencia: entrada fora de ordem produz o mesmo resultado |
| Timestamps iguais | Ficam dentro da janela. O desempate reproduzível não cria relação de "antes/depois" para a AUTH-003 |
| Alertas repetidos | **Um alerta por episódio.** Depois do disparo, falhas seguintes com a mesma chave e intervalo ≤ `window_minutes` em relação à anterior são **agregadas** ao mesmo alerta |
| Novo episódio | Depois de um intervalo > `window_minutes` sem falha, a contagem recomeça do zero. Cada falha pertence a no máximo um alerta |
| Evento de disparo | A falha que completou o limiar (`is_trigger=yes` em `alert_evidence.csv`) |
| Duplicatas | Removidas antes da regra; não inflam a contagem |

## AUTH-003: Sucesso após falhas repetidas

**Dispara quando**, para um alerta AUTH-001, existe um 4624 elegível com a **mesma chave** que:

1. ocorre **estritamente depois** da falha que completou o limiar da AUTH-001; e
2. ocorre em até `success_within_minutes` após a **última falha anterior a ele** (limite inclusivo).

| Aspecto | Definição |
|---|---|
| Vínculo | `parent_alert_id` aponta para o AUTH-001 correspondente |
| Evidências | As falhas do AUTH-001 anteriores ao sucesso, mais o sucesso |
| Sucesso antes das falhas ou antes do limiar | Não dispara |
| Sucesso no **mesmo segundo** da falha de disparo | Não dispara: a ordem é indeterminada |
| Alertas repetidos | No máximo **um** AUTH-003 por AUTH-001 (o primeiro sucesso que se qualifica). Cada sucesso é usado por no máximo um AUTH-003 |
| Sucesso com IP ausente ou chave diferente | Não é correlacionado; aparece como não elegível ou simplesmente não casa |
| Dependência | AUTH-003 exige AUTH-001 habilitada (validado na configuração) |

## Ausência de alertas × insuficiência de dados

O relatório e o `summary.json` informam, por regra, os candidatos (eventos do tipo), os elegíveis e os motivos de não elegibilidade:

- **"Dados insuficientes"**: não há candidatos ou nenhum é elegível. Ausência de alerta **não** indica ausência de atividade.
- **"Cobertura parcial"**: parte dos candidatos não pôde ser avaliada.
- **"Nenhum padrão atingiu os critérios"**: todos os candidatos foram avaliados e nenhum formou sequência.

## Exceções

Não há exceções na v1: nenhuma conta, nenhum LogonType e nenhuma origem é ignorada. Excluir contas de serviço ou LogonType 3 de forma global esconderia ataques contra exatamente esses alvos. O cenário 3 discute como seria uma exceção aceitável (específica, justificada, temporária).

## Mapeamento MITRE ATT&CK (referência de estudo)

- AUTH-001 é compatível com [T1110.001 Brute Force: Password Guessing](https://attack.mitre.org/techniques/T1110/001/).
- AUTH-003 é compatível com a transição de T1110 para [T1078 Valid Accounts](https://attack.mitre.org/techniques/T1078/).

"Compatível" não quer dizer "confirmado": o mesmo padrão aparece em atividade legítima (cenários 1 e 3).
