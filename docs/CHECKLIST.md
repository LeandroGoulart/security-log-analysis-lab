# Checklist e andamento

Este documento é o registro de trabalho do projeto. Atualize o estado após cada etapa: marque como concluído somente o que foi executado e verificado; anote falhas e próximos passos antes de avançar.

## Marcos concluídos

- **Planejamento:** objetivo, escopo e limites do laboratório documentados.
- **MVP local:** parser e normalização, AUTH-001/AUTH-003, rastreabilidade, três cenários, saídas CSV/HTML, ficha de investigação, calibração e testes implementados.
- **Revisão atual:** projeto inspecionado; corrigida a associação de AUTH-003 para ligar o sucesso ao episódio qualificante mais recente; convenção simples de commits e comentários adicionada em [PADRAO-GITHUB.md](PADRAO-GITHUB.md).
- **Verificação Windows:** 87 testes passaram com Python 3.13; `python -m authlab demo --strict` conferiu os resultados dos três cenários.

Esses itens ficam como resumo, não como tarefas abertas. As decisões sobre duplicatas e diferenças em relação ao planejamento estão registradas em [decisoes.md](decisoes.md).

## Marco atual: v1 publicada

- [x] Instalar dependências em `.venv`, executar `pytest` e `python -m authlab demo --strict` no Windows com Python 3.13.
- Commit `7b0928b`: `feat: publica primeira versão do laboratório`.
- Publicado em `origin/main`; o hash remoto foi confirmado igual ao local.
- `.vscode/settings.json` permaneceu somente local e não foi incluído.

## Próximo incremento

- [ ] Preparar uma estrutura Python instalável com layout `src/`, mantendo os comandos do README e cobrindo a mudança com testes.
- [ ] Planejar melhorias seguintes em issues/commits pequenos, sem misturar regras futuras com a v1.

## Roadmap posterior

- [ ] AUTH-002: padrão compatível com password spraying.
- [ ] AUTH-004: logon fora de horário configurado.
- [ ] Importação validada de logs reais do Windows.
- [ ] Suporte a EVTX.
- [ ] Regras Sigma e validação no destino.
- [ ] Dashboard Power BI e comparação com SIEM.

Esses itens estão fora da primeira versão; não devem ser descritos como implementados.

## Registro de sessões

| Data | Etapa concluída | Verificação | Próximo passo |
|---|---|---|---|
| 2026-09-25 | Inspeção integral, correção de vínculo AUTH-003, convenção de GitHub e revisão do checklist. | 87 testes passaram e a demo estrita conferiu os três cenários no Windows com Python 3.13; instalação repetida no `.venv`. | Publicar o marco v1. |
| 2026-09-25 | Marco v1 publicado em `origin/main` como `7b0928b`. | `git ls-remote` confirmou o mesmo hash; workspace sincronizado, com `.vscode/settings.json` somente local. | Preparar o próximo incremento: layout Python instalável `src/`. |

## Como atualizar este checklist

Ao concluir uma tarefa, remova-a da lista aberta e registre o resultado em “Marcos concluídos” ou no histórico. Mantenha pendentes apenas ações que ainda precisam ser executadas. Não marque como concluído algo apenas planejado ou escrito em documentação.