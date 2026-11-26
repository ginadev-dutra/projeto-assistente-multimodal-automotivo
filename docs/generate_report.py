from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'relatorio_desenvolvimento.pdf'
FONT_DIR = Path(r'C:\Windows\Fonts')
pdfmetrics.registerFont(TTFont('Arial', str(FONT_DIR / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold', str(FONT_DIR / 'arialbd.ttf')))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='CoverTitle',
    parent=styles['Title'],
    fontName='Arial-Bold',
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    textColor=HexColor('#15324b'),
    spaceAfter=12,
))
styles.add(ParagraphStyle(
    name='H1x',
    parent=styles['Heading1'],
    fontName='Arial-Bold',
    fontSize=15,
    leading=18,
    textColor=HexColor('#15324b'),
    spaceAfter=7,
))
styles.add(ParagraphStyle(
    name='H2x',
    parent=styles['Heading2'],
    fontName='Arial-Bold',
    fontSize=10.5,
    leading=13,
    textColor=HexColor('#1e5373'),
    spaceBefore=4,
    spaceAfter=3,
))
styles.add(ParagraphStyle(
    name='Bodyx',
    parent=styles['BodyText'],
    fontName='Arial',
    fontSize=8.2,
    leading=10.8,
    spaceAfter=4,
))
styles.add(ParagraphStyle(
    name='Smallx',
    parent=styles['BodyText'],
    fontName='Arial',
    fontSize=7,
    leading=8.7,
    textColor=HexColor('#333333'),
    spaceAfter=3,
))
styles.add(ParagraphStyle(
    name='Captionx',
    parent=styles['BodyText'],
    fontName='Arial',
    fontSize=7.1,
    leading=9,
    alignment=TA_CENTER,
    textColor=HexColor('#444444'),
    spaceBefore=4,
    spaceAfter=4,
))
styles.add(ParagraphStyle(
    name='Cellx',
    parent=styles['BodyText'],
    fontName='Arial',
    fontSize=6.8,
    leading=8.3,
    spaceAfter=0,
))
styles.add(ParagraphStyle(
    name='CellBoldx',
    parent=styles['BodyText'],
    fontName='Arial-Bold',
    fontSize=6.8,
    leading=8.3,
    spaceAfter=0,
))


def p(text, style='Bodyx'):
    return Paragraph(text, styles[style])


def bullets(items):
    return [p('• ' + item) for item in items]


def table(rows, widths):
    data = [
        [p(str(value), 'CellBoldx' if row_index == 0 else 'Cellx') for value in row]
        for row_index, row in enumerate(rows)
    ]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    result.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#cbd5df')),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f0f5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#15324b')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f7f9fb')]),
    ]))
    return result


class ArchitectureDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 510
        self.height = 158

    def draw(self):
        canvas = self.canv
        nodes = [
            (2, 'Entradas', 'texto / foto / áudio'),
            (88, 'Gradio', 'app/app.py'),
            (174, 'Contexto', 'Whisper + RAG'),
            (260, 'Modelos', 'Gemini / Groq'),
            (346, 'Pydantic', 'saída validada'),
            (432, 'Interface', 'diagnóstico'),
        ]
        y, width, height = 100, 76, 39
        for x, title, subtitle in nodes:
            canvas.setFillColor(HexColor('#eef5f8'))
            canvas.setStrokeColor(HexColor('#32627d'))
            canvas.roundRect(x, y, width, height, 5, fill=1, stroke=1)
            canvas.setFillColor(HexColor('#15324b'))
            canvas.setFont('Arial-Bold', 7.2)
            canvas.drawCentredString(x + width / 2, y + 24, title)
            canvas.setFont('Arial', 6.2)
            canvas.drawCentredString(x + width / 2, y + 11, subtitle)
        canvas.setStrokeColor(HexColor('#526675'))
        for x in (78, 164, 250, 336, 422):
            canvas.line(x, 119, x + 8, 119)
            canvas.line(x + 5, 122, x + 8, 119)
            canvas.line(x + 5, 116, x + 8, 119)
        for x, box_width, title, subtitle in (
            (82, 104, 'Manual PDF', '270 páginas'),
            (202, 104, 'ChromaDB', 'uma página por documento'),
            (333, 145, 'logs/usage.csv', 'tokens • latência • custo'),
        ):
            canvas.setFillColor(HexColor('#f7f7f2'))
            canvas.setStrokeColor(HexColor('#84917e'))
            canvas.roundRect(x, 28, box_width, 35, 4, fill=1, stroke=1)
            canvas.setFillColor(HexColor('#243b2c'))
            canvas.setFont('Arial-Bold', 7)
            canvas.drawCentredString(x + box_width / 2, 49, title)
            canvas.setFont('Arial', 6)
            canvas.drawCentredString(x + box_width / 2, 37, subtitle)
        canvas.line(186, 45, 202, 45)
        canvas.line(190, 48, 186, 45)
        canvas.line(190, 42, 186, 45)
        canvas.line(254, 63, 216, 100)
        canvas.line(251, 65, 254, 63)
        canvas.line(254, 67, 254, 63)
        canvas.line(298, 100, 365, 63)
        canvas.line(361, 63, 365, 63)
        canvas.line(364, 67, 365, 63)
        canvas.setFont('Arial', 6)
        canvas.setFillColor(HexColor('#555555'))
        canvas.drawString(
            2,
            8,
            'A foto só segue para Gemini quando fornecida; conversas não são persistidas.',
        )


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(HexColor('#d6dce2'))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont('Arial', 7)
    canvas.setFillColor(HexColor('#58636d'))
    canvas.drawString(
        18 * mm,
        10 * mm,
        'GuiaDeBordo IA Automotivo • Trabalho Orientado PUC Minas • 26/11/2026',
    )
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=14 * mm,
    bottomMargin=19 * mm,
    title='Relatório de desenvolvimento — GuiaDeBordo IA Automotivo',
    author=(
        'Gina Rocha Dutra, Luciano Goldoni, Luiz Guilherme de Almeida '
        'e Raphael Rodrigues Lima'
    ),
)
story = []

