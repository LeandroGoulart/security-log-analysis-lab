# Cenário 1 – Erro de digitação

## Contexto inicial

Segunda-feira, 14/09/2026, início do expediente. Você recebeu o arquivo `events.csv` com eventos de logon de algumas estações e do servidor de arquivos `SRV-FILE-01`. Não há chamado aberto nem alerta prévio: a tarefa é revisar o lote e decidir se algo merece investigação.

O arquivo foi montado à mão por outra pessoa da equipe, e ela avisou que "pode ter alguma linha estranha".

## Perguntas orientadoras

1. Quantos registros foram lidos, quantos são válidos e o que aconteceu com os demais? Encontre a linha de cada rejeição e de cada duplicata.
2. A conta `carla.mendes` teve falhas. Quantas, em quanto tempo e com qual Status/SubStatus? O que a documentação da Microsoft diz sobre esses códigos?
3. Por que a AUTH-001 não disparou? O que teria de ser diferente para disparar?
4. Um evento de sucesso não foi avaliado pela AUTH-003. Qual e por quê? Isso muda a sua conclusão?
5. "Nenhum alerta" significa "nada aconteceu"? O que o relatório diz sobre a cobertura?
6. Rode o exercício de calibração com limiar 3 ([`docs/calibracao.md`](../../../../../docs/calibracao.md)). O alerta que aparece é útil ou é ruído? Qual o custo de manter esse limiar em um ambiente com centenas de usuários?

## Resultado esperado (configuração padrão)

| Indicador | Valor |
| --- | --- |
| Registros lidos | 11 |
| Válidos | 9 |
| Rejeitados | 1 (linha 10: timestamp sem fuso) |
| Duplicados removidos | 1 (linha 8 repete a linha 7) |
| AUTH-001 | 0 alertas (3 falhas, limiar 5) |
| AUTH-003 | 0 alertas; 1 sucesso não elegível (IP ausente, linha 9) |

Depois de responder, leia [`contexto-investigacao.md`](contexto-investigacao.md) e, por fim, o [`gabarito.md`](gabarito.md).
