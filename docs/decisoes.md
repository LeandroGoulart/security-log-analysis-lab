# Decisões e premissas

Registro das escolhas feitas na v1, para que possam ser questionadas e revistas.

| # | Decisão | Motivo | Alternativa descartada |
|---|---|---|---|
| D1 | CSV **próprio** e documentado | Entrada reproduzível e testável sem depender de uma máquina Windows | Prometer compatibilidade com CSV do Event Viewer/EVTX sem validar (roadmap) |
| D2 | Timestamp **exige** fuso; processamento em UTC; exibição em UTC e no fuso configurado | Um fuso adivinhado desloca a linha do tempo em horas | Assumir horário local |
| D3 | Deslocamento de exibição fixo (`-03:00`) em vez de fuso nomeado | No Windows, `zoneinfo` depende do pacote `tzdata`; o horário de Brasília não tem horário de verão desde 2019 | Adicionar dependência `tzdata` |
| D4 | `-` e vazio = ausente; eventos sem campo de correlação **não elegíveis** | Agrupar ausências criaria uma "origem desconhecida" fictícia | Substituir por `unknown` |
| D5 | Registros inválidos vão para `rejected.csv` com motivo e linha | Nada descartado em silêncio; o analista vê a qualidade da entrada | Ignorar linhas ruins |
| D6 | `event_uid` = hash(host, channel, EventRecordID); sem EventRecordID, hash do conteúdo + ocorrência | EventRecordID não é globalmente único (premissa); o conteúdo sozinho colapsaria falhas legítimas idênticas | Usar EventRecordID puro ou o número da linha |
| D7 | Sem EventRecordID, linhas idênticas são **mantidas** e contadas | Remover poderia subcontar falhas reais do mesmo segundo | Deduplicar por conteúdo |
| D8 | Chave AUTH-001/003 = domain + user + src_ip + host | Escopo do MVP, fácil de explicar | Chaves mais largas (roadmap: AUTH-002) |
| D9 | Um alerta por episódio; falhas seguintes são agregadas | Evita dezenas de alertas para a mesma sequência (cenário 3) | Um alerta por janela |
| D10 | Sucesso no mesmo segundo da falha de disparo não gera AUTH-003 | A ordem entre eventos com o mesmo timestamp é indeterminada | Desempatar por EventRecordID (não confiável entre fontes) |
| D11 | Sem exceções (allowlist) na v1 | Exceções globais escondem ataques; exceções específicas exigem processo de governança | Ignorar contas de serviço/LogonType 3 |
| D12 | Sem campo de severidade automática | Prioridade é decisão do analista, justificada na ficha | Severidade fixa por regra |
| D13 | Interpretar só códigos da tabela oficial do 4625 | Não inventar significados | Tabelas de terceiros |
| D14 | Células CSV começando com `= + - @` recebem `'` na frente | Evita injeção de fórmulas ao abrir no Excel | Gravar sem tratamento |
| D15 | Pacote na raiz (`python -m authlab`), sem instalação do pacote (decisão original, substituída pela D20) | Um comando para iniciantes, sem empacotamento | `pip install -e .` |
| D16 | Dependências: PyYAML (execução) e pytest (testes) | Poucas dependências, instalação simples | pandas, Jinja2 |
| D17 | Caminho da configuração exibido de forma relativa no relatório | Não expor a estrutura de pastas do computador | Caminho absoluto |
| D18 | IP informado mas inválido → linha rejeitada; IP vazio ou `-` → ausente (não elegível) | Ausência é comum no Windows; valor malformado é problema de qualidade (alinhado a [MVP-E-REGRAS.md](MVP-E-REGRAS.md)) | Manter a linha como não elegível |
| D19 | Desempate de timestamps iguais por EventRecordID (quando houver) e depois `event_uid` | Reproduzível mesmo se as linhas forem reordenadas | Ordem física das linhas |
| D20 | Aplicação em `src/authlab`, com comando `authlab` e configuração/cenários como recursos do pacote | Instalação consistente de checkout editável ou wheel sem depender da pasta atual | Resolver recursos pela raiz do repositório |
| D21 | Erros/rejeições não repetem valores brutos; `rejected.csv` mantém só arquivo, linha e motivo | Evitar que uma linha malformada replique conteúdo sensível em mais um artefato | Copiar toda a linha para a saída de rejeições |
| D22 | `.gitignore` cobre entradas locais, relatórios e configurações do editor; saídas válidas ainda podem conter dados sensíveis | Reduzir publicação acidental sem alegar anonimização | Ignorar genericamente todos os CSVs, incluindo os samples fictícios |

## Divergências em relação ao planejamento ([MVP-E-REGRAS.md](MVP-E-REGRAS.md))

O documento de planejamento foi escrito antes da implementação. Onde a implementação diverge dele, vale o comportamento abaixo, que é o testado:

| Tema | Planejado | Implementado | Motivo |
|---|---|---|---|
| `event_uid` e duplicatas **sem** EventRecordID | Hash do conteúdo; cópias idênticas removidas como duplicatas | Hash do conteúdo + nº da ocorrência; cópias idênticas **mantidas** e contadas como "possíveis duplicados" | Duas falhas reais no mesmo segundo podem ser idênticas nos campos do CSV; removê-las subestimaria a contagem da AUTH-001. A contagem aparece no relatório para decisão do analista |
| Mesmo host + channel + EventRecordID com conteúdo **diferente** | Eventos distintos (o hash inclui o conteúdo) | Segunda ocorrência **rejeitada** por conflito | O mesmo registro de log não pode ter dois conteúdos; o conflito indica problema na origem do arquivo |
| Desempate de timestamps iguais | `event_uid` | EventRecordID (quando houver) e depois `event_uid` | EventRecordID reflete a ordem de gravação dentro do mesmo log |
| `channel` | Contexto do log, sem valor fixo | Precisa ser `Security` | 4624/4625 são eventos do log de Segurança |

Se preferir o comportamento planejado para duplicatas, a mudança fica concentrada em `src/authlab/events.py` (`read_events`) e nos testes `test_identical_rows_without_record_id_are_kept_and_counted` e `test_record_id_conflict_is_rejected`.

## Premissas

- **P1.** Os dados de entrada representam eventos do log `Security` de computadores Windows. A ferramenta não verifica a autenticidade nem a integridade da coleta.
- **P2.** `host` é o computador que registrou o evento (destino da tentativa), não a origem.
- **P3.** O relógio dos computadores está razoavelmente sincronizado. Diferenças de relógio entre hosts afetam a ordem dos eventos.
- **P4.** Os limiares padrão servem para demonstração e não representam nenhuma recomendação.