story.extend([
    Spacer(1, 8 * mm),
    p('RELATÓRIO DE DESENVOLVIMENTO', 'CoverTitle'),
    p('GuiaDeBordo IA Automotivo', 'CoverTitle'),
    Spacer(1, 4 * mm),
    p(
        '<b>Integrantes</b><br/>Gina Rocha Dutra<br/>Luciano Goldoni'
        '<br/>Luiz Guilherme de Almeida<br/>Raphael Rodrigues Lima'
    ),
    p(
        '<b>Repositório</b><br/><link '
        'href="https://github.com/ginadev-dutra/projeto-assistente-multimodal-automotivo" '
        'color="#176b87">github.com/ginadev-dutra/'
        'projeto-assistente-multimodal-automotivo</link>'
    ),
    p('<b>Aplicação publicada</b><br/>Não publicada; publicação é opcional.'),
    Spacer(1, 3 * mm),
    p('1. Objetivo do projeto', 'H1x'),
    p(
        'Construir um protótipo interativo que recebe uma foto de alerta do painel '
        'e/ou relato em texto ou áudio, consulta o manual do Volkswagen Polo por '
        'RAG e produz um diagnóstico estruturado, com urgência, explicação, ações '
        'recomendadas e resumo para oficina. O resultado orienta a próxima ação '
        'do motorista, sem substituir inspeção profissional.'
    ),
    p('2. Problema que resolve', 'H1x'),
    p(
        'Uma luz do painel pode ser difícil de identificar e interpretar em '
        'contexto. O protótipo combina evidência visual, relato do motorista e '
        'trechos de um manual específico. Isso reduz a dependência de uma '
        'descrição textual precisa, mas não elimina erros de identificação nem '
        'valida uma falha mecânica.'
    ),
    p('3. Metodologia', 'H1x'),
    p(
        'O trabalho integrou Gemini/Groq e Whisper, interface Gradio, validação '
        'Pydantic, recuperação semântica do manual, conjunto de 10 perguntas e '
        'métrica acerto@3, instrumentação de uso/custo e testes controlados de '
        'falha. Os resultados abaixo distinguem chamadas reais observadas de '
        'entradas sintéticas.'
    ),
    p(
        '<b>Nota:</b> o caso de sucesso usa imagem sintética e execução real '
        'do protótipo; não representa veículo real nem valida diagnóstico em campo.',
        'Smallx',
    ),
    PageBreak(),
])

