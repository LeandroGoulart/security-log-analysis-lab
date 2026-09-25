# Guia do projeto

Este guia explica o laboratório sem exigir experiência prévia em segurança da informação.

## Para que serve

O projeto ensina a investigar registros de autenticação do Windows. Um registro informa que houve uma tentativa de entrar em uma conta; vários registros, analisados juntos, podem formar um sinal que merece investigação.

O laboratório não decide sozinho que houve invasão. Um alerta é um indício, não uma conclusão. Uma pessoa analista deve conferir o contexto, considerar explicações legítimas e registrar o que ainda não sabe.

## O que significam os eventos

- `4624`: o Windows registrou um logon bem-sucedido.
- `4625`: o Windows registrou uma falha de logon.
- `EventID`: identifica o tipo de evento, como `4624` ou `4625`.
- `EventRecordID`: identifica um registro dentro do contexto do log que o produziu. Não é um identificador global.
- `timestamp`: horário do evento. A ferramenta exige fuso explícito e converte o instante para UTC para comparar eventos corretamente.

Uma falha `4625` não significa necessariamente “senha errada”. Os campos `status` e `sub_status` são preservados; a ferramenta só explica um código quando ele consta na documentação da Microsoft ([referências](referencias.md)).

## Como o fluxo funciona

1. A pessoa fornece um CSV no formato próprio e documentado pelo projeto.
2. O programa valida cada linha. Linhas com problema são registradas em um arquivo de rejeições, com o número da linha e o motivo.
3. Linhas válidas são normalizadas para campos consistentes e horários UTC.
4. Duas regras didáticas procuram padrões de falhas e sucesso após falhas.
5. Cada alerta aponta para os registros que o sustentam.
6. O programa grava CSVs e um relatório HTML local, que pode ser aberto no navegador sem iniciar um servidor.

O fluxo está implementado na v1 (`python -m authlab demo`; veja o [README principal](../README.md)). O [checklist](CHECKLIST.md) registra o que foi verificado e o que falta.

## Regras do MVP

O MVP é a primeira versão pequena que permite percorrer o fluxo completo com dados fictícios.

- **AUTH-001 — falhas repetidas:** identifica ao menos o limite configurado de eventos `4625` em uma janela móvel, correlacionados por domínio, conta, IP válido e host que registrou o evento.
- **AUTH-003 — sucesso após falhas:** identifica um `4624` posterior à sequência que disparou AUTH-001, com a mesma chave de correlação e dentro do intervalo configurado.

Os valores iniciais são didáticos e ficam em `config/rules.yaml`; não devem ser tratados como recomendação para um ambiente real. A especificação vigente está em [regras.md](regras.md); o planejamento original, em [MVP e regras](MVP-E-REGRAS.md).

## Vocabulário rápido

- **Normalizar:** converter dados válidos para um formato comum, sem perder a origem.
- **Correlação:** relacionar eventos por campos e tempo para verificar se fazem parte de uma sequência.
- **Evidência:** registros específicos que permitem conferir por que um alerta apareceu.
- **Falso positivo:** alerta que corresponde à regra, mas cuja causa pode ser legítima, como uma senha antiga salva em um serviço.
- **Triagem:** primeira análise para decidir o que precisa ser investigado e com qual prioridade.

## Limites

O MVP processa arquivos em lote. Não coleta eventos continuamente, não bloqueia acessos e não usa logs reais na demonstração. A correlação por IP e host não encontra tentativas distribuídas por várias origens ou destinos. IP de origem não identifica com certeza uma pessoa ou equipamento.

O CSV didático não é um exportador/importador genérico do Event Viewer. Suporte a CSV real do Windows e a arquivos EVTX fica para uma etapa futura, com validação própria.

## Documentos relacionados

- [Especificação das regras](regras.md) · [Formato CSV](formato-csv.md)
- [Como investigar um alerta](investigacao.md) · [Ficha de investigação](ficha-investigacao.md)
- [Exercício de calibração](calibracao.md) · [Decisões e premissas](decisoes.md) · [Referências](referencias.md)
- [Padrão simples para commits e comentários no GitHub](PADRAO-GITHUB.md)
- [MVP e regras (planejamento original)](MVP-E-REGRAS.md)
- [Cenários didáticos](../scenarios/README.md)
- [Checklist e histórico de andamento](CHECKLIST.md)
- [Descrição dos dados fictícios existentes](../data/samples/README.md)