# Formato CSV aceito (v1)

Formato **próprio do projeto**. Ele **não** é o CSV exportado pelo Event Viewer e não há leitura de EVTX. Uma importação validada de dados Windows reais está no roadmap.

## Regras gerais

- Codificação UTF-8 (com ou sem BOM), separador vírgula, primeira linha com cabeçalho.
- Todas as 12 colunas abaixo precisam existir no cabeçalho, em qualquer ordem. Colunas extras são ignoradas e listadas no relatório.
- Célula vazia ou `-` significa **valor ausente**. O Windows usa `-` em vários campos, como o IP em alguns tipos de logon.
- Espaços nas pontas são removidos.

## Colunas

| Coluna | Obrigatória | Formato | Campo correspondente no evento Windows |
|---|---|---|---|
| `event_record_id` | não | inteiro positivo | `EventRecordID` (System) |
| `timestamp` | **sim** | ISO 8601 **com fuso**: `2026-09-15T21:48:03-03:00` ou `2026-09-15T21:48:03Z` | `TimeCreated` (System) |
| `event_id` | **sim** | `4624` ou `4625` | `EventID` (System) |
| `channel` | **sim** | `Security` | `Channel` (System) |
| `host` | **sim** | texto | `Computer` (System): computador que **registrou** o evento |
| `user` | não* | texto | `TargetUserName` |
| `domain` | não* | texto | `TargetDomainName` |
| `src_ip` | não* | IPv4 ou IPv6 | `IpAddress` ("Source Network Address") |
| `logon_type` | não | inteiro | `LogonType` |
| `status` | não | hexadecimal `0x...` | `Status` (4625) |
| `sub_status` | não | hexadecimal `0x...` | `SubStatus` (4625) |
| `outcome` | **sim** | `success` ou `failure` | derivado: 4624 = success, 4625 = failure |

\* Não são obrigatórios para o registro ser **válido**, mas são necessários para ele ser **elegível** às regras (ver [regras.md](regras.md)).

## Validações

| Situação | Tratamento |
|---|---|
| Coluna obrigatória ausente no cabeçalho | Erro: o arquivo inteiro é recusado |
| Campo obrigatório vazio ou `-` | Linha rejeitada |
| Timestamp sem fuso ou fora do ISO 8601 | Linha rejeitada. Não adivinhamos o fuso: um erro de 3 horas muda a análise |
| `event_id` diferente de 4624/4625 | Linha rejeitada (fora do escopo) |
| `channel` diferente de `Security` | Linha rejeitada |
| `outcome` incoerente com `event_id` | Linha rejeitada |
| 4624 com Status/SubStatus de falha; 4625 com Status `0x0` | Linha rejeitada |
| Status/SubStatus fora do formato hexadecimal | Linha rejeitada |
| `logon_type` ou `event_record_id` não numérico | Linha rejeitada |
| Linha com mais colunas que o cabeçalho | Linha rejeitada |
| IP informado, mas inválido | Linha rejeitada (problema de qualidade, diferente de ausência) |
| IP ausente | Linha **mantida**, `src_ip_state=missing`, não elegível para correlação |

Toda linha lida termina em **exatamente um** destino: evento válido, `rejected.csv` (com motivo e número da linha) ou `duplicates.csv` (com referência à primeira ocorrência). Nada é descartado em silêncio.

## Normalização

- `timestamp` → `timestamp_utc`. O valor original é preservado em `timestamp_original`.
- `src_ip`: IPv4 mapeado em IPv6 (`::ffff:10.0.0.5`) vira `10.0.0.5`. A Microsoft documenta que o campo pode vir nesse formato.
- `status`/`sub_status`: `0xc000006a` → `0xC000006A`.
- `channel`: grafia padronizada `Security`.
- `user`, `domain` e `host` são preservados como vieram. Só a **comparação** para correlação ignora maiúsculas e minúsculas.

## Identificação estável e deduplicação

`EventID` identifica o **tipo** de evento (4624, 4625). `EventRecordID` identifica um **registro** dentro de um log. Ele **não é globalmente único**: dois computadores podem ter o mesmo número, e a documentação usada não garante unicidade além disso.

| Situação | `event_uid` | Deduplicação |
|---|---|---|
| Com `event_record_id` | hash de (`host`, `channel`, `event_record_id`) | mesmo trio + mesmo conteúdo = duplicata removida; mesmo trio com conteúdo diferente = linha rejeitada por conflito |
| Sem `event_record_id` | hash do conteúdo normalizado + nº da ocorrência | **não remove**. Linhas idênticas são mantidas e contadas como "possíveis duplicados", porque duas falhas reais no mesmo segundo podem ser idênticas nos campos disponíveis |

O `event_uid` não depende da posição da linha. Reordenar o arquivo não muda os identificadores.

## Exemplo

```csv
event_record_id,timestamp,event_id,channel,host,user,domain,src_ip,logon_type,status,sub_status,outcome
551208,2026-09-15T21:48:03-03:00,4625,Security,SRV-RDP-01,joao.silva,LAB,203.0.113.50,10,0xC000006D,0xC000006A,failure
551220,2026-09-15T21:54:08-03:00,4624,Security,SRV-RDP-01,joao.silva,LAB,203.0.113.50,10,,,success
```