story.extend([
    p('3.1 Dados e 3.2 Arquitetura', 'H1x'),
    p(
        'O corpus é um único manual oficial Volkswagen Brasil, <i>Manual de '
        'instruções — Polo</i>, edição/identificação V2, R2, Brazil, pt_BR, '
        'fechamento 18/12/2024, edição impressa 03/2025, código 2GB012766BO. '
        'O PDF possui 270 páginas; todas passam pelo filtro atual de extração '
        '(mais de 50 caracteres). Fonte: <link href="https://www.vw.com.br/idhub/'
        'content/dam/onehub_pkw/importers/br/literatura-de-bordo/manual-novo-polo/'
        'my26/26A_5B1_POL_66_Manual_de_instrucoes.pdf" color="#176b87">'
        'Volkswagen Brasil</link>.'
    ),
    ArchitectureDiagram(),
    table([
        ['Dado', 'Quantidade/origem', 'Uso'],
        ['Manual Polo', '1 PDF; 270 páginas', 'RAG; uma página por documento no ChromaDB.'],
        ['Avaliação RAG', '10 perguntas anotadas', 'Acerto@3; dados em dados/exemplos/perguntas_rag.json.'],
        [
            'Entradas de demonstração',
            '1 imagem e 1 áudio sintetizados localmente',
            'Testes sem dados pessoais; não representam usuário ou veículo real.',
        ],
    ], [31 * mm, 55 * mm, 82 * mm]),
    p('Privacidade e direitos', 'H2x'),
    p(
        'Texto, trechos do manual e imagem seguem para provedores externos '
        'conforme o fluxo; áudio vai ao endpoint Groq para transcrição. O log '
        'local registra metadados, não conteúdo ou chaves. A responsável pelo '
        'projeto confirmou autorização para manter/versionar o manual; isso '
        'não implica licença aberta para outros usos. Preservar fonte e avisos '
        'de copyright. Não enviar rostos, placas identificáveis, dados pessoais '
        'ou documentos sigilosos. Serviços gratuitos podem tratar dados segundo '
        'seus termos.'
    ),
    p(
        'Não há histórico conversacional persistente. O índice ChromaDB e o '
        'cache são locais/em memória no processo.',
        'Smallx',
    ),
    PageBreak(),
])

story.extend([
    p('3.3 Modelos e 3.4 Prompts e testes', 'H1x'),
    p(
        'A rota visual usa Gemini porque o Groq configurado é textual. Consultas '
        'sem imagem priorizam Groq <i>openai/gpt-oss-20b</i> e podem recorrer a '
        'Gemini. O áudio é transcrito por Groq Whisper '
        '<i>whisper-large-v3-turbo</i>; a transcrição entra no diagnóstico. '
        'Retentativas/fallback aumentam disponibilidade potencial, mas também '
        'latência e custo.'
    ),
    table([
        ['Etapa', 'Modelo/artefato', 'Evidência/decisão'],
        [
            'Visão',
            'Gemini; resposta em gemini-3.1-flash-lite',
            'Imagem sintética; 4.064 tokens entrada, 341 saída, 2,37 s na chamada final.',
        ],
        [
            'Texto',
            'Groq openai/gpt-oss-20b',
            'Uma chamada observada: 2.667 tokens entrada, 708 saída, 1,52 s.',
        ],
        [
            'Áudio',
            'Whisper Turbo + Groq LLM',
            'Transcrição medida; UI não mostrou resposta final antes do fim do teste.',
        ],
        [
            'Saída',
            'DiagnosticReport (Pydantic)',
            'Valida símbolo, urgência, significado, prognóstico, ações e resumo.',
        ],
    ], [23 * mm, 50 * mm, 95 * mm]),
    p('Prompts e critério de teste', 'H2x'),
    p(
        'Prompts em prompts/diagnostico_v1.txt e prompts/groq_json_v1.txt. A '
        'saída é um objeto estruturado validado pelo esquema Pydantic. O conjunto '
        'de 10 casos está em dados/exemplos/perguntas_rag.json; conta como acerto '
        'quando a página esperada aparece entre as três primeiras (acerto@3).'
    ),
    p(
        'Foram aprovados 10 testes unitários de custos e falhas: imagem inválida, '
        'indisponibilidade do Gemini, erro de transcrição, tarifas, amostras '
        'incompletas e ausência de conteúdo sensível no log. Comando: '
        '<font name="Arial-Bold">python -m unittest tests.test_error_handling '
        'tests.test_usage_service -v</font>.'
    ),
    p(
        'Não foi feito benchmark controlado de qualidade/latência entre todos '
        'os modelos. A comparação sistemática permanece trabalho futuro.',
        'Smallx',
    ),
    PageBreak(),
])

