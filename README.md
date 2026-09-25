# Security Log Analysis Lab: Investigação de autenticação Windows

Laboratório de estudo de **SOC / Blue Team** para interpretar eventos de autenticação do Windows (`4624` e `4625`), correlacioná-los, investigar hipóteses e comunicar conclusões. O público inclui pessoas sem formação técnica.

O projeto implementa, de forma transparente e testável, uma fatia do que um SIEM faz:

```
CSV documentado → validação e normalização → detecção → evidências → relatório HTML local
```

Ele **não** substitui um SIEM: não há coleta contínua, armazenamento em escala nem resposta automática. O foco está na lógica: por que uma regra dispara, quais eventos a sustentam, quando o alerta é ruído e como explicar isso a quem decide.

> **Iniciante?** Comece pelo [guia do projeto](docs/README.md). O andamento está no [checklist](docs/CHECKLIST.md).

> Todos os dados incluídos são **fictícios**. Os limiares padrão são **didáticos** e não servem para nenhum ambiente real sem calibração.

## Competências praticadas

| Competência | Onde aparece |
|---|---|
| Interpretar logs de autenticação Windows | Status/SubStatus e LogonType com base na documentação da Microsoft ([referências](docs/referencias.md)) |
| Triagem e correlação | AUTH-001 e AUTH-003 com chave de correlação explícita ([regras](docs/regras.md)) |
| Investigar hipóteses e falsos positivos | 3 cenários com perguntas e gabarito, incluindo um alerta sobre atividade legítima |
| Decidir com base em evidências | Cada alerta aponta para `event_uid` e `arquivo:linha` de origem |
| Automação básica com Python | Pipeline sem frameworks, com 87 testes |
| Comunicação | Resumo em linguagem simples por alerta e [ficha de investigação](docs/ficha-investigacao.md) com resumo para gestor |

## Início rápido (Windows / PowerShell)

