import json
import os
import re
import unicodedata
from pathlib import Path

class AnalyzeDevis:
    def __init__(self, config_path: str | Path = "analyse/devis.json"):
        """Initialise l'analyseur de Devis avec son fichier de configuration."""
        self.config_path = Path(config_path)
        
        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE)
        self.PHONE_RE = re.compile(r"(?:\+?\d[\d .()/:-]{7,}\d)")
        self.DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")
        self.AMOUNT_RE = re.compile(r"\d[\d ]*(?:[.,]\d{2,3})?\s*[€C∈]")
        self.POSTAL_CITY_RE = re.compile(r"\b\d{5}\s*[A-Za-zÀ-ÿ-]")
        self.UK_POSTCODE_RE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.IGNORECASE)
        self.STREET_HINT_RE = re.compile(
            r"\b(rue|street|st\.|avenue|av\.|boulevard|bd\.|road|rd\.|quai|place|route|impasse|chemin)\b",
            re.IGNORECASE,
        )
        self.DOC_TYPE_RE = re.compile(r"\b(Devis|Facture|Avoir)\b", re.IGNORECASE)
        self.TABLE_START_RE = re.compile(
            r"(?:^Description$|^Descriptif$|^Designation$|^ID$|DESCRIPTION DU SERVICE|Prixunitaire|Tarif/jour|Tarif jour)",
            re.IGNORECASE,
        )
        self.TABLE_HEADER_TOKEN_RE = re.compile(
            r"^(Description|Descriptif|Designation|ID|Quantit[eé]?|Quantite|Unité|Unit[eé]|Prix unitaire(?: HT)?|Prixunitaire|% TVA|Total TVA|Total TTC|Total HT|Nb\.?jours|Tarif/jour|Tarif jour|Montant|DESCRIPTION DU SERVICE|HEURES|PAR HEURE|TOTAL)$",
            re.IGNORECASE,
        )
        self.TOTAL_MARKER_RE = re.compile(r"^(?:Total\b|TOTAL\b|Sous total\b|SOUS TOTAL\b|TOTALHT:?$|TOTALTTC:?$|TOTALHORS\b)", re.IGNORECASE)

        self.ocr_model = None

    @staticmethod
    def normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        replacements = {
            "：": ":", "€ ": "€", "∈": "€", "C ": "€ ",
            "parvirementbancaire": "par virement bancaire",
            "Coordonneesbancaires": "Coordonnees bancaires",
            "Emispar": "Emis par",
            "A lattention de": "A l'attention de",
            "Date:": "Date : ",
            "Devis:": "Devis : ",
            "FACTURE:": "FACTURE : ",
            "TOTALTTC:": "TOTAL TTC : ",
            "TOTALHT:": "TOTAL HT : ",
            "Prixunitaire": "Prix unitaire",
            "TotalHT": "Total HT",
            "TOTALHORS": "TOTAL HORS",
            "TAUXTVA": "TAUX TVA",
            "MONTANTTVA": "MONTANT TVA",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def build_entry(description: str, regex: str, full_match: str | None, groups: dict[str, str]) -> dict:
        non_empty_groups = {key: value for key, value in groups.items() if value}
        return {
            "description": description,
            "regex": regex,
            "matched": bool(full_match or non_empty_groups),
            "full_match": full_match,
            "groups": non_empty_groups,
        }

    @staticmethod
    def find_token_index(tokens: list[str], pattern: str) -> int | None:
        regex = re.compile(pattern, re.IGNORECASE)
        for index, token in enumerate(tokens):
            if regex.search(token):
                return index
        return None

    @staticmethod
    def join_tokens(tokens: list[str]) -> str:
        return AnalyzeDevis.normalize_text(" ".join(token for token in tokens if AnalyzeDevis.normalize_text(token)))

    @staticmethod
    def sort_records(records: list[dict]) -> list[dict]:
        return sorted(records, key=lambda item: (item["y1"], item["x1"]))

    @staticmethod
    def tokens_from_records(records: list[dict]) -> list[str]:
        return [record["text"] for record in AnalyzeDevis.sort_records(records)]

    @staticmethod
    def slice_records_between(records: list[dict], start_y: float, end_y: float) -> list[dict]:
        return [record for record in records if record["y1"] >= start_y and record["y1"] < end_y]

    def is_email(self, token: str) -> bool: return bool(self.EMAIL_RE.search(token))
    def is_phone(self, token: str) -> bool: return bool(self.PHONE_RE.search(token))
    def is_date(self, token: str) -> bool: return bool(self.DATE_RE.search(token))
    def is_amount(self, token: str) -> bool: return bool(self.AMOUNT_RE.search(self.normalize_text(token)))
    
    def is_city_token(self, token: str) -> bool:
        normalized = self.normalize_text(token)
        return bool(self.POSTAL_CITY_RE.search(normalized) or self.UK_POSTCODE_RE.search(normalized))

    def looks_like_address(self, token: str) -> bool:
        normalized = self.normalize_text(token)
        if self.STREET_HINT_RE.search(normalized): return True
        return bool(re.match(r"^\d{1,4}\b", normalized))

    def clean_label(self, token: str) -> str:
        normalized = self.normalize_text(token)
        return re.sub(
            r"^(vendeur|client|destinataire|a l'attention de|a l attention de|adresse du client|emis par|fournisseur de services)\s*:?\s*",
            "", normalized, flags=re.IGNORECASE
        ).strip()

    def strip_leading_label(self, tokens: list[str]) -> list[str]:
        if not tokens: return tokens
        first = self.clean_label(tokens[0])
        if first != self.normalize_text(tokens[0]):
            tokens = tokens[:]
            if first: tokens[0] = first
            else: tokens = tokens[1:]
        return tokens

    def find_table_start_index(self, rec_texts: list[str]) -> int | None:
        for index, token in enumerate(rec_texts):
            if self.TABLE_START_RE.search(token): return index
        return None

    def find_total_start_index(self, rec_texts: list[str], start_index: int = 0) -> int | None:
        for index in range(start_index, len(rec_texts)):
            if self.TOTAL_MARKER_RE.search(rec_texts[index]): return index
        return None

    def find_table_content_start_index(self, rec_texts: list[str]) -> int | None:
        start_index = self.find_table_start_index(rec_texts)
        if start_index is None: return None

        index = start_index
        while index < len(rec_texts) and self.TABLE_HEADER_TOKEN_RE.search(rec_texts[index]):
            index += 1
        return index

    def parse_contact_segment(self, tokens: list[str]) -> dict[str, str]:
        tokens = [self.normalize_text(token) for token in tokens if self.normalize_text(token)]
        tokens = self.strip_leading_label(tokens)
        emails = [token for token in tokens if self.is_email(token)]
        phones = [token for token in tokens if self.is_phone(token)]
        cities = [token for token in tokens if self.is_city_token(token)]
        addresses = [token for token in tokens if self.looks_like_address(token)]

        name_candidates: list[str] = []
        for token in tokens:
            lower = token.lower()
            if (self.is_email(token) or self.is_phone(token) or self.is_city_token(token) or 
                self.looks_like_address(token) or self.is_date(token) or self.is_amount(token) or 
                "devis" in lower or "facture" in lower or "signature" in lower or "total" in lower or 
                "description" in lower or "conditions" in lower or "coordonnees bancaires" in lower):
                continue
            name_candidates.append(token)

        primary_name = name_candidates[0] if name_candidates else ""
        secondary_name = name_candidates[1] if len(name_candidates) > 1 else ""

        return {
            "name": primary_name,
            "secondary_name": secondary_name,
            "address": addresses[0] if addresses else "",
            "city": cities[0] if cities else "",
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "full": self.join_tokens(tokens),
        }

    def _extract_document_type(self, joined_text: str) -> dict:
        block_config = self.config["document_type"]
        match = self.DOC_TYPE_RE.search(joined_text)
        groups = {"1": match.group(1)} if match else {}
        return self.build_entry(block_config.get("description"), block_config["regex"], match.group(0) if match else None, groups)

    def _extract_vendor_and_client(self, rec_texts: list[str], records: list[dict]) -> tuple[dict, dict]:
        vendor_cfg = self.config["bloc_vendeur"]
        client_cfg = self.config["bloc_client"]

        vendor_entry = self.build_entry(vendor_cfg.get("description"), "heuristic_vendor_segment", None, {})
        client_entry = self.build_entry(client_cfg.get("description"), "heuristic_client_segment", None, {})

        table_start = self.find_table_start_index(rec_texts)
        if table_start is None: table_start = len(rec_texts)

        vendor_start = self.find_token_index(rec_texts, r"^(Vendeur|Emis par|FOURNISSEUR DE SERVICES|Entreprise .+)$")
        client_start = self.find_token_index(rec_texts, r"^(Client|Destinataire|A l'attention de|Adresse du Client)\b")

        vendor_tokens, client_tokens = [], []

        supplier_header = next((record for record in records if re.search(r"FOURNISSEUR DE SERVICES", record["text"], re.IGNORECASE)), None)
        client_header = next((record for record in records if re.search(r"^(CLIENT|Adresse du Client)$", record["text"], re.IGNORECASE)), None)
        
        if supplier_header and client_header:
            split_x = (supplier_header["x_center"] + client_header["x_center"]) / 2
            section_records = self.slice_records_between(records, min(supplier_header["y2"], client_header["y2"]), float("inf"))
            table_start_record = next((record for record in section_records if self.TABLE_START_RE.search(record["text"])), None)
            end_y = table_start_record["y1"] if table_start_record else float("inf")
            section_records = self.slice_records_between(section_records, min(supplier_header["y2"], client_header["y2"]), end_y)
            vendor_tokens = self.tokens_from_records([record for record in section_records if record["x_center"] < split_x])
            client_tokens = self.tokens_from_records([record for record in section_records if record["x_center"] >= split_x])

        elif vendor_start is not None and client_start is not None and vendor_start < client_start:
            vendor_tokens = rec_texts[vendor_start:client_start]
            client_tokens = rec_texts[client_start:table_start]
        elif client_start is not None:
            vendor_tokens = rec_texts[:client_start]
            client_tokens = rec_texts[client_start:table_start]
        elif vendor_start is not None:
            vendor_tokens = rec_texts[vendor_start:table_start]
        else:
            vendor_tokens = rec_texts[:table_start]

        vendor_info = self.parse_contact_segment(vendor_tokens)
        client_info = self.parse_contact_segment(client_tokens)

        if not vendor_info["name"]:
            footer_start = self.find_token_index(rec_texts, r"(Coordonnees|Informations de paiement|Pour l'entreprise|SARL|Siret)")
            footer_tokens = rec_texts[footer_start:] if footer_start is not None else []
            footer_info = self.parse_contact_segment(footer_tokens)
            for key in ("name", "address", "city", "email", "phone"):
                if not vendor_info[key]: vendor_info[key] = footer_info[key]

        if vendor_info["name"] or vendor_info["address"] or vendor_info["city"]:
            vendor_entry = self.build_entry(
                vendor_cfg.get("description"), "heuristic_vendor_segment", vendor_info["full"],
                {
                    "nom_entreprise": vendor_info["secondary_name"] or vendor_info["name"],
                    "adresse": vendor_info["address"],
                    "code_postal_ville": vendor_info["city"],
                },
            )

        if client_info["name"] or client_info["address"] or client_info["city"]:
            client_entry = self.build_entry(
                client_cfg.get("description"), "heuristic_client_segment", client_info["full"],
                {
                    "nom_client": client_info["name"],
                    "adresse_client": client_info["address"],
                    "code_postal_ville_client": client_info["city"],
                },
            )

        return vendor_entry, client_entry

    def _extract_infos_devis(self, rec_texts: list[str], joined_text: str) -> dict:
        block_config = self.config["bloc_infos_devis"]
        standard_match = re.search(block_config["regex"], joined_text, flags=re.IGNORECASE)
        if standard_match:
            return self.build_entry(
                block_config.get("description"), block_config["regex"], standard_match.group(0),
                {
                    "date_devis": standard_match.group(1),
                    "reference_devis": standard_match.group(2),
                    "date_validite": standard_match.group(3),
                },
            )

        date_devis, reference_devis, date_validite = "", "", ""

        for token in rec_texts:
            normalized = self.normalize_text(token)
            lower = normalized.lower()
            if not date_devis and "date" in lower:
                match = self.DATE_RE.search(normalized)
                if match: date_devis = match.group(0)
            if not reference_devis:
                if re.search(r"\b(devis|facture)\b", lower) and ("valable" not in lower) and (":" in normalized or "n°" in lower or "nº" in lower):
                    ref_match = re.search(r"(?:devis|facture)\s*:?\s*(?:n[°ºo]\s*)?([A-Z0-9'-]+)", normalized, flags=re.IGNORECASE)
                    if ref_match: reference_devis = ref_match.group(1)
                elif re.fullmatch(r"n[°º]\s*([A-Z0-9'-]+)", normalized, flags=re.IGNORECASE):
                    reference_devis = re.fullmatch(r"n[°º]\s*([A-Z0-9'-]+)", normalized, flags=re.IGNORECASE).group(1)
                elif "code client" in lower:
                    ref_match = re.search(r"code client\s*:?\s*([A-Z0-9-]+)", normalized, flags=re.IGNORECASE)
                    if ref_match: reference_devis = ref_match.group(1)
            if not date_validite and "valable" in lower:
                date_validite = normalized

        if not reference_devis:
            ref_match = re.search(r"DEVIS\s*:?\s*N?[°º]?\s*([A-Z0-9'-]+)", joined_text, flags=re.IGNORECASE)
            if ref_match: reference_devis = ref_match.group(1)

        full_match = self.join_tokens([value for value in (date_devis, reference_devis, date_validite) if value])
        return self.build_entry(
            block_config.get("description"), "heuristic_infos_devis", full_match or None,
            {
                "date_devis": date_devis,
                "reference_devis": reference_devis,
                "date_validite": date_validite,
            },
        )

    def _extract_informations_additionnelles(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_informations_additionnelles"]
        start_index = self.find_token_index(rec_texts, r"(Informations additionnelles|DEMANDES DU CLIENT)")
        table_start = self.find_table_start_index(rec_texts)
        if start_index is None or table_start is None or start_index >= table_start:
            return self.build_entry(block_config.get("description"), "heuristic_additional_info", None, {})

        segment = self.join_tokens(rec_texts[start_index + 1 : table_start])
        return self.build_entry(
            block_config.get("description"), "heuristic_additional_info", segment or None,
            {"texte_informations_additionnelles": segment},
        )

    def _extract_tableau_lignes(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_tableau_lignes"]
        start_index = self.find_table_content_start_index(rec_texts)
        if start_index is None:
            return self.build_entry(block_config.get("description"), "heuristic_table_lines", None, {})

        end_index = self.find_total_start_index(rec_texts, start_index)
        if end_index is None: end_index = len(rec_texts)

        line_tokens = rec_texts[start_index:end_index]
        segment = self.join_tokens(line_tokens)
        return self.build_entry(
            block_config.get("description"), "heuristic_table_lines", segment or None,
            {"contenu_lignes": segment},
        )

    def _extract_totaux(self, rec_texts: list[str], joined_text: str) -> dict:
        block_config = self.config["bloc_totaux"]
        total_ht, total_tva, total_ttc = "", "", ""

        def next_amount(index: int) -> str:
            for offset in range(1, 5):
                if index + offset < len(rec_texts):
                    candidate = self.normalize_text(rec_texts[index + offset]).replace("C", "€")
                    if self.is_amount(candidate): return candidate
            return ""

        def immediate_amount(index: int) -> str:
            if index + 1 < len(rec_texts):
                candidate = self.normalize_text(rec_texts[index + 1]).replace("C", "€")
                if self.is_amount(candidate): return candidate
            return ""

        for index, token in enumerate(rec_texts):
            normalized = self.normalize_text(token)
            lower = normalized.lower()
            if not total_ht and ("total ht" in lower or "total hors" in lower or "sous total" in lower):
                total_ht = next_amount(index)
            if not total_tva and ("montant tva" in lower or re.fullmatch(r"tva(?: \d+%)?", lower)):
                total_tva = next_amount(index)
            if not total_ttc and "total ttc" in lower:
                total_ttc = immediate_amount(index)
            if (not total_ttc and lower == "total" and index > 0 and index + 1 < len(rec_texts) and 
                self.is_amount(rec_texts[index + 1]) and not self.TABLE_HEADER_TOKEN_RE.search(rec_texts[index - 1])):
                total_ttc = immediate_amount(index)

        patterns = [
            (r"Total HT\s*:?\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_ht"),
            (r"TOTAL HORS TAXE\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_ht"),
            (r"Sous total\s*([0-9 ]+[.,][0-9]{0,3}\s*€?)", "total_ht"),
            (r"TVA(?:\s+\d+%)?\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_tva"),
            (r"MONTANT TVA\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_tva"),
            (r"Total TTC\s*:?\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_ttc"),
            (r"TOTAL TTC\s*:?\s*([0-9 ]+[.,][0-9]{2,3}\s*€?)", "total_ttc"),
            (r"Total\.\s*([0-9 ]+[.,][0-9]{0,3}\s*[€C])", "total_ttc"),
            (r"Total\s+([0-9 ]+[.,][0-9]{0,3}\s*€?)", "total_ttc"),
        ]

        for pattern, target in patterns:
            match = re.search(pattern, joined_text, flags=re.IGNORECASE)
            if match:
                if target == "total_ht" and not total_ht: total_ht = self.normalize_text(match.group(1)).replace("C", "€")
                if target == "total_tva" and not total_tva: total_tva = self.normalize_text(match.group(1)).replace("C", "€")
                if target == "total_ttc" and not total_ttc: total_ttc = self.normalize_text(match.group(1)).replace("C", "€")

        if total_ttc and not total_ht and not total_tva:
            total_ht = total_ttc

        full_match = self.join_tokens([value for value in (total_ht, total_tva, total_ttc) if value]) or None
        return self.build_entry(
            block_config.get("description"), "heuristic_totaux", full_match,
            {"total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc},
        )

    def _extract_signature(self, joined_text: str) -> dict:
        block_config = self.config["bloc_signature"]
        match = re.search(
            r"(Signature[^.:\"]*?(?:bon pour accord|Lu et approuv[ée]|mention[^.:\"]+)?(?:\"[^\"]+\")?)",
            joined_text, flags=re.IGNORECASE,
        )
        mention = match.group(1) if match else ""
        return self.build_entry(block_config.get("description"), "heuristic_signature", mention or None, {"mention_signature": mention})

    def _extract_coordonnees_fournisseur(self, rec_texts: list[str], joined_text: str) -> dict:
        block_config = self.config["bloc_coordonnees_fournisseur"]
        vendor_start = self.find_token_index(rec_texts, r"(Coordonnees|Informations de paiement|Merci pour votre confiance|Pour l'entreprise)")
        segment_tokens = rec_texts[vendor_start:] if vendor_start is not None else rec_texts
        info = self.parse_contact_segment(segment_tokens)
        website_match = re.search(r"\b(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", joined_text, flags=re.IGNORECASE)

        return self.build_entry(
            block_config.get("description"), "heuristic_supplier_coordinates", info["full"] or None,
            {
                "nom_contact": info["name"], "telephone": info["phone"], "email": info["email"],
                "site_web": website_match.group(0) if website_match else "",
            },
        )

    def _extract_bancaire(self, joined_text: str) -> dict:
        block_config = self.config["bloc_bancaire"]
        iban_match = re.search(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{2,4}){3,}\b", joined_text)
        bic_match = re.search(r"\b[A-Z0-9]{8,11}\b", joined_text)
        bank_match = re.search(r"Banque\s+([A-Za-z0-9 .'-]+)", joined_text, flags=re.IGNORECASE)
        account_match = re.search(r"Compte\s*:?\s*([A-Z0-9]{8,})", joined_text, flags=re.IGNORECASE)
        iban_or_account = iban_match.group(0) if iban_match else account_match.group(1) if account_match else ""

        full_match = self.join_tokens([value for value in (bank_match.group(1) if bank_match else "", iban_or_account, bic_match.group(0) if bic_match else "")])
        return self.build_entry(
            block_config.get("description"), "heuristic_bank_details", full_match or None,
            {
                "nom_banque": self.normalize_text(bank_match.group(1)) if bank_match else "",
                "iban": self.normalize_text(iban_or_account),
                "bic_swift": bic_match.group(0) if bic_match and iban_match else "",
            },
        )

    def _extract_identifiants_entreprise(self, joined_text: str) -> dict:
        block_config = self.config["bloc_identifiants_entreprise"]
        siret_match = re.search(r"Siret\s*:?\s*([0-9 ]{9,20})", joined_text, flags=re.IGNORECASE)
        tva_match = re.search(r"TVA(?:\s*Intra(?:com)?)?\s*:?\s*([A-Z]{2}[A-Z0-9]+)", joined_text, flags=re.IGNORECASE)
        full_match = self.join_tokens([value for value in (siret_match.group(0) if siret_match else "", tva_match.group(0) if tva_match else "")])
        return self.build_entry(
            block_config.get("description"), "heuristic_company_identifiers", full_match or None,
            {
                "siren_ou_siret": self.normalize_text(siret_match.group(1)) if siret_match else "",
                "tva_intra": tva_match.group(1) if tva_match else "",
            },
        )

    def analyze(self, image_path: str) -> dict:
        """Exécute l'OCR sur un devis et extrait tous les blocs configurés."""
        
        if self.ocr_model is None:
            from paddleocr import PaddleOCR
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
            os.environ["FLAGS_use_mkldnn"] = "0"
            self.ocr_model = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device="cpu",
                enable_mkldnn=False,
            )

        results = self.ocr_model.predict(input=str(image_path))
        
        rec_texts = []
        records = []
        for page in results:
            if not page: continue
            for item in page:
                box = item[0]
                text = item[1][0]
                normalized_text = self.normalize_text(text)
                
                if not normalized_text: continue
                
                rec_texts.append(normalized_text)
                records.append({
                    "text": normalized_text,
                    "x1": float(box[0][0]),
                    "y1": float(box[0][1]),
                    "x2": float(box[2][0]),
                    "y2": float(box[2][1]),
                    "x_center": (float(box[0][0]) + float(box[2][0])) / 2,
                })
                
        joined_text = self.join_tokens(rec_texts)

        vendor_entry, client_entry = self._extract_vendor_and_client(rec_texts, records)

        return {
            "document_type": self._extract_document_type(joined_text),
            "bloc_vendeur": vendor_entry,
            "bloc_client": client_entry,
            "bloc_infos_devis": self._extract_infos_devis(rec_texts, joined_text),
            "bloc_informations_additionnelles": self._extract_informations_additionnelles(rec_texts),
            "bloc_tableau_lignes": self._extract_tableau_lignes(rec_texts),
            "bloc_totaux": self._extract_totaux(rec_texts, joined_text),
            "bloc_signature": self._extract_signature(joined_text),
            "bloc_coordonnees_fournisseur": self._extract_coordonnees_fournisseur(rec_texts, joined_text),
            "bloc_bancaire": self._extract_bancaire(joined_text),
            "bloc_identifiants_entreprise": self._extract_identifiants_entreprise(joined_text),
        }