story.extend([
    p('3.5 Contexto e 4. Resultados', 'H1x'),
    p(
        'O protótipo não mantém memória de conversa. Para consultar instruções '
        'específicas do veículo, cada página extraída do manual é um documento '
        'independente no índice semântico; a busca retorna até três páginas com '
        'fonte e número. A granularidade mantém referências localizáveis, mas '
        'ainda há falhas de recuperação.'
    ),
    p('Avaliação de recuperação (10 perguntas)', 'H2x'),
    table([
        ['Estratégia', 'Acertos', 'Decisão'],
        ['Semântica atual; 1 página/documento', '8/10 (80%)', 'Baseline em produção.'],
        ['Consulta compactada + RRF', '9/10 (90%)', 'Experimento no avaliador.'],
        ['BM25 + semântica + RRF', '9/10 (90%)', 'Não supera consulta compactada; não adotado.'],
        ['Janelas de 2 ou 3 páginas', '8/10 (80%)', 'Não adotadas.'],
    ], [69 * mm, 30 * mm, 69 * mm]),
    p('Limitações da métrica', 'H2x'),
    p(
        'O baseline errou rag-09 (nível do óleo; referência página 195) e rag-10 '
        '(congelamento do líquido; referência página 197). Consulta compactada '
        'recuperou rag-10 no top 3, mas rag-09 continuou falhando. As estratégias '
        'experimentais não foram promovidas à busca de produção. Acerto@3 mede '
        'recuperação, não correção do diagnóstico; 10 perguntas não provam '
        'generalização.'
    ),
    p(
        'Na execução com imagem sintética, a UI exibiu urgência “Médio”, ações '
        'cautelosas e referência à página física 166 do PDF (página impressa 164). '
        'A resposta combina EPC e sistema de emissões. A entrada artificial '
        'prova a execução do caminho visual, não a identificação correta de um '
        'símbolo de carro real. Conferir o pictograma, a fonte e a recomendação '
        'com pessoa qualificada.'
    ),
    PageBreak(),
])

story.extend([
    p('3.6 Execução e telas — caso concluído', 'H1x'),
    p(
        'Instruções no README: criar/ativar ambiente virtual, instalar '
        '<font name="Arial-Bold">pip install -r requirements.txt</font>, '
        'configurar .env, colocar o manual em manuals/ e executar '
        '<font name="Arial-Bold">python -m app.app</font>. A publicação é '
        'opcional e não foi realizada.'
    ),
    Spacer(1, 2 * mm),
    Image(
        str(ROOT / 'docs' / 'evidencias_caso_sintetico.png'),
        width=235,
        height=235 * 2160 / 826,
    ),
    p(
        'Figura 1 — Execução real na interface Gradio com imagem sintética e '
        'relato de teste. O modelo retornou “EPC ou falha no sistema de emissões”, '
        'urgência média e recomendação de avaliação profissional. A entrada é '
        'artificial; não constitui diagnóstico de veículo real.',
        'Captionx',
    ),
    PageBreak(),
])

story.extend([
    p('5. Custos: uso medido e projeção', 'H1x'),
    p(
        'O log local registra provedor/modelo, operação, status, tokens quando '
        'disponíveis, duração do áudio, latência e custo estimado. Preços de '
        'lista não são fatura. Tentativas são eventos separados; chamadas '
        'sintéticas são excluídas do estimador.'
    ),
    table([
        ['Execução', 'Tokens/duração', 'Latência', 'Custo conhecido'],
        [
            'Texto observado — Groq GPT-OSS-20B',
            '2.667 entrada / 708 saída',
            '1,52 s',
            'US$ 0,000412425',
        ],
        [
            'Imagem sintética — Gemini 3.1 Flash-Lite',
            '4.064 entrada / 341 saída',
            '2,37 s',
            'US$ 0,0015275',
        ],
        [
            'Quatro tentativas Gemini anteriores',
            'Sem metadados de uso',
            '4,95; 4,79; 30,51; 4,55 s',
            'Desconhecido',
        ],
        [
            'Whisper — áudio sintético',
            '12,99 s de áudio',
            '2,96 s',
            'US$ 0,000144333',
        ],
        [
            'Groq após transcrição sintética',
            '2.748 entrada / 688 saída',
            '1,54 s',
            'US$ 0,0004125',
        ],
    ], [43 * mm, 43 * mm, 34 * mm, 48 * mm]),
    p(
        'Cenário: 50 usuários × 10 consultas/dia × 30 dias = '
        '<b>15.000 consultas/mês</b>. Com a única solicitação observada e '
        'completa (texto): 15.000 × US$ 0,000412425 = US$ 6,186375 ≈ '
        '<b>US$ 6,19/mês</b> se todas fossem iguais a essa consulta textual. '
        'É uma extrapolação ilustrativa de uma amostra única, não uma projeção '
        'confiável do mix multimodal. O script alerta que a amostra é pequena.'
    ),
    p(
        'O custo total da solicitação de imagem não é conhecido porque quatro '
        'tentativas anteriores não retornaram uso faturável. O teste de áudio '
        'teve chamadas registradas, mas a UI não mostrou resultado final e ele '
        'foi excluído da projeção. Não há dados suficientes para custo mensal '
        'multimodal confiável. Tarifas e limitações detalhadas em docs/api_costs.md.',
        'Smallx',
    ),
    PageBreak(),
])

