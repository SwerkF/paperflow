import json
import os
import re
import unicodedata
from pathlib import Path
import tempfile

class AnalyzeFacture:
    def __init__(self, ocr_model, config_path: str | Path = "analyse/facture.json"):
        """Initialise l'analyseur de Facture avec son fichier de configuration."""
        self.config_path = Path(config_path)
        self.ocr_model = ocr_model

        # Chargement de la configuration
        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.CIVILITY_RE = re.compile(r"^(M(?:onsieur|me|adame)?|Mme|Madame|Mr)\b", re.IGNORECASE)
        self.LEGAL_FORM_RE = re.compile(r"\b(SA|SAS|SARL|SCI|EURL|EI|SNC|GMBH|LLC|LTD|INC|BV|NV)\b", re.IGNORECASE)
        self.POSTAL_CITY_RE = re.compile(r"\b\d{5}\b")
        self.EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.STREET_HINT_RE = re.compile(
            r"(^\d)|\b(rue|avenue|av\.?|boulevard|bd\.?|chemin|impasse|route|place|cours|all[ée]e)\b",
            re.IGNORECASE,
        )
        self.NOISE_TOKEN_RE = re.compile(
            r"^(SC|page \d+|NV-[0-9-]+|[0-9]{2}-[0-9]{2}-[0-9]{4}|t[ée]l[ée]phone|email|:contact@)",
            re.IGNORECASE,
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        replacements = {
            "％": "%",
            "€ ": "€",
            "N°client": "N° client",
            "N°Siret": "N° Siret",
            "IBANDE": "IBAN DE",
            "Mode de palement": "Mode de paiement",
            "Details banguaires": "Détails bancaires",
            "Détails banquaires": "Détails bancaires",
            "CodeAPE": "Code APE ",
            "N'TVAIntracom.": "N° TVA Intracom. ",
            "MaxMustermann": "Max Mustermann",
            "Avenuedes": "Avenue des",
            "Allemegne": "Allemagne",
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
    def split_city_token(token: str) -> tuple[str, str]:
        match = re.search(r"(.*?)(\b\d{5}\s+.+)", token)
        if not match:
            return "", token.strip()
        address_tail = match.group(1).strip(" ,")
        city = match.group(2).strip()
        return address_tail, city

    def join_tokens(self, tokens: list[str]) -> str:
        return self.normalize_text(" ".join(token.strip() for token in tokens if token.strip()))

    def is_noise_token(self, token: str) -> bool:
        return bool(self.NOISE_TOKEN_RE.search(token.strip()))

    def is_postal_city(self, token: str) -> bool:
        return bool(self.POSTAL_CITY_RE.search(token))

    def looks_like_company_token(self, token: str) -> bool:
        stripped = token.strip()
        if self.LEGAL_FORM_RE.search(stripped):
            return True
        letters_only = re.sub(r"[^A-Za-zÀ-ÿ-]", "", stripped)
        return bool(letters_only) and stripped.upper() == stripped and len(letters_only) > 3

    def parse_party_block(self, tokens: list[str], prefer_person: bool) -> dict[str, str]:
        if not tokens:
            return {}

        city_index = next((index for index in range(len(tokens) - 1, -1, -1) if self.is_postal_city(tokens[index])), None)
        if city_index is None:
            return {}

        city_token = tokens[city_index]
        address_tail, city = self.split_city_token(city_token)

        address_start = None
        for index, token in enumerate(tokens[:city_index]):
            if self.STREET_HINT_RE.search(token):
                address_start = index
                break

        if address_start is None:
            address_start = max(1, city_index - 1)

        head_tokens = [token for token in tokens[:address_start] if not self.is_noise_token(token)]
        address_tokens = tokens[address_start:city_index]
        if address_tail:
            address_tokens.append(address_tail)

        name = ""
        company = ""

        if prefer_person and head_tokens and self.CIVILITY_RE.search(head_tokens[0]):
            split_index = len(head_tokens)
            for index in range(1, len(head_tokens)):
                if self.looks_like_company_token(head_tokens[index]):
                    split_index = index
                    break
            name = self.join_tokens(head_tokens[:split_index])
            company = self.join_tokens(head_tokens[split_index:])
        else:
            name = self.join_tokens(head_tokens)

        return {
            "name": name,
            "company": company,
            "address": self.join_tokens(address_tokens),
            "city": city,
        }

    def _extract_document_type(self, joined_text: str) -> dict:
        block_config = self.config["document_type"]
        pattern = block_config["regex"]
        match = re.search(pattern, joined_text, flags=re.IGNORECASE)
        groups = {"1": match.group(1)} if match else {}
        return self.build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)

    def _extract_client_and_vendor(self, rec_texts: list[str]) -> tuple[dict, dict]:
        facture_index = self.find_token_index(rec_texts, r"\bfacture\b")
        postal_indices = [index for index, token in enumerate(rec_texts) if self.is_postal_city(token)]

        vendor_entry = self.build_entry(self.config["bloc_vendeur"].get("description"), "heuristic_vendor_segment", None, {})
        client_entry = self.build_entry(self.config["bloc_client"].get("description"), "heuristic_client_segment", None, {})

        if facture_index is None:
            return vendor_entry, client_entry

        header_postal_indices = [index for index in postal_indices if index < facture_index]
        if not header_postal_indices:
            return vendor_entry, client_entry

        client_city_index = header_postal_indices[-1]
        vendor_city_index = header_postal_indices[-2] if len(header_postal_indices) >= 2 else None

        client_start = vendor_city_index + 1 if vendor_city_index is not None else 0
        client_tokens = [token for token in rec_texts[client_start:facture_index] if not self.is_noise_token(token)]
        client_data = self.parse_party_block(client_tokens, prefer_person=True)
        
        if client_data:
            client_entry = self.build_entry(
                self.config["bloc_client"].get("description"),
                "heuristic_client_segment",
                self.join_tokens(client_tokens),
                {
                    "nom_client": client_data.get("name", ""),
                    "societe_client": client_data.get("company", ""),
                    "adresse_client": client_data.get("address", ""),
                    "code_postal_ville_client": client_data.get("city", ""),
                },
            )

        if vendor_city_index is not None:
            vendor_tokens = [token for token in rec_texts[: vendor_city_index + 1] if not self.is_noise_token(token)]
            vendor_data = self.parse_party_block(vendor_tokens, prefer_person=False)
            if vendor_data:
                vendor_entry = self.build_entry(
                    self.config["bloc_vendeur"].get("description"),
                    "heuristic_vendor_segment",
                    self.join_tokens(vendor_tokens),
                    {
                        "nom_vendeur": vendor_data.get("name", ""),
                        "adresse_vendeur": vendor_data.get("address", ""),
                        "code_postal_ville_vendeur": vendor_data.get("city", ""),
                    },
                )

        return vendor_entry, client_entry

    def _extract_infos_facture(self, joined_text: str) -> dict:
        block_config = self.config["bloc_infos_facture"]
        pattern = (
            r"Num[ée]ro de facture\s*:?\s*([A-Z0-9-]+)\s+"
            r"Date de facture\s*:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
            r"N.?\s*client\s*:?\s*([A-Z0-9-]+)"
        )
        match = re.search(pattern, joined_text, flags=re.IGNORECASE)
        groups = {}
        if match:
            groups = {
                "numero_facture": match.group(1),
                "date_facture": match.group(2),
                "numero_client": match.group(3),
            }
        return self.build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)

    def _extract_lignes_facture(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_lignes_facture"]
        start_index = self.find_token_index(rec_texts, r"Description")
        end_index = None
        if start_index is not None:
            total_ht_seen = 0
            for index in range(start_index + 1, len(rec_texts)):
                if re.search(r"^Total HT$", rec_texts[index], re.IGNORECASE):
                    total_ht_seen += 1
                    if total_ht_seen == 2:
                        end_index = index
                        break

        lines_tokens = rec_texts[start_index + 1 : end_index] if start_index is not None and end_index is not None else []
        full_match = self.join_tokens(lines_tokens) if lines_tokens else None
        return self.build_entry(
            block_config.get("description"),
            "heuristic_lines_between_description_and_total_ht",
            full_match,
            {"lignes": full_match or ""},
        )

    def _extract_totaux_tva(self, joined_text: str) -> dict:
        block_config = self.config["bloc_totaux_tva"]
        pattern = r"(Total HT.+?Total TTC\s*[0-9 ]+[.,][0-9]{2}\s*€?)"
        match = re.search(pattern, joined_text, flags=re.IGNORECASE)
        if not match:
            return self.build_entry(block_config.get("description"), pattern, None, {})

        segment = match.group(1)
        total_ht_match = re.search(r"Total HT\s+([0-9 ]+[.,][0-9]{2}\s*€?)", segment, flags=re.IGNORECASE)
        total_ttc_match = re.search(r"Total TTC\s*([0-9 ]+[.,][0-9]{2}\s*€?)", segment, flags=re.IGNORECASE)
        tva_amounts = re.findall(
            r"TVA(?:\s*\([0-9]{1,2}%\)|\s*[0-9]{1,2}\s*%)?\s+([0-9 ]+[.,][0-9]{2}\s*€?)",
            segment,
            flags=re.IGNORECASE,
        )

        return self.build_entry(
            block_config.get("description"),
            pattern,
            segment,
            {
                "total_ht": total_ht_match.group(1) if total_ht_match else "",
                "montant_tva20_tableau_gauche": tva_amounts[0] if len(tva_amounts) > 0 else "",
                "montant_tva20_tableau_droite": tva_amounts[1] if len(tva_amounts) > 1 else "",
                "montant_tva10_tableau_gauche": tva_amounts[2] if len(tva_amounts) > 2 else "",
                "montant_tva10_tableau_droite": tva_amounts[3] if len(tva_amounts) > 3 else "",
                "total_ttc": total_ttc_match.group(1) if total_ttc_match else "",
            },
        )

    def _extract_conditions_paiement(self, joined_text: str) -> dict:
        block_config = self.config["bloc_conditions_paiement"]
        pattern = (
            r"Conditions de paiement\s*:\s*(.+?)\s+"
            r"(?:[0-9 ]+[.,][0-9]{2}\s*€?)?\s*"
            r"Mode de pai?ement\s*:\s*(.+?)\s+"
            r"Nous vous remercions"
        )
        match = re.search(pattern, joined_text, flags=re.IGNORECASE)
        groups = {}
        if match:
            groups = {
                "conditions_paiement": match.group(1),
                "mode_paiement": match.group(2),
            }
        return self.build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)

    def _extract_signature_coordonnees(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_signature_coordonnees"]
        pattern = "heuristic_signature_from_rec_texts"
        start_index = self.find_token_index(rec_texts, r"^Cordialement$")
        if start_index is None:
            return self.build_entry(block_config.get("description"), pattern, None, {})

        segment_tokens = rec_texts[start_index:]
        segment = self.join_tokens(segment_tokens)

        def token_value(token_pattern: str, cleanup_pattern: str) -> str:
            index = self.find_token_index(segment_tokens, token_pattern)
            if index is None:
                return ""
            return self.normalize_text(re.sub(cleanup_pattern, "", segment_tokens[index], flags=re.IGNORECASE)).strip()

        details_index = self.find_token_index(segment_tokens, r"D[ée]tails?\s+bancaires")
        directeur_index = self.find_token_index(segment_tokens, r"^Directeur:?\s*$")
        iban_index = self.find_token_index(segment_tokens, r"^IBAN\b")
        bic_index = self.find_token_index(segment_tokens, r"^BIC\b")

        company = self.join_tokens(segment_tokens[1:details_index]) if details_index is not None else ""
        address = segment_tokens[directeur_index + 1] if directeur_index is not None and directeur_index + 1 < len(segment_tokens) else ""
        iban = token_value(r"^IBAN\b", r"^IBAN\s*")
        contact = segment_tokens[iban_index + 1] if iban_index is not None and iban_index + 1 < len(segment_tokens) else ""
        
        city = ""
        if iban_index is not None:
            for token in segment_tokens[iban_index + 2 :]:
                if self.is_postal_city(token):
                    city = token
                    break
                    
        bic = token_value(r"^BIC\b", r"^BIC\s*")
        country = segment_tokens[bic_index + 1] if bic_index is not None and bic_index + 1 < len(segment_tokens) else ""
        siret = token_value(r"Siret", r"^N.? ?Siret\s*")
        phone = token_value(r"T[ée]l|Tel", r"^T[ée]l\.?\s*:?\s*|^Tel\.?\s*:?\s*")
        code_ape = token_value(r"Code ?APE", r"^Code ?APE\s*")
        email = token_value(r"E-?Mail", r"^E-?Mail:?\s*")
        tva = token_value(r"TVA ?Intracom", r"^N.? ?TVA ?Intracom\.?\s*")

        return self.build_entry(
            block_config.get("description"),
            pattern,
            segment,
            {
                "nom_societe": company,
                "adresse": address,
                "iban": iban,
                "contact_nom": contact,
                "code_postal_ville": city,
                "bic": bic,
                "pays": country,
                "siret": siret,
                "telephone": phone,
                "code_ape": code_ape,
                "email": email,
                "tva_intracom": tva,
            },
        )

    def analyze(self, image_path: str) -> dict:
        results = self.ocr_model.predict(input=str(image_path))
        
        rec_texts = []
        records = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            for index, res in enumerate(results):
                result_path = temp_dir_path / f"temp_result_{index}.json"
                res.save_to_json(str(result_path))
                
                with result_path.open("r", encoding="utf-8") as handle:
                    page_data = json.load(handle)
                    
                page_texts = page_data.get("rec_texts", [])
                page_boxes = page_data.get("rec_boxes", [])
                
                if isinstance(page_texts, list):
                    for i, item in enumerate(page_texts):
                        normalized = self.normalize_text(str(item))
                        if not normalized:
                            continue
                        
                        rec_texts.append(normalized)
                        
                        if isinstance(page_boxes, list) and i < len(page_boxes):
                            box = page_boxes[i]
                            if isinstance(box, list) and len(box) == 4:
                                records.append({
                                    "text": normalized,
                                    "x1": float(box[0]),
                                    "y1": float(box[1]),
                                    "x2": float(box[2]),
                                    "y2": float(box[3]),
                                    "x_center": (float(box[0]) + float(box[2])) / 2,
                                })

        joined_text = self.join_tokens(rec_texts)
        vendor_entry, client_entry = self._extract_vendor_and_client(rec_texts, records)

        return {
            "document_type": self._extract_document_type(joined_text),
            "bloc_vendeur": vendor_entry,
            "bloc_client": client_entry,
            "bloc_infos_facture": self._extract_infos_facture(joined_text),
            "bloc_lignes_facture": self._extract_lignes_facture(rec_texts),
            "bloc_totaux_tva": self._extract_totaux_tva(joined_text),
            "bloc_conditions_paiement": self._extract_conditions_paiement(joined_text),
            "bloc_signature_coordonnees": self._extract_signature_coordonnees(rec_texts),
        }