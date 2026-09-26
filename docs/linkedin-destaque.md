# Posicionamento do projeto no LinkedIn

Este documento orienta a publicação do **Security Log Analysis Lab** como projeto em
**Destaques**. O projeto deve aparecer como evidência de aprendizado aplicado, sem ser
apresentado como experiência profissional em SOC.

## Título sugerido

**Security Log Analysis Lab | Investigação de autenticação Windows para SOC/Blue Team**

## Descrição para o Destaques

Projeto pessoal de laboratório para investigar eventos de autenticação Windows `4624` e
`4625` com Python.

O fluxo valida e normaliza os dados, aplica regras de correlação temporal, gera alertas
explicáveis e mantém a relação entre alerta e evento de origem. Os relatórios também mostram
rejeições, duplicatas, cobertura parcial, hipóteses de falso positivo e limitações da análise.

Criei três cenários fictícios: erro de digitação, acesso suspeito e credencial de serviço
desatualizada. A proposta é praticar o raciocínio de triagem de um SOC: um alerta é um
indício para investigação, não uma confirmação de ataque.

**Competências evidenciadas:** SOC, Blue Team, detecção baseada em eventos, correlação,
qualidade de dados, investigação, rastreabilidade, Python, testes automatizados e comunicação
técnica.

## O que este projeto cobre

| Gap ou objetivo | Evidência atual | Classificação |
|---|---|---|
| Blue Team / SOC | Regras AUTH-001/AUTH-003, triagem e relatórios | Projeto/laboratório |
| Investigação de incidentes | Linha do tempo, hipóteses e próximos passos | Projeto/laboratório |
| IAM | Correlação por domínio, conta, origem e host; cenários de conta de serviço | Projeto aplicado, não experiência profissional |
| GRC | Limitações, critérios, qualidade, rastreabilidade e documentação | Projeto aplicado |
| Engenharia de detecção | Regras configuráveis, limites documentados e testes de borda | Projeto aplicado |
| Cloud Security / AWS | Ainda não demonstrado neste repositório | Gap aberto |
| SIEM | Conceitos de correlação, sem produto SIEM | Gap aberto |
| Password spraying | Limitação documentada; AUTH-002 é próximo passo | Gap aberto |
| Resposta operacional | Recomenda próximos passos, mas não executa contenção | Gap aberto |

## Texto curto para uma publicação

Nem todo alerta de autenticação é um ataque. E nenhum alerta deveria ser aceito sem
evidência.

Para praticar investigação defensiva, construí um laboratório em Python que analisa eventos
Windows `4624` e `4625`. O projeto valida os dados, correlaciona falhas por conta, origem e
host, identifica um sucesso após falhas repetidas e gera relatórios com a trilha completa da
decisão.

Também incluí cenários em que o padrão pode ser legítimo, como uma credencial de serviço
desatualizada. Isso foi importante: detectar é apenas uma parte do trabalho. A outra é
explicar o que foi observado, o que ainda é hipótese e qual contexto falta para decidir.

O laboratório é fictício e não substitui experiência em produção. Ele representa meu estudo
aplicado em SOC/Blue Team e conecta minha base profissional em suporte, IAM, operações e
governança ao próximo passo da minha formação em cybersecurity.

Repositório: [cole aqui a URL pública do GitHub]

#CyberSecurity #BlueTeam #SOC #IAM #SegurançaDaInformação

## Como apresentar honestamente

- **Experiência profissional:** suporte N1/N2, IAM, Active Directory, Microsoft 365, Google
  Workspace, implantação, sustentação e governança.
- **Projeto:** este laboratório de análise de logs e investigação defensiva.
- **Estudo:** AWS, cloud security, defesa cibernética, endpoint security e temas ofensivos.
- **Ainda não afirmar:** atuação profissional em SOC, SIEM, resposta a incidentes em produção,
  AWS Security ou Purple Team.

## Próximos incrementos que reduzem gaps

1. Implementar AUTH-002 para password spraying e adicionar testes com várias contas/origens.
2. Criar uma regra equivalente em Sigma e documentar o mapeamento para ATT&CK.
3. Adicionar um cenário de identidade em cloud com dados fictícios e limites explícitos.
4. Documentar um playbook de triagem com severidade, decisão, escalonamento e encerramento.
5. Publicar cada evolução com o que foi construído, o que foi aprendido e o que continua fora
   do escopo.