story.extend([
    p('6. Segurança e riscos — caso de erro', 'H1x'),
    p(
        'Credenciais ficam no .env, fora do Git; .env.example tem apenas os '
        'nomes das variáveis. Imagens, textos, transcrições e trechos do manual '
        'podem sair do computador rumo aos provedores configurados. O log local '
        'não registra conteúdo ou chaves.'
    ),
    p(
        'Riscos: identificação errada, alucinação, citação imprecisa, prompt '
        'injection em conteúdo recebido, limites/indisponibilidade de API, '
        'exposição de dados pessoais e custo de retries. A aplicação informa '
        'falhas visuais e recomenda cautela, mas não substitui validação humana '
        'ou assistência profissional.'
    ),
    Spacer(1, 2 * mm),
    Image(
        str(ROOT / 'docs' / 'evidencias_erro_gemini.png'),
        width=330,
        height=330 * 1341 / 826,
    ),
    p(
        'Figura 2 — Falha controlada na UI com Gemini sem chave: mensagem '
        'explícita de indisponibilidade. Para evitar custos, o RAG foi '
        'substituído por contexto de teste e nenhuma API externa foi chamada. '
        'Não simula uma indisponibilidade externa real.',
        'Captionx',
    ),
    PageBreak(),
])

story.extend([
    p('7. Uso de IA e 8. Limitações e próximos passos', 'H1x'),
    p(
        'REGISTRO_IA.md documenta onde o assistente ajudou, correções feitas '
        'pela equipe e alternativas recusadas. O assistente apoiou estrutura, '
        'integração, telemetria, testes RAG, experimentos e documentação. A '
        'equipe manteve RRF/BM25 fora da busca de produção e confirmou '
        'autorização para versionar o manual. Os integrantes respondem pelo '
        'código e pelas decisões do protótipo.'
    ),
    p('Limitações observadas', 'H2x'),
])
story.extend(bullets([
    'Há apenas uma solicitação real observada, completa e não sintética de texto na projeção; amostra muito pequena.',
    'A imagem funcionou após quatro tentativas Gemini com falha; custo dessas tentativas desconhecido e latência elevada.',
    'No teste de áudio, Whisper e Groq registraram sucesso de API, mas a UI permaneceu “Analisando” por mais de 165 s e não exibiu resposta antes de o teste ser encerrado. Investigar parsing, fallback e tempo de resposta.',
    'O RAG tem 10 perguntas e um único manual; acerto@3 não demonstra qualidade ou segurança mecânica geral.',
    'As entradas de demonstração são artificiais; faltam testes de campo autorizados e avaliação humana das respostas.',
]))
story.extend([
    p('Próximos passos prioritários', 'H2x'),
])
story.extend(bullets([
    'Investigar e corrigir o estado “Analisando” no fluxo de áudio e repetir o teste end-to-end.',
    'Coletar ao menos cinco solicitações completas por modalidade esperada, com mix representativo, e revisar tarifas.',
    'Ampliar o conjunto de testes e avaliar respostas/citações com revisão humana.',
    'Testar riscos de privacidade, prompt injection e segurança das recomendações.',
]))
story.extend([
    p(
        'O repositório contém este relatório, documentação da arquitetura e '
        'custos, entradas sintéticas e duas capturas da interface. A estimativa '
        'mensal multimodal e a validação end-to-end do áudio permanecem '
        'pendentes; não foram apresentadas como concluídas.'
    ),
    p(
        'Fontes oficiais do manual e das tarifas estão em '
        'docs/architecture_and_data.md e docs/api_costs.md.',
        'Smallx',
    ),
])

doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
print(OUTPUT)
print(f'bytes={OUTPUT.stat().st_size}')
