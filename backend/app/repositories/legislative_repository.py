from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.entities import BillEntity, HighlightEntity, PoliticianEntity, VoteEventEntity
from app.models import Bill, BillStage, Highlight, Politician, PoliticianHistory, PoliticianTimelineEvent, PoliticianVoteHistory, VoteSession


class LegislativeRepository:
    def list_highlights(self, db: Session) -> list[Highlight]:
        bills_count = db.query(BillEntity).count()
        votes_count = db.query(VoteEventEntity).count()
        politicians_count = db.query(PoliticianEntity).count()

        if bills_count == 0 and votes_count == 0 and politicians_count == 0:
            rows = db.query(HighlightEntity).order_by(HighlightEntity.id.asc()).all()
            return [Highlight(title=row.title, subtitle=row.subtitle, metric=row.metric) for row in rows]

        return [
            Highlight(title="Projetos monitorados", subtitle="Base legislativa disponível", metric=str(bills_count)),
            Highlight(title="Eventos de voto", subtitle="Histórico nominal disponível", metric=str(votes_count)),
            Highlight(title="Parlamentares catalogados", subtitle="Registros sincronizados", metric=str(politicians_count)),
        ]

    def list_politicians(
        self,
        db: Session,
        query: str | None = None,
        cargo: list[str] | None = None,
        partido: list[str] | None = None,
        uf: list[str] | None = None,
        cidade: list[str] | None = None,
        status_politico: list[str] | None = None,
        identidade_tipo: str | None = None,
    ) -> list[Politician]:
        real_count = db.query(PoliticianEntity).filter(PoliticianEntity.fonte != 'seed').count()
        statement = db.query(PoliticianEntity)
        if real_count > 0:
            statement = statement.filter(PoliticianEntity.fonte != 'seed')
        if identidade_tipo == 'historica':
            statement = statement.filter(PoliticianEntity.identidade_tipo == 'historica')
        elif identidade_tipo == 'todas':
            pass
        else:
            statement = statement.filter(PoliticianEntity.identidade_tipo != 'historica')

        if query:
            like = f"%{query}%"
            statement = statement.filter(PoliticianEntity.nome.ilike(like))
        if cargo:
            statement = statement.filter(PoliticianEntity.cargo.in_(cargo))
        if partido:
            statement = statement.filter(PoliticianEntity.partido.in_(partido))
        if uf:
            statement = statement.filter(PoliticianEntity.uf.in_(uf))
        if cidade:
            statement = statement.filter(PoliticianEntity.cidade.in_(cidade))
        if status_politico:
            statement = statement.filter(PoliticianEntity.status_politico.in_(status_politico))

        rows = statement.order_by(PoliticianEntity.nome.asc()).all()
        return [
            Politician(
                id=row.id,
                canonical_politician_id=row.canonical_politician_id,
                nome=row.nome,
                partido=row.partido,
                uf=row.uf,
                cidade=row.cidade,
                cargo=row.cargo,
                casa=row.casa,
                foto_url=row.foto_url,
                ativo=row.ativo,
                status_politico=row.status_politico,
                identidade_tipo=row.identidade_tipo,
                legislatura=row.legislatura,
                mandato_inicio=row.mandato_inicio,
                mandato_fim=row.mandato_fim,
                fonte=row.fonte,
                origem_externa_id=row.origem_externa_id,
                origem_dados=row.origem_dados,
                ultima_sincronizacao=row.ultima_sincronizacao.isoformat() + 'Z' if row.ultima_sincronizacao else None,
            )
            for row in rows
        ]

    def get_politician(self, db: Session, politician_id: int) -> Politician | None:
        row = db.get(PoliticianEntity, politician_id)
        if row is None:
            return None
        if row.identidade_tipo == 'historica' and row.canonical_politician_id is not None:
            canonical = db.get(PoliticianEntity, row.canonical_politician_id)
            if canonical is not None:
                row = canonical
        return Politician(
            id=row.id,
            canonical_politician_id=row.canonical_politician_id,
            nome=row.nome,
            partido=row.partido,
            uf=row.uf,
            cidade=row.cidade,
            cargo=row.cargo,
            casa=row.casa,
            foto_url=row.foto_url,
            ativo=row.ativo,
            status_politico=row.status_politico,
            identidade_tipo=row.identidade_tipo,
            legislatura=row.legislatura,
            mandato_inicio=row.mandato_inicio,
            mandato_fim=row.mandato_fim,
            fonte=row.fonte,
            origem_externa_id=row.origem_externa_id,
            origem_dados=row.origem_dados,
            ultima_sincronizacao=row.ultima_sincronizacao.isoformat() + 'Z' if row.ultima_sincronizacao else None,
        )

    def _build_politician_timeline(self, row: PoliticianEntity) -> list[PoliticianTimelineEvent]:
        origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
        historico = origem_dados.get('historico') if isinstance(origem_dados.get('historico'), list) else []
        eventos = origem_dados.get('eventos') if isinstance(origem_dados.get('eventos'), list) else []
        mandatos_externos = origem_dados.get('mandatosExternos') if isinstance(origem_dados.get('mandatosExternos'), list) else []
        extra_historical_events = origem_dados.get('extra_historical_events') if isinstance(origem_dados.get('extra_historical_events'), list) else []
        timeline_items: list[dict] = []
        elected_terms = 0
        had_cassation = False

        for item in historico:
            descricao_status = str(item.get('descricaoStatus') or '').strip()
            data = item.get('dataHora')
            situacao = str(item.get('situacao') or '').strip()
            tipo = 'historico'
            titulo = situacao or 'Atualização de mandato'
            descricao = descricao_status or 'Atualização registrada pela Câmara dos Deputados.'
            texto = ' '.join(
                part
                for part in [
                    descricao_status.lower(),
                    situacao.lower(),
                    str(item.get('condicaoEleitoral') or '').strip().lower(),
                ]
                if part
            )

            if ('entrada' in texto or 'posse' in texto) and had_cassation:
                tipo = 'retorno'
                titulo = 'Retorno ao cargo'
            elif 'entrada' in texto or 'posse' in texto:
                elected_terms += 1
                tipo = 'eleicao'
                titulo = f'Eleito pela {elected_terms}ª vez'
                descricao = f'{descricao}. Mandato na legislatura {item.get("idLegislatura") or "não informada"}.'
            elif 'retorno' in texto or 'reassun' in texto:
                tipo = 'retorno'
                titulo = 'Retorno ao cargo'
            elif 'cass' in texto or 'perda de mandato por resolução' in texto or 'perda de mandato' in texto:
                tipo = 'cassacao'
                titulo = 'Cassação'
                had_cassation = True
            elif 'saída' in texto or 'afastamento' in texto or 'fim de mandato' in texto or 'licença' in texto or 'renúncia' in texto or 'renuncia' in texto:
                tipo = 'saida'
                titulo = 'Saída do cargo'

            timeline_items.append(
                {
                    'data': data,
                    'titulo': titulo,
                    'descricao': descricao,
                    'tipo': tipo,
                    'fonte': 'camara',
                    'legislatura': item.get('idLegislatura'),
                    'orgao': 'Câmara dos Deputados',
                }
            )

        for item in mandatos_externos:
            ano_inicio = item.get('anoInicio')
            ano_fim = item.get('anoFim')
            cargo = item.get('cargo') or 'Mandato externo'
            municipio = item.get('municipio') or ''
            uf = item.get('siglaUf') or ''
            local = ', '.join(part for part in [municipio, uf] if part)
            descricao = cargo if not local else f'{cargo} em {local}'
            if ano_inicio or ano_fim:
                descricao = f'{descricao} ({ano_inicio or "?"} - {ano_fim or "atual"})'
            timeline_items.append(
                {
                    'data': f'{ano_inicio}-01-01' if ano_inicio else None,
                    'titulo': cargo,
                    'descricao': descricao,
                    'tipo': 'mandato_externo',
                    'fonte': 'camara',
                    'legislatura': None,
                    'orgao': local or None,
                }
            )

        for item in eventos:
            descricao_tipo = item.get('descricaoTipo') or 'Evento político'
            descricao = item.get('descricao') or descricao_tipo
            orgaos = item.get('orgaos') if isinstance(item.get('orgaos'), list) else []
            orgao = None
            if orgaos:
                orgao = orgaos[0].get('nome') or orgaos[0].get('sigla')
            timeline_items.append(
                {
                    'data': item.get('dataHoraInicio') or item.get('dataHoraFim'),
                    'titulo': descricao_tipo,
                    'descricao': descricao,
                    'tipo': 'evento',
                    'fonte': 'camara',
                    'legislatura': None,
                    'orgao': orgao,
                }
            )

        for item in extra_historical_events:
            if not isinstance(item, dict):
                continue
            timeline_items.append(
                {
                    'data': item.get('data'),
                    'titulo': item.get('titulo') or 'Evento histórico',
                    'descricao': item.get('descricao') or 'Atualização histórica complementar.',
                    'tipo': item.get('tipo') or 'evento',
                    'fonte': item.get('fonte') or 'curated_web',
                    'legislatura': item.get('legislatura'),
                    'orgao': item.get('orgao'),
                }
            )

        ordered = sorted(timeline_items, key=lambda item: item.get('data') or '', reverse=True)
        return [
            PoliticianTimelineEvent(
                ordem=index,
                data=item.get('data'),
                titulo=item.get('titulo') or 'Evento político',
                descricao=item.get('descricao') or 'Atualização política registrada.',
                tipo=item.get('tipo') or 'evento',
                fonte=item.get('fonte') or 'camara',
                legislatura=item.get('legislatura'),
                orgao=item.get('orgao'),
            )
            for index, item in enumerate(ordered, start=1)
        ]

    @staticmethod
    def _bill_relevance_score(row: BillEntity) -> int:
        origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
        score = origem_dados.get('relevance_score')
        return score if isinstance(score, int) else 0

    @staticmethod
    def _bill_authors(row: BillEntity) -> list[str]:
        origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
        autores = origem_dados.get('autores') if isinstance(origem_dados.get('autores'), list) else []
        names = []
        for autor in autores:
            if not isinstance(autor, dict):
                continue
            author_name = autor.get('nomeAutor') or autor.get('nome') or autor.get('nomeParlamentar')
            if isinstance(author_name, str) and author_name.strip():
                names.append(author_name.strip())
        if names:
            return list(dict.fromkeys(names))
        return [row.autor_principal] if row.autor_principal else []

    @staticmethod
    def _bill_parties(row: BillEntity) -> list[str]:
        origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
        autores = origem_dados.get('autores') if isinstance(origem_dados.get('autores'), list) else []
        parties = []
        for autor in autores:
            if not isinstance(autor, dict):
                continue
            party = autor.get('siglaPartido') or autor.get('partido')
            if isinstance(party, str) and party.strip():
                parties.append(party.strip())
        return list(dict.fromkeys(parties))

    def list_bills(self, db: Session, sort_by: str | None = None) -> list[Bill]:
        real_count = db.query(BillEntity).filter(BillEntity.fonte != 'seed').count()
        statement = db.query(BillEntity)
        if real_count > 0:
            statement = statement.filter(BillEntity.fonte != 'seed')
        rows = statement.all()
        if sort_by == 'relevance':
            rows = sorted(rows, key=lambda row: (self._bill_relevance_score(row), row.ano, row.numero), reverse=True)
        else:
            rows = sorted(rows, key=lambda row: (row.ano, row.numero), reverse=True)
        return [self._map_bill(row) for row in rows]

    def search_approved_bills(
        self,
        db: Session,
        theme: str | None = None,
        author: str | None = None,
        party: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        page: int = 1,
        page_size: int = 12,
        sort_by: str | None = None,
    ) -> tuple[list[Bill], int]:
        statement = db.query(BillEntity).filter(BillEntity.aprovada.is_(True))
        if db.query(BillEntity).filter(BillEntity.fonte != 'seed').count() > 0:
            statement = statement.filter(BillEntity.fonte != 'seed')
        if year_from is not None:
            statement = statement.filter(BillEntity.ano >= year_from)
        if year_to is not None:
            statement = statement.filter(BillEntity.ano <= year_to)
        if theme:
            like = f"%{theme}%"
            statement = statement.filter(
                or_(
                    BillEntity.tema.ilike(like),
                    BillEntity.ementa.ilike(like),
                    BillEntity.resumo.ilike(like),
                )
            )

        rows = statement.all()

        if author:
            normalized_author = author.strip().lower()
            rows = [row for row in rows if any(name.lower() == normalized_author for name in self._bill_authors(row))]
        if party:
            normalized_party = party.strip().lower()
            rows = [row for row in rows if any(value.lower() == normalized_party for value in self._bill_parties(row))]

        def bill_chronological_key(row: BillEntity) -> tuple[str, int, int]:
            primary_date = row.data_apresentacao or row.data_ultima_acao or f"{row.ano:04d}-01-01"
            return (primary_date, row.ano, row.numero)

        if sort_by == 'relevance':
            rows = sorted(rows, key=lambda row: (self._bill_relevance_score(row), row.ano, row.numero), reverse=True)
        elif sort_by == 'oldest':
            rows = sorted(rows, key=bill_chronological_key)
        else:
            rows = sorted(rows, key=bill_chronological_key, reverse=True)

        total_count = len(rows)
        current_page = max(page, 1)
        current_page_size = max(page_size, 1)
        start = (current_page - 1) * current_page_size
        end = start + current_page_size
        paged_rows = rows[start:end]
        return [self._map_bill(row) for row in paged_rows], total_count

    def get_approved_bill_facets(self, db: Session) -> dict[str, list[str | int]]:
        statement = db.query(BillEntity).filter(BillEntity.aprovada.is_(True))
        if db.query(BillEntity).filter(BillEntity.fonte != 'seed').count() > 0:
            statement = statement.filter(BillEntity.fonte != 'seed')

        rows = statement.all()
        authors = sorted({author for row in rows for author in self._bill_authors(row) if author}, key=str.casefold)
        parties = sorted({party for row in rows for party in self._bill_parties(row) if party}, key=str.casefold)
        years = sorted({row.ano for row in rows}, reverse=True)
        return {
            'authors': authors,
            'parties': parties,
            'years': years,
        }

    def list_approved_bills(self, db: Session, query: str | None = None, year_from: int | None = None, year_to: int | None = None, sort_by: str | None = None) -> list[Bill]:
        statement = db.query(BillEntity).filter(BillEntity.aprovada.is_(True))
        if db.query(BillEntity).filter(BillEntity.fonte != 'seed').count() > 0:
            statement = statement.filter(BillEntity.fonte != 'seed')
        if year_from is not None:
            statement = statement.filter(BillEntity.ano >= year_from)
        if year_to is not None:
            statement = statement.filter(BillEntity.ano <= year_to)
        if query:
            like = f"%{query}%"
            statement = statement.filter(
                or_(
                    BillEntity.ementa.ilike(like),
                    BillEntity.resumo.ilike(like),
                    BillEntity.autor_principal.ilike(like),
                    BillEntity.tema.ilike(like),
                    BillEntity.sigla.ilike(like),
                )
            )
        rows = statement.all()

        def bill_chronological_key(row: BillEntity) -> tuple[str, int, int]:
            primary_date = row.data_apresentacao or row.data_ultima_acao or f"{row.ano:04d}-01-01"
            return (primary_date, row.ano, row.numero)

        if sort_by == 'relevance':
            rows = sorted(rows, key=lambda row: (self._bill_relevance_score(row), row.ano, row.numero), reverse=True)
        elif sort_by == 'oldest':
            rows = sorted(rows, key=bill_chronological_key)
        else:
            rows = sorted(rows, key=bill_chronological_key, reverse=True)
        return [self._map_bill(row) for row in rows]

    def get_politician_history(self, db: Session, politician_id: int) -> PoliticianHistory | None:
        politician_row = db.get(PoliticianEntity, politician_id)
        if politician_row is None:
            return None

        politician = self.get_politician(db, politician_id)
        if politician is None:
            return None

        vote_statement = db.query(VoteEventEntity).filter(VoteEventEntity.politician_id == politician_id)
        if db.query(VoteEventEntity).filter(VoteEventEntity.fonte != 'seed').count() > 0:
            vote_statement = vote_statement.filter(VoteEventEntity.fonte != 'seed')
        vote_rows = vote_statement.order_by(VoteEventEntity.data.desc()).all()
        if not vote_rows:
            fallback_vote_rows: list[VoteEventEntity] = []
            vote_bill_candidates = db.query(BillEntity).order_by(BillEntity.ano.desc(), BillEntity.numero.desc()).all()
            for bill_row in vote_bill_candidates:
                if not bill_row.votacoes:
                    continue
                for session in bill_row.votacoes:
                    if not isinstance(session, dict):
                        continue
                    for vote in session.get('votos', []):
                        if not isinstance(vote, dict):
                            continue
                        if vote.get('politician_id') != politician_id:
                            continue
                        fallback_vote_rows.append(
                            VoteEventEntity(
                                politician_id=politician_id,
                                politician_name=vote.get('politician_name') or politician.nome,
                                bill_id=bill_row.id,
                                bill_label=f"{bill_row.sigla} {bill_row.numero}/{bill_row.ano}",
                                votacao_id=str(session.get('id') or ''),
                                data=session.get('data'),
                                orgao=session.get('orgao') or 'Órgão não informado',
                                resultado=str(session.get('resultado')) if session.get('resultado') is not None else None,
                                voto=vote.get('voto') or 'Não informado',
                                partido=vote.get('partido'),
                                uf=vote.get('uf'),
                                fonte='bill_embedded',
                            )
                        )
            vote_rows = sorted(fallback_vote_rows, key=lambda row: row.data or '', reverse=True)
        bill_ids = {row.bill_id for row in vote_rows if row.bill_id is not None}
        bills_by_id: dict[int, BillEntity] = {}
        if bill_ids:
            bills_by_id = {
                row.id: row
                for row in db.query(BillEntity).filter(BillEntity.id.in_(bill_ids)).all()
            }
        approved_bill_rows = []

        politician_names = {
            value.strip().lower()
            for value in [politician.nome, politician_row.nome]
            if isinstance(value, str) and value.strip()
        }

        def is_vote_in_favor(vote_value: str | None) -> bool:
            if not isinstance(vote_value, str):
                return False
            normalized_vote = vote_value.strip().lower()
            return normalized_vote in {'sim', 'favorável', 'favoravel'}

        def is_vote_against(vote_value: str | None) -> bool:
            if not isinstance(vote_value, str):
                return False
            normalized_vote = vote_value.strip().lower()
            return normalized_vote in {'não', 'nao', 'contra'}

        def is_authored_by_politician(row: BillEntity) -> bool:
            if row.autor_principal and row.autor_principal.strip().lower() in politician_names:
                return True
            origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
            autores = origem_dados.get('autores') if isinstance(origem_dados.get('autores'), list) else []
            for autor in autores:
                if not isinstance(autor, dict):
                    continue
                author_id = autor.get('idAutor') or autor.get('autor_id') or autor.get('idDeputado') or autor.get('deputado_id')
                if str(author_id).isdigit() and int(author_id) == politician_id:
                    return True
                author_name = autor.get('nomeAutor') or autor.get('nome') or autor.get('nomeParlamentar')
                if isinstance(author_name, str) and author_name.strip().lower() in politician_names:
                    return True
            return False

        vote_rows_by_bill_id: dict[int, list[VoteEventEntity]] = {}
        for vote_row in vote_rows:
            if vote_row.bill_id is None:
                continue
            vote_rows_by_bill_id.setdefault(vote_row.bill_id, []).append(vote_row)

        approved_candidates = db.query(BillEntity).order_by(BillEntity.ano.desc(), BillEntity.numero.desc()).all()
        related_bill_map: dict[int, tuple[BillEntity, list[str]]] = {}
        for row in approved_candidates:
            relation_types: list[str] = []
            related_vote_rows = vote_rows_by_bill_id.get(row.id, [])
            if row.aprovada and related_vote_rows:
                relation_types.append('approved_enacted')
            if any(is_vote_in_favor(vote_row.voto) for vote_row in related_vote_rows):
                relation_types.append('approved_by_politician')
            if any(is_vote_against(vote_row.voto) for vote_row in related_vote_rows):
                relation_types.append('rejected_by_politician')
            if is_authored_by_politician(row):
                relation_types.append('authored')
            if relation_types:
                related_bill_map[row.id] = (row, relation_types)
        approved_bill_rows = [item[0] for item in related_bill_map.values()]

        return PoliticianHistory(
            politician=politician,
            timeline=self._build_politician_timeline(politician_row),
            voting_history=[
                PoliticianVoteHistory(
                    bill_id=row.bill_id,
                    bill_label=row.bill_label,
                    bill_text=bills_by_id[row.bill_id].ementa if row.bill_id in bills_by_id else None,
                    votacao_id=row.votacao_id,
                    data=row.data,
                    orgao=row.orgao,
                    resultado=row.resultado,
                    voto=row.voto,
                    fonte=row.fonte,
                )
                for row in vote_rows
            ],
            approved_bills_related=[self._map_bill(row, relation_types=related_bill_map[row.id][1]) for row in approved_bill_rows],
        )

    def get_bill(self, db: Session, bill_id: int) -> Bill | None:
        row = db.get(BillEntity, bill_id)
        if row is None:
            return None
        votes_by_politician_id: dict[int, PoliticianEntity] = {}
        if row.votacoes:
            politician_ids = {
                vote.get('politician_id')
                for session in row.votacoes
                for vote in session.get('votos', [])
                if isinstance(vote, dict) and vote.get('politician_id') is not None
            }
            if politician_ids:
                votes_by_politician_id = {
                    politician.id: politician
                    for politician in db.query(PoliticianEntity).filter(PoliticianEntity.id.in_(politician_ids)).all()
                }
        return self._map_bill(row, votes_by_politician_id, db)

    def _map_bill(self, row: BillEntity, votes_by_politician_id: dict[int, PoliticianEntity] | None = None, db: Session | None = None, relation_types: list[str] | None = None) -> Bill:
        origem_dados = row.origem_dados if isinstance(row.origem_dados, dict) else {}
        raw_tramitacoes = origem_dados.get('tramitacoes') if isinstance(origem_dados.get('tramitacoes'), list) else []
        reversed_tramitacoes = list(reversed(raw_tramitacoes))
        relator_ids = set()
        for item in reversed_tramitacoes:
            if not isinstance(item, dict):
                continue
            uri_ultimo_relator = item.get('uriUltimoRelator')
            if not isinstance(uri_ultimo_relator, str) or '/' not in uri_ultimo_relator:
                continue
            maybe_id = uri_ultimo_relator.rstrip('/').split('/')[-1]
            if maybe_id.isdigit():
                relator_ids.add(int(maybe_id))

        relators_by_id: dict[int, PoliticianEntity] = {}
        if db is not None and relator_ids:
            relators_by_id = {
                politician.id: politician
                for politician in db.query(PoliticianEntity).filter(PoliticianEntity.id.in_(relator_ids)).all()
            }

        normalized_timeline = []
        for index, stage in enumerate(row.timeline):
            if not isinstance(stage, dict):
                continue
            relator_id = stage.get('relator_id')
            relator_name = stage.get('relator_name')
            if index < len(reversed_tramitacoes):
                tramitacao = reversed_tramitacoes[index]
                if isinstance(tramitacao, dict):
                    uri_ultimo_relator = tramitacao.get('uriUltimoRelator')
                    if isinstance(uri_ultimo_relator, str) and '/' in uri_ultimo_relator:
                        maybe_id = uri_ultimo_relator.rstrip('/').split('/')[-1]
                        if maybe_id.isdigit():
                            relator_id = int(maybe_id)
                            if relator_id in relators_by_id:
                                relator_name = relators_by_id[relator_id].nome
            normalized_timeline.append({**stage, 'relator_id': relator_id, 'relator_name': relator_name})

        normalized_votacoes = []
        for vote_session in row.votacoes:
            votos_normalizados = []
            for vote in vote_session.get('votos', []):
                if not isinstance(vote, dict):
                    continue
                politician = None
                politician_id = vote.get('politician_id')
                if votes_by_politician_id and politician_id in votes_by_politician_id:
                    politician = votes_by_politician_id[politician_id]
                votos_normalizados.append(
                    {
                        **vote,
                        'partido': vote.get('partido') or (politician.partido if politician else None),
                        'uf': vote.get('uf') or (politician.uf if politician else None),
                        'cidade': vote.get('cidade') or (politician.cidade if politician else None),
                    }
                )
            normalized_votacoes.append({**vote_session, 'votos': votos_normalizados})

        return Bill(
            id=row.id,
            sigla=row.sigla,
            numero=row.numero,
            ano=row.ano,
            ementa=row.ementa,
            resumo=row.resumo,
            autor_principal=row.autor_principal,
            casa_origem=row.casa_origem,
            status_atual=row.status_atual,
            tema=row.tema,
            impacto_financeiro=row.impacto_financeiro,
            precisa_plenario=row.precisa_plenario,
            aprovada=row.aprovada,
            data_apresentacao=row.data_apresentacao,
            data_ultima_acao=row.data_ultima_acao,
            timeline=[BillStage(**stage) for stage in normalized_timeline],
            votacoes=[VoteSession(**vote) for vote in normalized_votacoes],
            fonte=row.fonte,
            origem_externa_id=row.origem_externa_id,
            origem_dados=row.origem_dados,
            related_to_politician_as=relation_types or [],
            ultima_sincronizacao=row.ultima_sincronizacao.isoformat() + 'Z' if row.ultima_sincronizacao else None,
        )


legislative_repository = LegislativeRepository()
