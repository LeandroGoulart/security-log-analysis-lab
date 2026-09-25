# Cenário 3 – Credencial de serviço desatualizada

## Contexto inicial

Quarta-feira, 16/09/2026. `SRV-SQL-01` é um servidor de banco de dados. A conta `LAB\svc_relatorios` é usada por uma aplicação de relatórios. Você recebe um alerta AUTH-001 e, em seguida, um AUTH-003 para essa conta.

## Perguntas orientadoras

1. Quantas falhas compõem o alerta AUTH-001? Por que há **um** alerta e não seis ou trinta?
2. Observe os intervalos entre as falhas. O que a regularidade sugere, e o que ela **não** prova?
3. Olhe o que acontece antes das 10:00 e depois das 11:02 com a mesma conta e origem. O que mudou?
4. O Status/SubStatus indica qual causa? O que a documentação da Microsoft recomenda sobre falhas de contas de serviço?
5. A regra funcionou conforme a especificação? O alerta é útil mesmo se a atividade for legítima?
6. Você criaria uma exceção para esta conta? Se sim, com quais limites (conta, origem, destino, prazo)? Por que uma exceção global para contas de serviço ou para LogonType 3 seria perigosa?
7. Qual melhoria de processo evitaria este alerta no futuro?

## Resultado esperado (configuração padrão)

| Indicador | Valor |
|---|---|
| Registros lidos / válidos | 40 / 40 |
| AUTH-001 | 1 alerta com 30 falhas (10:00–10:58, a cada 2 min) |
| AUTH-003 | 1 alerta: sucesso às 11:02:30, 4 min 30 s após a última falha |

Depois de responder, leia [`contexto-investigacao.md`](contexto-investigacao.md) e, por fim, o [`gabarito.md`](gabarito.md).
