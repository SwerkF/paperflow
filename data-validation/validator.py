from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from datetime import datetime

_REGEX_SIRET = re.compile(r"^\d{14}$")
_REGEX_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REGEX_DATE_FR = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$")
_REGEX_DIGITS = re.compile(r"\d+")
_REGEX_NUMBER = re.compile(r"^\d+(?:\.\d+)?$")


class ServiceValidation:
    def _add_anomalie(self, alertes, doc_id, message: str):
        """
        Ajouter une anomalie à la liste des alertes.
        """
        alertes.append({"doc_id": doc_id, "message": message})

    def _matches(self, valeur, regex: re.Pattern):
        """
        Vérifier si une valeur correspond à une regex.
        """
        if valeur is None:
            return False
        return bool(regex.match(str(valeur).strip()))

    def _check_luhn(self, numero: str) -> bool:
        """
        Validation Luhn (utilisée sur les SIRET).
        """
        if not numero or not numero.isdigit():
            return False

        total = 0
        for i, ch in enumerate(numero[::-1]):
            digit = int(ch)
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return total % 10 == 0

    def _normalize_company(self, nom: str | None) -> str | None:
        """
        Normalise un nom société pour comparaison (accents/majuscules ect).
        """
        if not nom or not str(nom).strip():
            return None

        s = str(nom).strip()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.upper()
        s = re.sub(r"[^A-Z0-9]+", " ", s)
        tokens = s.split()
        merged: list[str] = []
        buf = ""

        for t in tokens:
            if len(t) == 1 and t.isalpha():
                buf += t
                continue
            if buf:
                merged.append(buf)
                buf = ""
            merged.append(t)

        if buf:
            merged.append(buf)

        s = " ".join(merged)
        s = re.sub(r"\b(SASU|SAS|SARL|EURL|SA|SCI|SNC|SCS|SCOP|SCA|GIE)\b", " ", s)
        s = re.sub(r"\s+", " ", s).strip().replace(" ", "")
        return s or None

    def _same_company_name(self, a: str | None, b: str | None) -> bool:
        """
        Comparer les noms des entreprises
        """
        normalized_a = self._normalize_company(a)
        normalized_b = self._normalize_company(b)
        if not normalized_a or not normalized_b:
            return False

        return normalized_a == normalized_b

    def _normalize_text(self, value: str | None) -> str:
        """
        Normalisation pour matching de type de document.
        """
        if not value:
            return ""

        normalized_value = unicodedata.normalize("NFKD", str(value))
        normalized_value = "".join(ch for ch in normalized_value if not unicodedata.combining(ch))
        return normalized_value.lower()

    def _extract_digits(self, value) -> str | None:
        """
        Extrait uniquement les chiffres d'une valeur.
        On le fait par exemple pour le SIRET, on ne veut pas de lettres, de caractères spéciaux, etc.
        """
        if value is None:
            return None

        extracted_digits = "".join(_REGEX_DIGITS.findall(str(value)))
        return extracted_digits or None

    def _extract_siret(self, value) -> str | None:
        """
        Retourne un SIRET uniquement s'il a strictement 14 chiffres. Sinon ça créera une anomalie.
        """
        digits = self._extract_digits(value)
        if not digits or len(digits) != 14:
            return None

        return digits

    def _parse_date(self, value: str | None) -> str | None:
        """
        Convertit la première date trouvée vers le format YYYY-MM-DD.
        """
        if not value:
            return None

        raw = str(value).strip()
        if self._matches(raw, _REGEX_DATE_ISO):
            return raw

        match = _REGEX_DATE_FR.search(raw)
        if not match:
            return None

        day, month, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"

        try:
            dt = datetime(int(year), int(month), int(day))
        except ValueError:
            return None

        return dt.strftime("%Y-%m-%d")

    def _parse_amount(self, value):
        """
        Convertit un montant en float.
        """
        if isinstance(value, (int, float)):
            return float(value)

        if value is None:
            return None

        if not isinstance(value, str):
            return None

        s = value.replace("\u00a0", " ").replace("\u202f", " ").strip()
        s = re.sub(r"[€$]", "", s)
        s = s.replace(" ", "").replace(",", ".")

        if not self._matches(s, _REGEX_NUMBER):
            return None

        try:
            return float(s)
        except ValueError:
            return None

    def _to_tva_ratio(self, value):
        """
        Convertit une TVA brute vers ratio (20 -> 0.2).
        Ex: 20% -> 0.2
        """
        if isinstance(value, (int, float)):
            return value / 100 if value > 1 else float(value)

        if value is None:
            return None

        raw = str(value).replace("%", "").replace(",", ".").strip()
        if not raw:
            return None

        if not self._matches(raw, _REGEX_NUMBER):
            return None

        num = float(raw)
        return num / 100 if num > 1 else num

    def _block_groups(self, doc, block_name: str) -> dict:
        """
        Récupère doc[bloc].groups en toute sécurité.
        Ex:
        {
            "bloc": {
                "groups": {
                    "societe_client": "Acheteur SA"
                }
            }
        }
        Retourne:
        {
            "societe_client": "Acheteur SA"
        }
        """
        block = doc.get(block_name)
        if not isinstance(block, dict):
            return {}

        groups = block.get("groups")
        return groups if isinstance(groups, dict) else {}

    def _detect_doc_type(self, doc) -> str:
        """Détecte le type du document."""
        if not isinstance(doc, dict):
            return "inconnu"

        if doc.get("type"):
            return str(doc.get("type")).strip().lower()

        dt = doc.get("document_type")
        full = dt.get("full_match") if isinstance(dt, dict) else None
        groups = self._block_groups(doc, "document_type")
        label = " ".join(
            str(x) for x in (full, groups.get("1"), groups.get("type"), groups.get("document_type")) if x
        )
        normalized_label = self._normalize_text(label)

        if "attestation de fourniture des declarations sociales" in normalized_label:
            return "attestation_siret"
        elif re.search(r"\burssaf\b", normalized_label):
            return "urssaf"
        elif "facture" in normalized_label:
            return "facture"
        elif "devis" in normalized_label:
            return "devis"
        elif "kbis" in normalized_label or "immatriculation principale" in normalized_label:
            return "kbis"
        elif re.search(r"\brib\b", normalized_label) or "identite bancaire" in normalized_label:
            return "rib"
        else:
            return "inconnu"

    def _normalize_ocr_document(self, document, index: int):
        """
        Transformation du document de l'OCR vers une structure plus exploitable
        """
        doc_id = f"DOC-{index}"

        if not isinstance(document, dict):
            return {"id": doc_id, "type": "inconnu", "company": None, "client": None}

        normalized = {"id": document.get("id") or doc_id, "type": self._detect_doc_type(document), "company": None, "client": None}
        doc_type = normalized["type"]

        vendeur = self._block_groups(document, "bloc_vendeur")
        client = self._block_groups(document, "bloc_client")
        infos_facture = self._block_groups(document, "bloc_infos_facture")
        infos_devis = self._block_groups(document, "bloc_infos_devis")
        totaux_facture = self._block_groups(document, "bloc_totaux_tva")
        totaux_devis = self._block_groups(document, "bloc_totaux")
        sign = self._block_groups(document, "bloc_signature_coordonnees")
        id_entreprise = self._block_groups(document, "bloc_identifiants_entreprise")
        kbis = self._block_groups(document, "bloc_identification_personne_morale")
        rib_owner = self._block_groups(document, "bloc_titulaire_compte")
        urssaf_emetteur = self._block_groups(document, "bloc_emetteur")
        urssaf_dest = self._block_groups(document, "bloc_date_destinataire")

        if doc_type in ("facture", "devis"):
            company_name = sign.get("nom_societe") or vendeur.get("nom_vendeur") or vendeur.get("nom_entreprise")
            company_siret = self._extract_siret(sign.get("siret") or id_entreprise.get("siren_ou_siret"))
            client_name = client.get("societe_client") or client.get("nom_client")
            client_siret = self._extract_siret(client.get("siret_client") or client.get("siret"))

            normalized["company"] = {"nom": company_name, "siret": company_siret} if (company_name or company_siret) else None
            normalized["client"] = {"nom": client_name, "siret": client_siret} if (client_name or client_siret) else None

            if doc_type == "facture":
                normalized["date_facture"] = self._parse_date(infos_facture.get("date_facture"))
                normalized["montant_ht"] = totaux_facture.get("total_ht")
                normalized["montant_ttc"] = totaux_facture.get("total_ttc")
                montant_ht = self._parse_amount(normalized["montant_ht"])
                montant_ttc = self._parse_amount(normalized["montant_ttc"])
                tva = None
                if montant_ht and montant_ttc and montant_ht > 0:
                    tva = (montant_ttc - montant_ht) / montant_ht
                normalized["tva"] = tva
            else:
                normalized["date_facture"] = self._parse_date(infos_devis.get("date_devis"))
                normalized["montant_ht"] = totaux_devis.get("total_ht")
                normalized["montant_ttc"] = totaux_devis.get("total_ttc")
                total_tva = self._parse_amount(totaux_devis.get("total_tva"))
                montant_ht = self._parse_amount(normalized["montant_ht"])
                tva = (total_tva / montant_ht) if (total_tva is not None and montant_ht) else None
                normalized["tva"] = tva

        elif doc_type == "kbis":
            company_name = kbis.get("denomination")
            company_siret = self._extract_siret(kbis.get("immatriculation_rcs"))
            normalized["company"] = {"nom": company_name, "siret": company_siret} if (company_name or company_siret) else None

        elif doc_type == "rib":
            company_name = rib_owner.get("nom_titulaire")
            normalized["company"] = {"nom": company_name, "siret": None} if company_name else None

        elif doc_type in ("urssaf", "attestation_siret"):
            company_name = urssaf_dest.get("raison_sociale")
            company_siret = self._extract_siret(urssaf_emetteur.get("siret_urssaf"))
            normalized["company"] = {"nom": company_name, "siret": company_siret} if (company_name or company_siret) else None
            normalized["date_expiration"] = self._parse_date(urssaf_dest.get("date_document"))

        return normalized

    def _check_entity(
        self,
        entity_data,
        doc_id,
        role,
        entites_connues: dict,
        clients_connus: dict,
        ignore_sirets: set[str] | None = None,
    ):
        """
        Valider le SIRET et nom des entités.
        On utilise un "cache" pour avoir des références sur les entités connues.
        """
        alertes = []
        if not isinstance(entity_data, dict):
            return alertes

        siret = self._extract_siret(entity_data.get("siret"))
        nom = entity_data.get("nom")

        if not siret:
            return alertes
        if not self._check_luhn(siret):
            self._add_anomalie(alertes, doc_id, f"SIRET invalide pour {role} : '{siret}'.")
            return alertes

        cache = clients_connus if role == "Client" else entites_connues
        ignore = ignore_sirets or set()

        if siret in cache:
            ref_nom = cache[siret].get("nom")
            if nom and ref_nom and nom != ref_nom:
                if siret not in ignore or not self._same_company_name(nom, ref_nom):
                    self._add_anomalie(
                        alertes,
                        doc_id,
                        f"Incohérence d'identité ({role}) : le nom '{nom}' ne correspond pas au SIRET {siret} (attendu: '{ref_nom}').",
                    )
        else:
            entity = deepcopy(entity_data)
            entity["siret"] = siret
            cache[siret] = entity

        return alertes

    def _get_company_or_client(self, doc):
        """
        Choisit l'entité de périmètre: entreprise sinon client pour le document.
        """
        if isinstance(doc.get("company"), dict):
            return doc.get("company"), "company"
        if doc.get("type") in ("facture", "devis") and isinstance(doc.get("client"), dict):
            return doc.get("client"), "client"
        return None, None

    def _validate_context(self, contexte_utilisateur, alertes_globales):
        """
        Valide le contexte utilisateur avant traitement du lot.
        """
        doc_id = "BATCH"
        if not isinstance(contexte_utilisateur, dict):
            self._add_anomalie(alertes_globales, doc_id, "contexte_utilisateur invalide (objet attendu).")
            return None

        siret_principal = self._extract_digits(contexte_utilisateur.get("siret_principal"))
        if not siret_principal:
            self._add_anomalie(alertes_globales, doc_id, "contexte_utilisateur.siret_principal manquant.")
            return None
        if not self._matches(siret_principal, _REGEX_SIRET):
            self._add_anomalie(
                alertes_globales,
                doc_id,
                f"contexte_utilisateur.siret_principal invalide : '{siret_principal}' (14 chiffres attendus).",
            )
            return None
        if not self._check_luhn(siret_principal):
            self._add_anomalie(alertes_globales, doc_id, f"contexte_utilisateur.siret_principal invalide : '{siret_principal}'.")
            return None

        nom_principal = contexte_utilisateur.get("nom_principal")
        if nom_principal is not None and not str(nom_principal).strip():
            self._add_anomalie(alertes_globales, doc_id, "contexte_utilisateur.nom_principal est vide.")
            nom_principal = None
        if nom_principal is not None:
            nom_principal = str(nom_principal).strip()

        return {"siret_principal": siret_principal, "nom_principal": nom_principal}

    def _check_urssaf_dates(self, doc, doc_id, alertes_globales):
        """
        Valide la date d'expiration de l'attestation URSSAF.
        """
        if doc.get("type") not in ("urssaf", "attestation_siret"):
            return
        date_exp_raw = doc.get("date_expiration")
        if not date_exp_raw:
            return
        if not self._matches(date_exp_raw, _REGEX_DATE_ISO):
            self._add_anomalie(
                alertes_globales,
                doc_id,
                f"Format de date invalide pour date_expiration : '{date_exp_raw}' (YYYY-MM-DD attendu).",
            )
            return
        try:
            date_exp = datetime.strptime(date_exp_raw, "%Y-%m-%d")
        except ValueError:
            self._add_anomalie(alertes_globales, doc_id, f"Date invalide pour date_expiration : '{date_exp_raw}'.")
            return
        if date_exp < datetime.now():
            self._add_anomalie(alertes_globales, doc_id, f"L'attestation est expirée depuis le {date_exp_raw}.")

    def _check_invoice_math(self, doc, doc_id, alertes_globales):
        """
        Valide les montants sur la facture ou le devis 
        """
        if doc.get("type") not in ("facture", "devis"):
            return

        for champ in ("montant_ht", "montant_ttc"):
            raw = doc.get(champ)
            if raw in (None, ""):
                continue
            if self._parse_amount(raw) is None:
                self._add_anomalie(
                    alertes_globales,
                    doc_id,
                    f"Format invalide pour {champ} : '{raw}' (ex: 1234.56 ou 1234,56).",
                )

        ht = self._parse_amount(doc.get("montant_ht"))
        ttc = self._parse_amount(doc.get("montant_ttc"))
        tva = self._to_tva_ratio(doc.get("tva"))
        # Vérifie que les montants sont valides et que le calcul est correct
        if isinstance(ht, float) and isinstance(ttc, float) and isinstance(tva, float):
            calcul = ht * (1 + tva)
            if abs(calcul - ttc) > 0.05:
                self._add_anomalie(
                    alertes_globales,
                    doc_id,
                    f"Calcul faux : HT({ht}) + TVA({tva*100}%) = {calcul}, mais l'OCR a lu TTC({ttc}).",
                )

    def validate_documents(self, contexte_utilisateur, nouveaux_documents):
        """
        Fonction principale
        """
        alertes_globales = []
        entites_connues: dict = {}
        clients_connus: dict = {}
        context = self._validate_context(contexte_utilisateur, alertes_globales)
        if not context:
            return alertes_globales

        siret_principal = context["siret_principal"]
        if context.get("nom_principal"):
            entites_connues.setdefault(
                siret_principal, {"siret": siret_principal, "nom": context["nom_principal"]}
            )

        for index, document in enumerate(nouveaux_documents, start=1):
            doc = self._normalize_ocr_document(document, index)
            doc_id = doc.get("id", f"DOC-{index}")
            entity, type_entity = self._get_company_or_client(doc)
            siret = self._extract_siret(entity.get("siret")) if isinstance(entity, dict) else None

            if not entity:
                self._add_anomalie(
                    alertes_globales,
                    doc_id,
                    "Entité introuvable (attendu: 'company', ou 'client' pour une facture/devis).",
                )
            elif not siret:
                self._add_anomalie(
                    alertes_globales,
                    doc_id,
                    f"SIRET manquant ou invalide (14 chiffres attendus) pour l'entité ({type_entity}).",
                )
            elif siret and siret != siret_principal:
                self._add_anomalie(
                    alertes_globales,
                    doc_id,
                    f"Document invalide: SIRET {siret} n'est pas égal au SIRET principal {siret_principal}.",
                )

            if doc.get("type") in ("facture", "devis"):
                company = doc.get("company") if isinstance(doc.get("company"), dict) else entity
                alertes_globales.extend(
                    self._check_entity(
                        company,
                        doc_id,
                        "Entreprise",
                        entites_connues,
                        clients_connus
                    )
                )
                alertes_globales.extend(
                    self._check_entity(
                        doc.get("client"),
                        doc_id,
                        "Client",
                        entites_connues,
                        clients_connus,
                    )
                )
            else:
                alertes_globales.extend(
                    self._check_entity(
                        doc.get("company"),
                        doc_id,
                        "Entreprise",
                        entites_connues,
                        clients_connus
                    )
                )

            self._check_urssaf_dates(doc, doc_id, alertes_globales)
            self._check_invoice_math(doc, doc_id, alertes_globales)

        return alertes_globales
