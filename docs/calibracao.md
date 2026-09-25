# Exercício de calibração

**Objetivo:** ver na prática que mudar um limiar troca um tipo de erro por outro, e explicar esse custo.

Há duas configurações prontas em `config/exercicios/`. Elas são idênticas a `src/authlab/resources/config/rules.yaml`, exceto pelo `threshold` da AUTH-001.

## Passo a passo (PowerShell, na pasta do projeto, após instalar o app conforme o README)

```powershell
authlab demo --out output\calibracao-padrao
authlab demo --config config\exercicios\limiar-3.yaml --out output\calibracao-3
authlab demo --config config\exercicios\limiar-15.yaml --out output\calibracao-15
```

A demonstração compara cada cenário com o resultado esperado da configuração padrão. Com os limiares alterados, **diferenças são o objetivo do exercício** e aparecem como "DIFERENTE do esperado".

## Resultados obtidos com os dados fictícios (janela de 10 min)

| Cenário | Limiar 3 | Limiar 5 (padrão) | Limiar 15 |
|---|---|---|---|
| 1 – Erro de digitação (3 falhas) | AUTH-001 + AUTH-003 | nenhum | nenhum |
| 2 – Acesso suspeito (12 falhas em 5 min) | AUTH-001 + AUTH-003 | AUTH-001 + AUTH-003 | **nenhum** |
| 3 – Credencial de serviço (1 falha a cada 2 min) | AUTH-001 + AUTH-003 | AUTH-001 + AUTH-003 | **nenhum** (no máximo 6 falhas cabem em 10 min) |

## Perguntas para responder

1. Com limiar 3, o alerta do cenário 1 é útil? Em um ambiente com 500 pessoas, quantos alertas desse tipo você esperaria por dia? Quem vai analisá-los?
2. Com limiar 15, o cenário 2 deixa de alertar. Qual é o custo de perder esse caso, comparado ao custo de analisar alertas do cenário 1?
3. No cenário 3, a cadência de 1 falha a cada 2 min nunca atinge 15 falhas em 10 min. Aumentar a janela resolveria? O que mais mudaria com uma janela maior?
4. Que dado real você precisaria para escolher um limiar de forma fundamentada? (Pista: a distribuição de falhas por conta e origem no seu ambiente, durante algumas semanas.)

## O que este exercício **não** mostra

Os números acima vêm de **três cenários fictícios construídos para fins didáticos**. Eles não medem taxa de detecção nem de falsos positivos e não comprovam desempenho em produção. Calibrar de verdade exige dados do ambiente, período de observação e revisão dos alertas por pessoas.
