from app.models import Bill, BillStage, Highlight, Politician, VoteRecord, VoteSession


HIGHLIGHTS = [
    Highlight(title="Projetos em tramitação", subtitle="Base federal inicial", metric="1.248"),
    Highlight(title="Votações nominais", subtitle="Últimos 30 dias", metric="312"),
    Highlight(title="Parlamentares ativos", subtitle="Câmara e Senado", metric="594"),
]

POLITICIANS = [
    Politician(id=1, nome="Ana Ribeiro", partido="PSB", uf="SP", cargo="Deputada Federal", casa="Câmara dos Deputados"),
    Politician(id=2, nome="Carlos Menezes", partido="PSD", uf="BA", cargo="Senador", casa="Senado Federal"),
    Politician(id=3, nome="Marina Souza", partido="REDE", uf="PE", cargo="Deputada Federal", casa="Câmara dos Deputados"),
]

BILLS = [
    Bill(
        id=101,
        sigla="PL",
        numero=2450,
        ano=2026,
        ementa="Institui regras nacionais de transparência legislativa em formato digital aberto.",
        resumo="Proposta usada como exemplo do MVP para demonstrar tramitação, comissões, plenário, Senado e sanção.",
        autor_principal="Ana Ribeiro",
        casa_origem="Câmara dos Deputados",
        status_atual="Aguardando análise na CCJC",
        tema="Transparência pública",
        impacto_financeiro=True,
        precisa_plenario=False,
        timeline=[
            BillStage(ordem=1, fase="Apresentação", orgao="Mesa Diretora", descricao="Projeto apresentado e publicado."),
            BillStage(ordem=2, fase="Comissão de mérito", orgao="CTASP", descricao="Parecer favorável aprovado."),
            BillStage(ordem=3, fase="Impacto financeiro", orgao="CFT", descricao="Adequação orçamentária reconhecida."),
            BillStage(ordem=4, fase="Constitucionalidade", orgao="CCJC", descricao="Aguardando votação do parecer.", status="current"),
            BillStage(ordem=5, fase="Senado", orgao="Plenário do Senado", descricao="Etapa futura.", status="upcoming"),
            BillStage(ordem=6, fase="Presidência", orgao="Presidência da República", descricao="Sanção ou veto.", status="upcoming"),
        ],
        votacoes=[
            VoteSession(
                id=9001,
                titulo="Aprovação do parecer na CTASP",
                orgao="CTASP",
                data="2026-05-10",
                resultado="Aprovado",
                quorum="24 presentes",
                votos=[
                    VoteRecord(politician_id=1, politician_name="Ana Ribeiro", voto="Sim", partido="PSB", uf="SP"),
                    VoteRecord(politician_id=3, politician_name="Marina Souza", voto="Sim", partido="REDE", uf="PE"),
                ],
            )
        ],
    )
]
