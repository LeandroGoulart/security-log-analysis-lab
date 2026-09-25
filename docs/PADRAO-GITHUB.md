# Padrão simples para o GitHub

Use mensagens curtas e verdadeiras sobre o que foi feito. Uma mudança pequena e bem explicada é melhor do que dizer que algo está pronto quando ainda falta validar.

## Título do commit

Formato:

```text
tipo: ação + assunto
```

Escreva sem ponto final. Use um tipo desta lista:

- `docs`: documentação
- `feat`: funcionalidade nova
- `fix`: correção
- `test`: testes
- `chore`: organização ou manutenção

Exemplos deste projeto:

```text
docs: organiza o guia para iniciantes
feat: valida campos obrigatórios do CSV
test: cobre o limiar da AUTH-001
fix: vincula sucesso ao episódio mais recente
chore: ignora relatórios gerados localmente
```

## Descrição do commit ou pull request

Adicione uma descrição só quando ajudar a explicar a mudança. Três linhas bastam:

```text
O que mudou: [resumo simples]
Como verifiquei: [comando ou teste executado]
Próximo passo: [o que falta, se houver]
```

Exemplo:

```text
O que mudou: documentei como os cenários fictícios ajudam a investigar alertas.
Como verifiquei: conferi os links locais e executei os testes.
Próximo passo: revisar a instalação em outra máquina Windows.
```

Se não houver próximo passo relevante, remova essa linha. Se algo não foi testado, diga isso diretamente em vez de escrever “testes passaram”.

## Comentário de andamento

Para atualizar uma issue ou registrar o progresso de uma etapa, use uma frase curta:

```text
Concluí [etapa]. Verifiquei com [checagem]. Agora vou [próximo passo].
```

Exemplo:

```text
Concluí os testes das regras AUTH-001 e AUTH-003: 36 passaram no Windows com Python 3.13. Agora vou conferir a instalação em um ambiente virtual limpo.
```

O padrão ajuda a manter as publicações diretas; não precisa escrever como especialista. Explique o que você aprendeu e deixe explícito o que ainda está em aberto.

## Etapas pequenas

Prefira um commit por parte compreensível do trabalho, por exemplo: documentação, parser, uma regra, relatório ou testes. Antes de publicar, confira `git status` e leia o resumo do commit para não incluir dados reais, relatórios gerados ou arquivos que não pretendia enviar.