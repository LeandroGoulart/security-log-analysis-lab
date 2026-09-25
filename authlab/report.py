"""Relatório HTML local, autocontido (sem CSS/JS/fontes externos).

Todo conteúdo vindo dos dados passa por html.escape antes de entrar no HTML.
"""

from __future__ import annotations

import html
from pathlib import Path

from .explain import explain, fmt_local, fmt_utc
from .windows import EVENT_NAMES, codes_text, failure_reason, logon_type_short

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--muted:#5b5b61;--line:#dcdcd8;--card:#fff;
--accent:#1f5f99;--warn:#8a5a00;--warnbg:#fff6e0;--hit:#fdeceb;--ok:#e9f5ec}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:.2em 0}
h2{font-size:1.25rem;margin:2em 0 .6em;padding-bottom:.3em;border-bottom:1px solid var(--line)}
h3{font-size:1.05rem;margin:1.2em 0 .4em}
.muted{color:var(--muted)}
.notice{background:var(--warnbg);border-left:4px solid var(--warn);padding:10px 14px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:16px 0}
.tag{display:inline-block;font-size:.8rem;padding:1px 8px;border-radius:10px;
background:#e8eef5;color:var(--accent);font-weight:600}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:.9rem}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{background:#f1f1ee}
tr.trigger td{background:var(--hit)}
tr.success td{background:var(--ok)}
.scroll{overflow-x:auto}
code{font-family:Consolas,"Cascadia Mono",monospace;font-size:.88em}
dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:8px 0}
dt{font-weight:600}
.plain{background:#f4f7fb;border-radius:6px;padding:10px 14px}
details summary{cursor:pointer;font-weight:600;margin:8px 0}
@media print{details{display:block} .card{break-inside:avoid}}
"""


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _table(header: list[str], rows: list[list[str]], row_classes: list[str] | None = None) -> str:
    head = "".join(f"<th>{e(h)}</th>" for h in header)
    body = []
    for i, row in enumerate(rows):
        cls = f' class="{row_classes[i]}"' if row_classes and row_classes[i] else ""
        body.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def _event_result(ev) -> str:
    if ev.event_id == 4624:
        return "Sucesso"
    return "Falha: " + failure_reason(ev.status, ev.sub_status)


def _event_rows(events, cfg, trigger_uid=None, roles=None):
    rows, classes = [], []
    for i, ev in enumerate(events, start=1):
        is_trigger = ev.event_uid == trigger_uid
        marker = " <strong>(disparo)</strong>" if is_trigger else ""
        rows.append([
            e(i),
            e(fmt_local(ev.timestamp_utc, cfg)) + "<br><span class=muted>"
            + e(fmt_utc(ev.timestamp_utc)) + "</span>",
            e(f"{ev.event_id} – {EVENT_NAMES[ev.event_id]}") + marker,
            e(_event_result(ev)) + "<br><code>" + e(codes_text(ev.status, ev.sub_status))
            + "</code>" if ev.event_id == 4625 else e(_event_result(ev)),
            e(f"{ev.domain or '—'}\\{ev.user or '—'}"),
            e(ev.src_ip or "(ausente)"),
            e(ev.host),
            e(logon_type_short(ev.logon_type)),
            "<code>" + e(ev.event_uid) + "</code><br>RecordID " + e(ev.event_record_id or "—"),
            e(ev.source_ref),
        ])
        classes.append("trigger" if is_trigger else ("success" if ev.event_id == 4624 else ""))
    header = ["#", "Horário", "Evento", "Resultado", "Conta", "IP de origem",
              "Registrado em (host)", "LogonType", "event_uid", "Origem (arquivo:linha)"]
    return header, rows, classes


def _li(items) -> str:
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"


def render_report(r, paths: dict[str, Path]) -> str:
    cfg = r.config
    p = r.parsed
    parts: list[str] = []
    add = parts.append

    add(f"<h1>{e(r.title)}</h1>")
    if r.description:
        add(f'<p><span class="tag">Descrição do cenário</span> {e(r.description)}</p>')
    add('<div class="notice"><strong>Um alerta é um indício para investigação, não uma '
        'confirmação de ataque.</strong> Os textos abaixo separam o que foi observado nos '
        'eventos das explicações possíveis, que precisam ser verificadas.</div>')
    add("<dl>")
    for label, value in [
        ("Execução", r.run_id),
        ("Gerado em", f"{fmt_local(r.generated_at, cfg)} · {fmt_utc(r.generated_at)}"),
        ("Fuso de exibição", f"{cfg.display_timezone_label} (UTC{cfg.display_utc_offset}); "
                             "todo horário também aparece em UTC"),
        ("Arquivo de entrada", p.source_file),
        ("SHA-256 da entrada", r.input_sha256),
        ("Configuração", cfg.source_path or "(em memória)"),
        ("AUTH-001", f"{'habilitada' if cfg.auth001.enabled else 'desabilitada'}; "
                     f"limiar {cfg.auth001.threshold} falhas; janela {cfg.auth001.window_minutes} min"),
        ("AUTH-003", f"{'habilitada' if cfg.auth003.enabled else 'desabilitada'}; sucesso em até "
                     f"{cfg.auth003.success_within_minutes} min após a última falha"),
    ]:
        add(f"<dt>{e(label)}</dt><dd>{e(value)}</dd>")
    add("</dl>")
    add('<p class="muted">Os limiares são valores didáticos de demonstração e não são '
        'recomendados para nenhum ambiente real sem calibração.</p>')

    # Qualidade dos dados
    add("<h2>1. Qualidade dos dados</h2>")
    add(_table(["Indicador", "Quantidade"], [
        [e("Registros lidos"), e(p.rows_read)],
        [e("Válidos"), e(len(p.events))],
        [e("Rejeitados (ver motivos abaixo)"), e(len(p.rejected))],
        [e("Duplicados removidos (mesmo host + channel + EventRecordID e mesmo conteúdo)"),
         e(len(p.duplicates))],
        [e("Possíveis duplicados mantidos (sem EventRecordID, conteúdo idêntico)"),
         e(p.possible_duplicates_kept)],
    ]))
    if p.extra_columns:
        add(f"<p>Colunas extras ignoradas: {e(', '.join(p.extra_columns))}</p>")
    rows = []
    for rid, s in r.stats.items():
        reasons = ", ".join(f"{k}: {v}" for k, v in sorted(s.ineligible_reasons.items())) or "—"
        rows.append([e(rid), e(s.candidates), e(s.eligible), e(reasons), e(s.alerts),
                     e(s.status_message())])
    add("<h3>Elegibilidade por regra</h3>")
    add(_table(["Regra", "Candidatos", "Elegíveis", "Não elegíveis (motivo: qtde)",
                "Alertas", "Situação"], rows))
    if p.rejected:
        add("<h3>Registros rejeitados</h3>")
        add(_table(["Origem (arquivo:linha)", "Motivo(s)"],
                   [[e(f"{x.source_file}:{x.source_line}"), e(" | ".join(x.reasons))]
                    for x in p.rejected]))
    if p.duplicates:
        add("<h3>Duplicados removidos</h3>")
        add(_table(["Origem (arquivo:linha)", "Duplicado de", "Primeira ocorrência (linha)"],
                   [[e(f"{d.source_file}:{d.source_line}"), f"<code>{e(d.event_uid)}</code>",
                     e(d.first_source_line)] for d in p.duplicates]))

    # Resumo
    add("<h2>2. Resumo dos alertas</h2>")
    if not r.alerts:
        add("<p><strong>Nenhum alerta gerado.</strong> Confira a situação de cada regra acima: "
            "\"nenhum alerta\" só tem valor quando havia dados elegíveis suficientes.</p>")
    else:
        add(_table(["Alerta", "Regra", "Conta", "Origem (IP)", "Destino (host)", "Período",
                    "Falhas", "Vinculado a"], [
            [f'<a href="#{e(a.alert_id)}">{e(a.alert_id)}</a>', e(f"{a.rule_id} – {a.rule_name}"),
             e(f"{a.key.domain}\\{a.key.user}"), e(a.key.src_ip), e(a.key.host),
             e(fmt_local(a.first_seen, cfg)) + " →<br>" + e(fmt_local(a.last_seen, cfg)),
             e(len(a.failures)), e(a.parent_alert_id or "—")]
            for a in r.alerts
        ]))

    # Detalhes
    if r.alerts:
        add("<h2>3. Alertas em detalhe</h2>")
    for a in r.alerts:
        x = explain(a, cfg)
        add(f'<section class="card" id="{e(a.alert_id)}">')
        add(f'<span class="tag">{e(a.rule_id)}</span>')
        add(f"<h3>{e(a.alert_id)} – {e(a.rule_name)}</h3>")
        add("<dl>")
        add(f"<dt>Conta</dt><dd>{e(a.key.domain)}\\{e(a.key.user)}</dd>")
        add(f"<dt>Origem (IP)</dt><dd>{e(a.key.src_ip)} "
            "<span class=muted>(indica origem de rede; não identifica uma pessoa)</span></dd>")
        add(f"<dt>Destino (host que registrou)</dt><dd>{e(a.key.host)}</dd>")
        if a.parent_alert_id:
            add(f'<dt>Alerta de origem</dt><dd><a href="#{e(a.parent_alert_id)}">'
                f"{e(a.parent_alert_id)}</a></dd>")
        add("</dl>")
        add(f'<div class="plain"><strong>Em linguagem simples:</strong> {e(x.plain_summary)}</div>')
        add("<h3>O que foi observado</h3>" + _li(x.observed))
        add(f"<h3>Por que a regra disparou</h3><p>{e(x.why)}</p>")
        add("<h3>Explicações possíveis (não confirmadas)</h3>" + _li(x.possible))
        add("<h3>O que precisa ser verificado</h3>" + _li(x.verify))
        add("<h3>Linha do tempo e evidências</h3>")
        add('<p class="muted">Linha destacada em vermelho: evento que completou o critério. '
            "Em verde: logon bem-sucedido. Cada evento aponta para a linha do arquivo de origem "
            f"e está em <code>{e(paths['evidence'].name)}</code>.</p>")
        header, rows, classes = _event_rows([ev for ev, _ in a.evidence], cfg,
                                            a.trigger_event.event_uid)
        add(_table(header, rows, classes))
        add("</section>")

    # Linha do tempo completa
    add("<h2>4. Linha do tempo completa</h2>")
    add(f"<details><summary>Mostrar os {len(p.events)} eventos válidos, em ordem "
        "cronológica</summary>")
    header, rows, classes = _event_rows(p.events, cfg)
    add(_table(header, rows, classes))
    add("</details>")

    # Limitações
    add("<h2>5. Limitações desta análise</h2>")
    add(_li([
        "Dados fictícios ou fornecidos em CSV próprio; não há leitura de EVTX nem do CSV "
        "exportado pelo Event Viewer.",
        "A correlação exige mesma conta, domínio, IP de origem e host. Tentativas distribuídas "
        "entre várias origens, contas ou destinos não são detectadas (ex.: password spraying).",
        "Ataques lentos, com intervalo entre falhas maior que a janela, não atingem o limiar.",
        "Eventos sem algum campo de correlação (inclusive IP ausente) não são avaliados; "
        "veja a tabela de elegibilidade.",
        "Timestamps iguais têm ordem indeterminada: um sucesso no mesmo instante da falha que "
        "completou o limiar não gera AUTH-003.",
        "Os códigos de falha são interpretados apenas quando constam na documentação da "
        "Microsoft usada no projeto; os demais aparecem como falha de autenticação.",
        "Não há contexto externo (inventário, DHCP, VPN, registros de mudança). Ele é "
        "indispensável para concluir.",
    ]))

    add("<h2>6. Próximos passos de investigação</h2>")
    add(_li([
        "Para cada alerta, responda às perguntas da seção \"O que precisa ser verificado\".",
        "Registre fatos, evidências (event_uid e linha), hipóteses e lacunas na ficha "
        "docs/ficha-investigacao.md.",
        "Classifique a conclusão como: atividade legítima confirmada, suspeita confirmada ou "
        "inconclusiva. Inconclusiva é uma resposta válida quando falta informação.",
        "Escreva um resumo curto para gestor, sem jargão, com prioridade justificada.",
    ]))

    add("<h2>7. Arquivos desta execução</h2>")
    add(_li([f"{k}: {v.name}" for k, v in paths.items()]))
    add('<p class="muted">Estes arquivos reproduzem dados de entrada. Com logs reais, trate-os '
        "como sensíveis e não os publique.</p>")

    return (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{e(r.title)} – Relatório</title><style>{CSS}</style></head>"
        f"<body><main>{''.join(parts)}</main></body></html>"
    )


def render_index(runs: list[tuple[str, str, str, dict, str]]) -> str:
    """Página inicial da demonstração. runs: (título, descrição, link, contagens, conferência)."""
    rows = []
    for title, desc, link, counts, check in runs:
        rows.append([f'<a href="{e(link)}">{e(title)}</a>', e(desc),
                     e(counts.get("AUTH-001", 0)), e(counts.get("AUTH-003", 0)), e(check)])
    body = (
        "<h1>Security Log Analysis Lab – Demonstração</h1>"
        '<div class="notice">Dados inteiramente fictícios. Limiares didáticos. '
        "Um alerta é um indício para investigação, não uma confirmação de ataque.</div>"
        + _table(["Cenário", "Descrição", "AUTH-001", "AUTH-003", "Conferência com o esperado"],
                 rows)
        + "<p>Depois de abrir um relatório, leia o README do cenário em <code>scenarios/</code>, "
          "responda às perguntas orientadoras e só então consulte o gabarito.</p>"
    )
    return ('<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Demonstração – Security Log Analysis Lab</title><style>{CSS}</style>"
            f"</head><body><main>{body}</main></body></html>")
