# Como investigar um alerta

Um alerta é um **indício**, não uma conclusão. O objetivo da investigação é chegar a uma conclusão fundamentada, e "inconclusiva" também vale, com um próximo passo claro.

## Roteiro

### 1. Entenda o que disparou

No relatório (`report.html`), para cada alerta:

- **"Por que a regra disparou"**: qual critério foi atingido e em que evento (linha destacada em vermelho).
- **Chave de correlação**: conta, IP de origem e host que registrou o evento (destino).
- **Vínculo**: um AUTH-003 aponta para o AUTH-001 que o originou.

### 2. Levante os fatos

Use a seção **"O que foi observado"** e a tabela de evidências. Anote na [ficha](ficha-investigacao.md):

- quantidade de falhas, período e ritmo (rajada irregular ou cadência constante);
- **Status/SubStatus**: a causa registrada. Não trate todo 4625 como "senha errada". `0xC0000064` (conta inexistente) conta uma história diferente de `0xC000006A` (senha incorreta);
- **LogonType**: interativo (2), rede (3), remoto (10), serviço (5)...;
- se houve sucesso, quando e com qual LogonType.

### 3. Verifique a qualidade dos dados

Antes de concluir "nada aconteceu", veja a seção **Qualidade dos dados**:

- houve rejeições ou duplicatas? Leia os motivos;
- há eventos **não elegíveis** (IP ausente, usuário ausente)? Se sim, a cobertura é parcial e pode haver padrões que a regra não viu.

### 4. Rastreie as evidências

Cada evento do alerta tem `event_uid` e `arquivo:linha`. O arquivo `alert_evidence.csv` lista a relação alerta → eventos, e `events_normalized.csv` tem todos os campos. Cite essas referências na ficha: é assim que outra pessoa consegue refazer seu raciocínio.

### 5. Formule hipóteses concorrentes

Para cada hipótese (legítima e maliciosa), liste evidências a favor e contra. Cuidado com:

- **IP não é pessoa.** O IP indica a origem de rede. Pode haver NAT, VPN, proxy ou equipamento compartilhado.
- **Conta não é pessoa.** A atividade é **da conta**. Atribuir a uma pessoa exige outras evidências.
- **Padrão não é intenção.** Regularidade sugere automação, mas não prova. Muitas falhas sugerem tentativa e erro, mas podem ser configuração errada.

### 6. Busque contexto fora dos eventos

A ferramenta não tem acesso a inventário, DHCP, VPN, registros de mudança, chamados ou às pessoas. Liste o que falta e **onde** obteria. Nos cenários, esse contexto está em `contexto-investigacao.md`, sempre marcado como informação externa.

### 7. Decida e comunique

- **Prioridade**: combine impacto possível (que conta, que servidor) com confiança nas evidências.
- **Conclusão**: legítima confirmada, suspeita confirmada (escalar) ou inconclusiva.
- **Resumo para gestor**: até 4 frases, sem jargão, dizendo o que aconteceu, o que significa, o que será feito e se há impacto.

## Tom das explicações

| Evite | Prefira |
|---|---|
| "O usuário tentou invadir" | "Foram registradas 12 falhas de autenticação para a conta..." |
| "O atacante no IP X" | "A partir do IP de origem X" |
| "Senha errada" (sem olhar o código) | "Falha de autenticação, SubStatus 0xC000006A (senha incorreta, segundo a Microsoft)" |
| "Não houve ataque" (sem dados) | "Não houve alerta; 3 de 3 eventos foram avaliados" |
