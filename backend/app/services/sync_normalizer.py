import re


class SyncNormalizerService:
    RELEVANT_SIGLAS = {
        "PL",
        "PLP",
        "PEC",
        "MPV",
        "PLC",
        "PDC",
        "PDL",
        "PLV",
        "REQ",
        "MSC",
    }

    @staticmethod
    def normalize_tramitacoes(tramitacoes: list[dict]) -> list[dict]:
        if not tramitacoes:
            return [
                {
                    "ordem": 1,
                    "fase": "Apresentação",
                    "orgao": "Câmara dos Deputados",
                    "descricao": "Proposição importada sem tramitações detalhadas disponíveis no momento.",
                    "status": "current",
                }
            ]

        ordered = list(reversed(tramitacoes))
        timeline = []
        for index, item in enumerate(ordered, start=1):
            orgao = item.get("siglaOrgao") or item.get("descricaoOrgao") or "Órgão não informado"
            descricao = item.get("descricaoTramitacao") or item.get("despacho") or item.get("descricaoSituacao") or "Atualização legislativa importada."
            fase = item.get("descricaoSituacao") or item.get("descricaoTramitacao") or "Tramitação"
            status = "current" if index == len(ordered) else "completed"
            timeline.append(
                {
                    "ordem": index,
                    "fase": fase,
                    "orgao": orgao,
                    "descricao": descricao,
                    "status": status,
                }
            )
        return timeline

    @staticmethod
    def normalize_presidential_stage(status_proposicao: dict) -> dict | None:
        text = " ".join(
            filter(
                None,
                [
                    status_proposicao.get("descricaoSituacao"),
                    status_proposicao.get("descricaoTramitacao"),
                ],
            )
        ).lower()
        data = status_proposicao.get("dataHora") or status_proposicao.get("data")
        if "veto rejeitado" in text or "rejeição de veto" in text or "veto derrubado" in text or "veto rejeitado pelo congresso" in text:
            return {
                "fase": "Rejeição de veto",
                "orgao": "Congresso Nacional",
                "descricao": "O Congresso Nacional rejeitou o veto presidencial.",
                "data": data,
                "status": "current",
            }
        if "veto parcial" in text:
            return {
                "fase": "Transformado em Norma Jurídica com Veto Parcial",
                "orgao": "Presidência da República",
                "descricao": "A proposição foi sancionada com veto parcial da Presidência da República.",
                "data": data,
                "status": "current",
            }
        if "veto" in text:
            return {
                "fase": "Veto presidencial",
                "orgao": "Presidência da República",
                "descricao": "A Presidência da República vetou a proposição.",
                "data": data,
                "status": "current",
            }
        if "sancion" in text:
            return {
                "fase": "Sanção presidencial",
                "orgao": "Presidência da República",
                "descricao": "A Presidência da República sancionou a proposição.",
                "data": data,
                "status": "current",
            }
        if "promulg" in text:
            return {
                "fase": "Promulgação",
                "orgao": "Presidência da República",
                "descricao": "A proposição foi promulgada.",
                "data": data,
                "status": "current",
            }
        return None

    def build_timeline(self, tramitacoes: list[dict], status_proposicao: dict) -> list[dict]:
        timeline = self.normalize_tramitacoes(tramitacoes)
        presidential_stage = self.normalize_presidential_stage(status_proposicao)
        if presidential_stage is None:
            return timeline
        for item in timeline:
            item["status"] = "completed"
        timeline.append(
            {
                "ordem": len(timeline) + 1,
                **presidential_stage,
            }
        )
        return timeline

    @staticmethod
    def is_bill_approved(status_proposicao: dict) -> bool:
        text = " ".join(
            filter(
                None,
                [
                    status_proposicao.get("descricaoSituacao"),
                    status_proposicao.get("descricaoTramitacao"),
                ],
            )
        ).lower()
        approved_terms = ["transformado em norma", "aprovado", "sancionada", "sancionado", "promulgada", "promulgado"]
        return any(term in text for term in approved_terms)

    @staticmethod
    def extract_voting_sessions(votacoes: list[dict]) -> list[dict]:
        normalized = []
        for item in votacoes:
            resultado = item.get("resultado")
            if resultado in (None, ""):
                resultado = item.get("aprovacao")
            quorum = item.get("quorum")
            normalized.append(
                {
                    "id": str(item.get("id") or ""),
                    "titulo": item.get("descricao") or item.get("apreciacao") or "Votação importada",
                    "orgao": item.get("siglaOrgao") or item.get("descricaoOrgao") or "Órgão não informado",
                    "data": item.get("data") or item.get("dataHoraRegistro") or "",
                    "resultado": str(resultado) if resultado not in (None, "") else "Resultado não informado",
                    "quorum": str(quorum) if quorum not in (None, "") else "Não informado",
                    "votos": [],
                }
            )
        return normalized

    @staticmethod
    def normalize_vote_records(votos: list[dict]) -> list[dict]:
        normalized = []
        for item in votos:
            deputado = item.get("deputado_") or {}
            normalized.append(
                {
                    "politician_id": deputado.get("id"),
                    "politician_name": deputado.get("nome") or "Parlamentar não informado",
                    "voto": item.get("tipoVoto") or "Não informado",
                    "partido": deputado.get("siglaPartido"),
                    "uf": deputado.get("siglaUf"),
                }
            )
        return normalized

    def is_historically_relevant_proposition(self, proposicao: dict) -> bool:
        sigla = str(proposicao.get("siglaTipo") or proposicao.get("sigla") or "").strip().upper()
        if sigla in self.RELEVANT_SIGLAS:
            return True

        keywords = " ".join(
            str(value or "")
            for value in [
                proposicao.get("descricaoTipo"),
                proposicao.get("ementa"),
                proposicao.get("descricao"),
            ]
        ).lower()
        return any(
            term in keywords
            for term in [
                "lei",
                "emenda à constituição",
                "decreto legislativo",
                "medida provisória",
                "norma jurídica",
            ]
        )

    @staticmethod
    def build_authorship_summary(autores: list[dict], detalhe: dict, proposicao_resumo: dict) -> str:
        if autores:
            principal = next((item for item in autores if item.get("ordemAssinatura") in [1, "1"]), autores[0])
            nome = principal.get("nome") or principal.get("nomeAutor") or principal.get("descricaoTipo") or "Autoria não informada"
            sigla_partido = principal.get("siglaPartido") or principal.get("partido")
            sigla_uf = principal.get("siglaUf") or principal.get("uf")
            complemento = "/".join(part for part in [sigla_partido, sigla_uf] if part)
            return f"{nome} ({complemento})" if complemento else str(nome)

        status_proposicao = detalhe.get("statusProposicao") or {}
        despacho = str(status_proposicao.get("despacho") or "")
        match = re.search(r"pela?\s+(?:Deputad[oa]|Senador(?:a)?)\s+([^()]+?)\s*\(([^)]+)\)", despacho, flags=re.IGNORECASE)
        if match:
            nome = match.group(1).strip(" .,-")
            complemento = match.group(2).split(" -", 1)[0].strip()
            return f"{nome} ({complemento})" if complemento else nome

        descricao_tipo_autor = detalhe.get("descricaoTipoAutor")
        if descricao_tipo_autor:
            return str(descricao_tipo_autor)

        resumo_autor = proposicao_resumo.get("autor")
        if resumo_autor:
            return str(resumo_autor)

        return "Autoria a detalhar"

    @staticmethod
    def build_theme_summary(temas: list[dict]) -> str:
        nomes = []
        for item in temas:
            nome = item.get("tema") or item.get("descricaoTema") or item.get("siglaTema") or item.get("nome")
            if nome and nome not in nomes:
                nomes.append(str(nome))
        if not nomes:
            return "Legislativo federal"
        return ", ".join(nomes[:3])

    @staticmethod
    def infer_requires_plenary(sigla: str, status_proposicao: dict, votacoes: list[dict]) -> bool:
        sigla_upper = str(sigla or "").upper()
        if sigla_upper in {"PEC", "PLP", "MPV", "PLV"}:
            return True
        texto = " ".join(
            filter(
                None,
                [
                    status_proposicao.get("descricaoSituacao"),
                    status_proposicao.get("descricaoTramitacao"),
                ],
            )
        ).lower()
        return "plenário" in texto or any((item.get("siglaOrgao") or "").upper() == "PLEN" for item in votacoes)

    def calculate_legislative_relevance_score(
        self,
        proposicao_resumo: dict,
        detalhe: dict | None = None,
        status_proposicao: dict | None = None,
        votacoes: list[dict] | None = None,
        autores: list[dict] | None = None,
    ) -> int:
        sigla = str((detalhe or {}).get("siglaTipo") or proposicao_resumo.get("siglaTipo") or proposicao_resumo.get("sigla") or "").strip().upper()
        score = 0

        score_by_sigla = {
            "PEC": 100,
            "MPV": 95,
            "PLP": 90,
            "PLV": 85,
            "PL": 80,
            "PLC": 75,
            "PDC": 65,
            "PDL": 65,
            "MSC": 40,
            "REQ": 20,
        }
        score += score_by_sigla.get(sigla, 10)

        if status_proposicao and self.is_bill_approved(status_proposicao):
            score += 40

        if status_proposicao and self.infer_requires_plenary(sigla, status_proposicao, votacoes or []):
            score += 20

        text = " ".join(
            str(value or "")
            for value in [
                proposicao_resumo.get("ementa"),
                proposicao_resumo.get("descricaoTipo"),
                (detalhe or {}).get("ementa"),
            ]
        ).lower()
        for term, weight in [
            ("constituição", 20),
            ("tribut", 15),
            ("orçament", 15),
            ("eleitoral", 12),
            ("penal", 12),
            ("saúde", 10),
            ("educação", 10),
            ("segurança", 10),
        ]:
            if term in text:
                score += weight

        if votacoes:
            score += min(len(votacoes) * 3, 15)

        if autores and len(autores) > 1:
            score += min(len(autores), 10)

        return score

    @staticmethod
    def extract_presentation_month(proposicao: dict) -> int:
        for key in ["dataApresentacao", "data"]:
            value = proposicao.get(key)
            if not value or not isinstance(value, str):
                continue
            parts = value.split("T")[0].split("-")
            if len(parts) >= 2 and parts[1].isdigit():
                month = int(parts[1])
                if 1 <= month <= 12:
                    return month
        return 0


sync_normalizer = SyncNormalizerService()
