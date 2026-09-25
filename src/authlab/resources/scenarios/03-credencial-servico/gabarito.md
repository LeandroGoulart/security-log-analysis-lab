# Cenário 3 – Gabarito

## Fatos observados nos eventos

- Das 09:50 às 09:58: 5 sucessos 4624 de `LAB\svc_relatorios`, origem `10.20.5.15`, em `SRV-SQL-01`, LogonType 3 (Network), a cada 2 min.
- Das 10:00 às 10:58: 30 falhas 4625 com a mesma chave, **exatamente** a cada 2 min, `0xC000006D` / `0xC000006A` ("misspelled or bad password").
- A partir das 11:02:30: sucessos novamente a cada 2 min.
- O relatório aponta a regularidade dos intervalos como observação, sem concluir nada a partir dela.

## Por que um único alerta

A AUTH-001 disparou na 5ª falha (10:08). As falhas seguintes estão a 2 min uma da outra, dentro da janela de 10 min, e por isso foram agregadas ao mesmo alerta, em vez de gerar 26 alertas repetidos. A AUTH-003 usa o primeiro sucesso após o limiar (11:02:30). Os sucessos seguintes não geram novos alertas.

## A regra funcionou?

**Sim, exatamente como especificado.** Houve ≥ 5 falhas com a mesma chave em 10 min, seguidas de sucesso em até 30 min. A atividade, porém, é **legítima**: a senha foi trocada sem atualizar a aplicação (contexto). Nem todo alerta que dispara sobre atividade legítima significa uma regra "errada". A regra detecta um padrão, e cabe à investigação dar o significado.

O alerta também tem valor operacional: indica um serviço fora do ar e o risco de bloqueio da conta. A Microsoft recomenda monitorar eventos 4625 de contas de serviço, porque elas "should not be locked out or prevented from functioning".

## Hipóteses

| Hipótese | A favor | Contra |
|---|---|---|
| Credencial salva desatualizada | intervalos constantes; LogonType 3; origem é o servidor de aplicação; padrão sucesso → falha → sucesso casando com a mudança e o chamado | — |
| Força bruta contra conta de serviço | volume alto (30) | cadência perfeitamente regular e idêntica à operação normal; origem interna conhecida; mudança registrada |

## Conclusão sugerida

**Atividade legítima confirmada, com falha de processo. Prioridade de segurança baixa, prioridade operacional média.** Encerrar o alerta citando CHG-0042 e INC-1187 como evidência externa.

## Sobre exceções

Não criar exceção global para contas de serviço nem para LogonType 3: isso esconderia um ataque real contra essas contas. Se o ruído se repetir, uma exceção aceitável seria **específica** (conta + origem + destino), **justificada** (vinculada à mudança), **temporária** (com data de expiração) e **revisada**. A versão atual não implementa exceções.

## Melhoria de processo

Incluir no procedimento de rotação de senha a atualização das aplicações dependentes e uma verificação pós-mudança. Isso elimina a causa, em vez de silenciar o alerta.

## Resumo para gestor

"O alerta de quarta de manhã foi causado por uma troca de senha programada que não incluiu a atualização do sistema de relatórios. Os relatórios ficaram cerca de uma hora sem atualizar. Não houve incidente de segurança. Recomendamos incluir a atualização das aplicações no procedimento de troca de senha."

## Limitações

- Sem o contexto externo, os eventos sozinhos sustentariam "provável credencial desatualizada", mas não a confirmariam.
- Com janela de 1 min, cada falha ficaria isolada (intervalo de 2 min) e não haveria alerta: a cadência regular "escaparia" da regra.
