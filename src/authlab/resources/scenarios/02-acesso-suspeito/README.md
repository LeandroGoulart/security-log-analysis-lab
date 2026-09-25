# Cenário 2 – Acesso suspeito

## Contexto inicial

Terça-feira, 15/09/2026. O servidor `SRV-RDP-01` é um servidor de acesso remoto (Remote Desktop) usado pela equipe administrativa. Na manhã de quarta, você recebe o lote de eventos do dia anterior para revisar.

## Perguntas orientadoras

1. Quais alertas foram gerados e como eles se relacionam (`parent_alert_id`)?
2. Qual é a chave de correlação do alerta (conta, domínio, IP de origem, host)? Quantas falhas, em quanto tempo e com quais códigos?
3. Compare o comportamento de `joao.silva` de manhã com o da noite: origem, horário, quantidade de falhas, tempo até o sucesso. O que muda?
4. Por que a falha das 09:00:14 **não** entrou no alerta?
5. O que os eventos **provam** e o que **não provam**? O IP `203.0.113.50` identifica quem estava do outro lado?
6. Quais informações você pediria antes de concluir? A quem?
7. Qual prioridade você daria, e por quê?
8. Com limiar 15 ([`docs/calibracao.md`](../../../../../docs/calibracao.md)), o que acontece com este cenário? O que isso ensina sobre limiares altos?

## Resultado esperado (configuração padrão)

| Indicador | Valor |
| --- | --- |
| Registros lidos / válidos | 18 / 18 |
| AUTH-001 | 1 alerta: 12 falhas de `LAB\joao.silva` a partir de `203.0.113.50` em `SRV-RDP-01` |
| AUTH-003 | 1 alerta vinculado: sucesso às 21:54:08 (horário de Brasília), cerca de 1 min após a última falha |

Depois de responder, leia [`contexto-investigacao.md`](contexto-investigacao.md) e, por fim, o [`gabarito.md`](gabarito.md).
