# Cenário 2 – Gabarito

## Fatos observados nos eventos

- **Manhã:** `joao.silva` faz logon local em `WS-044` (08:55). Às 09:00:14 há 1 falha RDP em `SRV-RDP-01` a partir de `10.20.1.44`, seguida de sucesso 17 s depois.
- **Noite:** 12 falhas 4625 em `SRV-RDP-01` para `LAB\joao.silva`, origem `203.0.113.50`, LogonType 10 (RemoteInteractive), entre 21:48:03 e 21:53:04 (5 min). Todas com `0xC000006D` / `0xC000006A` ("misspelled or bad password", segundo a Microsoft). Intervalos irregulares, de 15 a 55 s.
- **Sucesso:** 4624 às 21:54:08 com a mesma chave, cerca de 1 min após a última falha.
- **Alertas:** AUTH-001 (disparo na 5ª falha, 21:49:27) e AUTH-003 vinculado.

## Por que a falha das 09:00 ficou fora

A chave de correlação inclui o IP de origem. `10.20.1.44` ≠ `203.0.113.50`, e as falhas estão separadas por mais de 12 horas. São sequências independentes.

## O que os eventos não provam

- Que houve ataque. Eles mostram uma sequência de falhas seguida de sucesso.
- Quem estava do outro lado. O IP mostra a origem de rede da conexão, não uma pessoa. Pode haver NAT, proxy ou VPN de terceiros no caminho.
- O que foi feito na sessão. Isso exige outros registros, fora do escopo desta ferramenta.

## Hipóteses

| Hipótese | A favor | Contra / o que falta |
|---|---|---|
| João acessou de casa e errou a senha | mesma conta; erros de senha acontecem | 12 erros em 5 min é muito; origem fora do inventário e da VPN; **João nega** (contexto) |
| Credencial salva desatualizada | — | intervalos irregulares; RDP interativo; houve sucesso sem troca de senha registrada |
| Senha descoberta por tentativa e erro | sequência + sucesso; origem não reconhecida; horário fora do expediente; servidor exposto (contexto) | não temos o que foi feito na sessão |
| Teste autorizado | — | nenhum teste agendado (contexto) |

## Conclusão sugerida

**Suspeita de acesso indevido: escalar como incidente, prioridade alta.** Os eventos sozinhos justificam investigação. O contexto (origem desconhecida, negativa do titular, nenhuma mudança agendada) enfraquece as explicações legítimas. Ainda não é uma confirmação de comprometimento, porque falta saber o que ocorreu na sessão. A resposta (redefinir a credencial, encerrar sessões, preservar evidências, revisar a exposição do RDP) segue o procedimento de resposta a incidentes da organização, que está fora do escopo desta ferramenta.

Justificativa da prioridade: conta com acesso a servidor administrativo, sucesso após falhas, origem não reconhecida e titular que não reconhece o acesso.

## Resumo para gestor

"Na noite de 15/09, alguém fez 12 tentativas de senha na conta de João Silva no servidor de acesso remoto e conseguiu entrar em seguida, a partir de um endereço que não pertence à empresa. O funcionário diz que não fez esse acesso. Tratamos como possível uso indevido da conta e acionamos o procedimento de incidente. Ainda estamos apurando o que foi feito durante o acesso."

## Limitações

- Com limiar 15, a AUTH-001 não dispara (12 falhas), e a AUTH-003 também não, porque depende dela. Um limiar alto reduz ruído, mas pode perder exatamente este caso.
- Se o atacante tivesse usado várias origens (por exemplo, 4 falhas por IP), a chave atual não correlacionaria as tentativas.
