# Ficha de investigação

> Copie este arquivo (por exemplo, para `output/fichas/AUTH-001-xxxx.md`; a pasta `output/` não é versionada) e preencha. Nunca coloque dados reais em arquivos versionados.
>
> Regra de ouro: separe o que **foi observado** do que **você supõe**. "Inconclusiva" é uma conclusão válida quando falta informação.

## 1. Identificação

| Campo | Valor |
|---|---|
| Alerta(s) | `AUTH-___-________` |
| Alerta relacionado (pai/filho) | |
| Execução (`run_id`) e arquivo de entrada | |
| Analista | |
| Data/hora da análise (com fuso) | |

## 2. Fatos observados

_Somente o que está nos eventos. Sem interpretação._

- Conta (domínio\usuário):
- IP de origem:
- Host que registrou (destino):
- Quantidade de falhas, período e intervalo:
- Status/SubStatus e o significado documentado:
- LogonType:
- Houve sucesso? Quando, e quanto tempo após a última falha?

## 3. Evidências

| event_uid | Horário (UTC) | Evento | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| | | | | |

## 4. Hipóteses

| Hipótese | Evidências a favor | Evidências contra | Como testar |
|---|---|---|---|
| Atividade legítima: ___ | | | |
| Atividade maliciosa: ___ | | | |
| Outra: ___ | | | |

## 5. Informações faltantes

_O que você precisa saber e onde conseguiria. Registre a fonte de cada resposta obtida._

- [ ] O responsável pela conta reconhece a atividade? (canal independente)
- [ ] A quem o IP estava atribuído no horário? (DHCP, VPN, inventário)
- [ ] Houve mudança, manutenção ou teste agendado?
- [ ] O que ocorreu depois do logon bem-sucedido?
- [ ] ___

## 6. Prioridade

- [ ] Alta
- [ ] Média
- [ ] Baixa

Justificativa (impacto possível + confiança nas evidências):

## 7. Conclusão

- [ ] Atividade legítima confirmada (cite a evidência externa)
- [ ] Suspeita confirmada: escalar como incidente
- [ ] Inconclusiva (diga o que falta para concluir)

Fundamentação:

## 8. Próximo passo

_Ação concreta, responsável e prazo._

## 9. Resumo para gestor

_No máximo 4 frases, sem jargão: o que aconteceu, o que isso significa, o que foi/será feito, se há impacto._
