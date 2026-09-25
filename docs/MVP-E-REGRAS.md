# MVP e regras de detecção

> **Documento de planejamento (histórico).** A v1 foi implementada. A especificação vigente e testada está em [regras.md](regras.md) e [formato-csv.md](formato-csv.md). Onde este planejamento diverge da implementação (identificação sem EventRecordID, conflito de EventRecordID, desempate e `channel`), veja [decisoes.md, seção Divergências](decisoes.md#divergências-em-relação-ao-planejamento-mvp-e-regrasmd).

Este documento registra as decisões do primeiro incremento. Ele descreve o comportamento pretendido; itens só devem ser marcados como entregues no [checklist](CHECKLIST.md) depois de implementados e verificados.

## Fluxo mínimo

`CSV didático → validação → normalização UTC → deduplicação → AUTH-001 → AUTH-003 → evidências → CSVs + HTML local`

Não haverá servidor web, banco de dados, coleta contínua, resposta automática, machine learning, autenticação de usuários ou integração com SIEM nesta versão.

## Esquema de entrada

O CSV próprio terá pelo menos estes campos:

| Campo | Regra inicial |
|---|---|
| `timestamp` | Obrigatório; data/hora ISO 8601 com `Z` ou deslocamento explícito. Normalizado para UTC. |
| `event_id` | Obrigatório; somente `4624` ou `4625`. Identifica o tipo do evento. |
| `event_uid` | Identificador estável derivado pelo programa de conteúdo normalizado, não confundido com `event_record_id`. |
| `event_record_id` | Opcional; preservado, mas nunca tratado como globalmente único. |
| `host` | Obrigatório; computador que registrou o evento. |
| `channel` | Obrigatório; contexto do log que originou o registro. |
| `user`, `domain` | Obrigatórios para a chave de correlação; valores vazios ou `-` tornam a linha inelegível às regras. |
| `src_ip` | Pode estar vazio ou ser `-`; só endereços IP válidos participam da correlação. |
| `logon_type` | Preservado como texto/número conforme formato documentado. Não haverá exclusões globais por tipo. |
| `status`, `sub_status` | Campos separados; vazios ou `-` são preservados como ausentes. |
| `outcome` | Deve ser `success` para `4624` e `failure` para `4625`. Inconsistências são rejeitadas. |

O programa acrescentará referência ao caminho do CSV e número da linha. O formato não promete compatibilidade com CSV exportado pelo Event Viewer nem com EVTX.

## Identidade e duplicatas

`event_uid` será um hash determinístico do conteúdo normalizado do evento, incluindo `event_record_id` quando presente, mas excluindo caminho e número da linha. Assim, cópias idênticas em arquivos diferentes podem ser reconhecidas como duplicatas. A primeira ocorrência determinística será mantida e as demais serão contadas como duplicadas.

`event_record_id` é apenas um campo do conteúdo e só tem significado junto ao host e channel/contexto de origem; ele não será usado sozinho para deduplicar. Se dois eventos distintos tiverem todos os mesmos campos disponíveis, o CSV não fornece informação suficiente para distingui-los: esse limite será documentado.

## Chave de correlação

AUTH-001 e AUTH-003 exigem todos estes componentes: domínio, conta, endereço IP válido e host. A chave usa comparação normalizada e explícita de domínio/conta/host e o IP validado. Eventos sem um desses componentes continuam válidos para a saída normalizada, mas não são elegíveis às regras. Origem ausente nunca será agrupada com outra origem desconhecida.

Essa escolha é didática e não correlaciona tentativas distribuídas por IPs diferentes nem eventos em hosts diferentes.

## AUTH-001 — falhas repetidas de autenticação

- Considera somente eventos `4625` com `outcome=failure` e chave de correlação completa.
- Conta falhas em uma janela móvel, por chave.
- O limiar e a duração da janela ficam em `config/rules.yaml`; valores iniciais propostos para demonstração: 5 eventos em 10 minutos.
- A janela inclui os dois extremos: uma falha exatamente no início da janela ainda conta.
- Eventos são ordenados por instante UTC, não pela ordem física das linhas. Em timestamps iguais, `event_uid` define ordenação reproduzível; igualdade de horário não cria relação temporal “depois”.
- Um alerta representa uma sequência: gera-se no primeiro evento que alcança o limiar; falhas adicionais dentro da mesma sequência atualizam suas evidências em vez de criarem alertas repetidos. Uma nova sequência só começa após um intervalo maior que a janela sem falhas daquela chave.

## AUTH-003 — sucesso após falhas repetidas

- Só é avaliado para uma sequência que já gerou AUTH-001.
- Procura evento `4624` com `outcome=success`, mesma chave e timestamp estritamente posterior ao momento em que o limiar foi atingido.
- O limite superior do intervalo configurado é inclusivo; o instante do limiar não é considerado “depois”.
- Uma sequência de falhas pode originar no máximo um AUTH-003; o primeiro sucesso correspondente é associado à sequência.
- AUTH-003 referencia o alerta AUTH-001 relacionado e inclui todas as falhas da sequência usadas na correlação e o evento de sucesso.
- Sucesso anterior às falhas, simultâneo ao instante de disparo ou fora do intervalo não dispara AUTH-003.

## Qualidade dos dados e interpretação

Datas inválidas, campos obrigatórios ausentes, IP inválido quando fornecido e inconsistência de tipo/resultado devem ser listados em rejeições, com arquivo, linha e motivo. Uma linha rejeitada não desaparece silenciosamente.

O resumo deve diferenciar volume lido, válido, rejeitado, duplicado, elegível por regra e alertas gerados. Zero alertas com dados suficientes não é o mesmo que nenhum dado elegível para avaliação.

Relatórios devem separar fatos observados, motivo do disparo, explicações possíveis e verificações pendentes. Nenhum resultado automático concluirá comprometimento ou atribuirá atividade a uma pessoa com base apenas em nome de conta ou IP.

## Valores e calibração

Os números propostos (5 falhas/10 minutos e até 30 minutos para um sucesso subsequente) são parâmetros didáticos inspirados nos exemplos atuais. Antes de serem executáveis, devem ser validados em `config/rules.yaml` e cobertos por testes. Não representam baseline nem recomendação de produção.

No exercício de calibração, reduzir o limiar tende a aumentar a cobertura de sequências menores e também pode aumentar alertas legítimos; elevá-lo pode reduzir ruído, mas deixar sequências suspeitas menores sem alerta. Os dados de demonstração não medem desempenho em produção.