Pré-requisitos: **Python 3.10 ou superior** ([python.org](https://www.python.org/downloads/); marque "Add python.exe to PATH" na instalação) e Git. Não precisa de privilégios de administrador.

```powershell
git clone https://github.com/LeandroGoulart/security-log-analysis-lab.git
cd security-log-analysis-lab
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m authlab demo --open
```

- Se o comando `py` não existir, use `python -m venv .venv`.
- Os comandos chamam `.\.venv\Scripts\python.exe` diretamente, sem ativar o ambiente, para evitar o bloqueio de scripts do PowerShell (`Activate.ps1`).
- `--open` abre o índice no navegador padrão. Sem ele, abra `output\demo\index.html` manualmente.

> **Estado da verificação:** no Windows com Python 3.13, as dependências foram instaladas em `.venv`, os 87 testes passaram e `demo --strict` conferiu os três cenários. Veja [Pendências](#limitações-e-pendências).

### Exemplo de resultado

```
[02-acesso-suspeito] Cenário 2 – Acesso suspeito
  Registros: lidos 18 | válidos 18 | rejeitados 0 | duplicados removidos 0 | possíveis duplicados mantidos 0
  AUTH-001: candidatos 13 | elegíveis 13 | alertas 1
    1 alerta(s). Avaliados 13 de 13 eventos candidatos.
  AUTH-003: candidatos 5 | elegíveis 5 | alertas 1
    1 alerta(s). Avaliados 5 de 5 eventos candidatos.
  Conferência: conforme o esperado
  Relatório: output/demo/02-acesso-suspeito/report.html
```

No relatório, cada alerta traz:

> **Em linguagem simples:** Foram registradas 12 falhas de autenticação para a conta joao.silva em 5 min 1 s, seguidas de um logon bem-sucedido com os mesmos campos de correlação. A sequência pode ter uma explicação legítima ou indicar tentativa de acesso indevido. É necessário verificar o contexto antes de concluir.

Em seguida vêm: o que foi observado, por que a regra disparou, explicações possíveis, o que verificar e a linha do tempo com as evidências.

## Cenários

| Cenário | Lição | Alertas |
|---|---|---|
| [1 – Erro de digitação](scenarios/01-erro-digitacao/README.md) | Abaixo do limiar; qualidade de dados; "sem alerta" com cobertura | nenhum |
| [2 – Acesso suspeito](scenarios/02-acesso-suspeito/README.md) | Falhas + sucesso de origem não reconhecida | AUTH-001 + AUTH-003 |
| [3 – Credencial de serviço](scenarios/03-credencial-servico/README.md) | A regra funciona conforme a especificação e ainda assim alerta sobre atividade legítima | AUTH-001 + AUTH-003 |

Cada cenário tem contexto, CSV, perguntas orientadoras, resultado esperado, contexto de investigação (fictício, externo aos eventos) e gabarito separado. Veja [como estudar os cenários](scenarios/README.md).

## Regras (resumo)

A chave de correlação das duas regras é **domínio + conta + IP de origem + host que registrou**.

| Regra | Dispara quando | Não cobre |
|---|---|---|
| **AUTH-001** – Falhas repetidas | ≥ 5 eventos 4625 com a mesma chave em até 10 min (limite inclusivo). Um alerta por episódio | tentativas distribuídas entre origens, contas ou destinos; ataques mais lentos que a janela |
| **AUTH-003** – Sucesso após falhas | 4624 com a mesma chave, depois da falha que completou a AUTH-001 e em até 30 min após a última falha | sucessos com chave diferente; sucesso no mesmo segundo do disparo |

Detalhes (empates, eventos fora de ordem, alertas repetidos, campos ausentes): [docs/regras.md](docs/regras.md). Os parâmetros ficam em [`config/rules.yaml`](config/rules.yaml), com validação e mensagens de erro em português.

## Formato de entrada

CSV próprio, com 12 colunas: `event_record_id, timestamp, event_id, channel, host, user, domain, src_ip, logon_type, status, sub_status, outcome`. O timestamp precisa ter fuso explícito. **Não** é o CSV do Event Viewer e não há leitura de EVTX. Especificação, validações e estratégia de deduplicação: [docs/formato-csv.md](docs/formato-csv.md).

Para analisar outro arquivo no mesmo formato:

```powershell
.\.venv\Scripts\python.exe -m authlab analyze --input data\samples\auth_events.csv --out output\exploratorio
```

## Saídas

Cada execução gera, em sua pasta de saída:

| Arquivo | Conteúdo |
|---|---|
| `report.html` | Relatório autocontido (sem recursos externos; conteúdo dos dados escapado) |
| `events_normalized.csv` | Eventos válidos normalizados, com `event_uid` e `arquivo:linha` |
| `alerts.csv` | Alertas, com vínculo `parent_alert_id` |
| `alert_evidence.csv` | Relação alerta → eventos de evidência (inclui o evento de disparo) |
| `rejected.csv` | Linhas rejeitadas, com motivo e número da linha |
| `duplicates.csv` | Duplicatas removidas e a primeira ocorrência |
| `summary.json` | Contagens de qualidade, elegibilidade por regra e alertas |

## Como investigar um alerta

1. Leia **por que a regra disparou** e identifique o evento de disparo.
2. Levante os fatos: quantidade, ritmo, Status/SubStatus, LogonType, sucesso.
3. Confira a **qualidade dos dados**: rejeições e eventos não elegíveis reduzem a cobertura.
4. Formule hipóteses legítimas e maliciosas. Lembre que IP não é pessoa e conta não é pessoa.
5. Liste o contexto que falta (inventário, mudanças, confirmação do titular).
6. Preencha a [ficha de investigação](docs/ficha-investigacao.md) com uma conclusão, que pode ser "inconclusiva", e um resumo para gestor.

Roteiro completo: [docs/investigacao.md](docs/investigacao.md). Exercício de calibração de limiar: [docs/calibracao.md](docs/calibracao.md).

## Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

Os testes cobrem: limiar exato e abaixo dele, limites de janela, eventos fora de ordem, timestamps iguais, chaves diferentes, duplicatas e conflitos de EventRecordID, campos ausentes, timestamp e configuração inválidos, sucesso antes/depois/fora do intervalo, prevenção de alertas redundantes, rastreabilidade das evidências, escape de HTML, proteção contra fórmulas em CSV e a execução completa dos três cenários com os resultados esperados.

## Estrutura

```
authlab/            código (config, events, rules, explain, report, pipeline, CLI)
config/             rules.yaml e configurações do exercício de calibração
scenarios/          3 cenários didáticos (CSV, perguntas, contexto, gabarito)
data/samples/       dataset exploratório fictício (fora da demonstração)
docs/               guia, checklist, formato, regras, investigação, ficha, calibração, decisões, referências
tests/              testes pytest
output/             saídas geradas (ignorado pelo Git)
```

## Segurança dos dados

- Só entram no repositório dados **fictícios**. `data/raw/`, `data/processed/`, `output/`, `*.evtx` e `*.pbix` estão no `.gitignore`.
- As saídas (CSV, HTML, JSON) **reproduzem os dados de entrada**. Com logs reais, elas contêm contas, hosts e IPs internos, e o mesmo vale para dashboards e capturas de tela feitos a partir delas. Não publique esses arquivos sem sanitização.
- O relatório exibe o caminho da configuração de forma relativa, para não expor a estrutura de pastas local.

## Limitações e pendências

- A instalação em `.venv`, os testes e a demonstração foram verificados no Windows com Python 3.13; outras versões e ambientes ainda não foram verificadas nesta sessão.
- Formato de entrada próprio; sem importação de dados reais do Windows.
- Correlação restrita à chave completa; sem detecção de tentativas distribuídas nem de ataques lentos.
- Interpretação apenas dos códigos de falha documentados na tabela do evento 4625.
- Sem contexto externo (inventário, DHCP, VPN, mudanças): a conclusão depende do analista.
- Métricas dos cenários fictícios **não** representam desempenho em produção.

Decisões e premissas registradas: [docs/decisoes.md](docs/decisoes.md).

## Roadmap

Nada abaixo está implementado.

- [ ] **AUTH-002**: padrão compatível com password spraying (mesma origem, várias contas)
- [ ] **AUTH-004**: logon fora do horário configurado
- [ ] Importação validada de dados Windows reais (formato a definir e testar)
- [ ] Suporte a EVTX
- [ ] Regras em formato Sigma e validação das correlações no destino
- [ ] Dashboard Power BI
- [ ] Comparação dos resultados com um SIEM de mercado (Splunk, Wazuh ou Elastic)

---

Projeto de estudo e portfólio em Blue Team / Detection Engineering. Dados inteiramente fictícios.
