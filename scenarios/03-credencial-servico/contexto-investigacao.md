# Cenário 3 – Contexto da investigação

> **Informação fictícia e externa aos eventos.** Nada abaixo aparece no `events.csv`. Simula o que o analista obteria conversando com pessoas ou consultando outros sistemas.

- **Registro de mudança CHG-0042 (fictício):** rotação trimestral da senha de `svc_relatorios`, executada pela equipe de infraestrutura às 09:59 de 16/09. O plano de mudança **não** incluía atualizar a aplicação de relatórios.
- **Inventário (fictício):** `10.20.5.15` é o servidor de aplicação `SRV-APP-02`, onde roda a aplicação de relatórios. A aplicação tenta se conectar ao banco a cada 2 minutos.
- **Chamado INC-1187 (fictício), aberto às 10:40:** "relatórios não atualizam desde as 10h". Às 11:02, a equipe da aplicação atualizou a senha na configuração e o serviço voltou.
