import json
import re
import unicodedata
from pathlib import Path

class AnalyzeRIB:
    def __init__(self, config_path: str | Path = "analyse/rib.json"):
        """Initialise l'analyseur de RIB avec son fichier de configuration."""
        self.config_path = Path(config_path)
        
        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.DOC_TYPE_RE = re.compile(r"(Relev[ée]\s*d[’']?Identit[ée]\s+Bancaire|RIB)", re.IGNORECASE)
        self.IBAN_RE = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", re.IGNORECASE)
        self.BIC_RE = re.compile(r"\b[A-Z0-9]{8,11}\b")
        self.POSTAL_CITY_RE = re.compile(r"\b\d{4,5}[A-Z ]{2,}|\b\d{5}\s+[A-Za-zÀ-ÿ-]+", re.IGNORECASE)

    @staticmethod
    def normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        replacements = {
            "–": "-",
            "—": "-",
            "RELEVED'IDENTITE BANCAIRE": "RELEVE D'IDENTITE BANCAIRE",
            "IBAN(": "IBAN (",
            "Domicilliation": "Domiciliation",
            "N de compte": "Numero de compte",
            "$N° compt": "Numero de compte",
            "Clé": "Cle",
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
    def join_tokens(tokens: list[str]) -> str:
        return AnalyzeRIB.normalize_text(" ".join(token for token in tokens if AnalyzeRIB.normalize_text(token)))

    @staticmethod
    def find_token_index(tokens: list[str], pattern: str) -> int | None:
        regex = re.compile(pattern, re.IGNORECASE)
        for index, token in enumerate(tokens):
            if regex.search(token):
                return index
        return None

    #Extraction
    def _extract_document_type(self, joined_text: str) -> dict:
        block_config = self.config["document_type"]
        match = self.DOC_TYPE_RE.search(joined_text)
        groups = {"1": match.group(1)} if match else {}
        return self.build_entry(block_config.get("description"), block_config["regex"], match.group(0) if match else None, groups)

    def _extract_simple_regex_block(self, block_name: str, joined_text: str) -> dict:
        block_config = self.config[block_name]
        pattern = block_config["regex"]
        match = re.search(pattern, joined_text, flags=re.IGNORECASE | re.DOTALL)
        entry = self.build_entry(block_config.get("description"), pattern, match.group(0) if match else None, {})
        if match:
            for index, value in enumerate(match.groups(), start=1):
                key = block_config.get("groups", {}).get(str(index), str(index))
                entry["groups"][key] = value
        return entry

    def _extract_rib_national(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_rib_national"]
        bank_code, branch_code, account_number, rib_key, currency, bank_name, domicile = "", "", "", "", "", "", ""

        start = self.find_token_index(rec_texts, r"Identifiant national de compte bancaire|Code banque|Banque")
        end = self.find_token_index(rec_texts, r"Identifiant international de compte bancaire|\bIBAN\b")
        segment = rec_texts[start:end] if start is not None and end is not None and start < end else rec_texts

        headers = {
            "Identifiant national de compte bancaire - RIB", "Identifiant national de compte bancaire-RIB",
            "Code banque", "Code Guichet", "Numero de compte", "Cle RIB", "Banque", "Guichet", "Cle", "Devise", "Domiciliation", "RIB",
        }

        numbers = [token for token in segment if re.fullmatch(r"\d{2,14}", token)]
        if len(numbers) >= 4:
            five_digit_values = [token for token in numbers if len(token) == 5]
            if five_digit_values: bank_code = five_digit_values[0]
            if len(five_digit_values) > 1: branch_code = five_digit_values[1]
            account_candidates = [token for token in numbers if len(token) >= 10]
            account_number = account_candidates[0] if account_candidates else ""
            two_digit_candidates = [token for token in numbers if len(token) == 2]
            rib_key = two_digit_candidates[0] if two_digit_candidates else ""

        currency_match = next((token for token in segment if re.fullmatch(r"[A-Z]{3}", token)), "")
        currency = currency_match

        first_bank_code_index = next((i for i, token in enumerate(segment) if token == bank_code), None)
        currency_index = next((i for i, token in enumerate(segment) if token == currency), None)

        before_code_candidates = [token for token in (segment[:first_bank_code_index] if first_bank_code_index is not None else []) if token not in headers and re.search(r"[A-Za-z]", token)]
        after_currency_candidates = [token for token in (segment[currency_index + 1 :] if currency_index is not None else []) if token not in headers and re.search(r"[A-Za-z]", token)]

        if any("citibank" in token.lower() for token in segment):
            bank_name = next(token for token in segment if "citibank" in token.lower())
        elif "WorldRemit" in rec_texts: bank_name = "WorldRemit"
        elif after_currency_candidates: bank_name = after_currency_candidates[0]
        elif before_code_candidates: bank_name = before_code_candidates[-1]
        else:
            bank_name = next((token for token in segment if re.search(r"(banque|credit|citi|worldremit|caisse)", token, re.IGNORECASE) and not re.fullmatch(r"(Banque|Guichet|Code banque|Code Guichet|Numero de compte|Cle|Devise|Domiciliation|RIB)", token, re.IGNORECASE)), "")

        domicile_tokens = []
        for token in segment:
            if token in headers or token in {bank_code, branch_code, account_number, rib_key, currency}: continue
            if token == bank_name and not any(part.isdigit() for part in token): continue
            if re.search(r"[A-Za-z]", token): domicile_tokens.append(token)
            
        domicile = self.join_tokens(domicile_tokens)

        return self.build_entry(
            block_config.get("description"), "heuristic_rib_national", self.join_tokens(segment) or None,
            {"code_banque": bank_code, "code_guichet": branch_code, "cle_rib": rib_key, "devise": currency, "numero_compte": account_number, "domiciliation": domicile or bank_name, "nom_banque": bank_name}
        )

    def _extract_domiciliation(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_domiciliation"]
        start = self.find_token_index(rec_texts, r"Domiciliation")
        end = self.find_token_index(rec_texts, r"Identifiant international de compte bancaire|\bIBAN\b")
        
        if start is not None and end is not None and start < end: tokens = rec_texts[start + 1 : end]
        elif start is not None: tokens = rec_texts[start + 1 :]
        else: tokens = []

        segment = self.join_tokens(tokens)
        return self.build_entry(block_config.get("description"), "heuristic_domiciliation", segment or None, {"domiciliation": segment})

    def _extract_iban(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_iban"]
        iban = ""

        for token in rec_texts:
            compact = re.sub(r"\s+", "", token)
            if self.IBAN_RE.fullmatch(compact):
                iban = compact
                break

        if not iban:
            start = self.find_token_index(rec_texts, r"IBAN")
            if start is not None:
                parts = []
                for token in rec_texts[start + 1 : start + 9]:
                    compact = re.sub(r"\s+", "", token)
                    if re.fullmatch(r"[A-Z]{2}\d{2}", compact) or re.fullmatch(r"\d{3,4}", compact):
                        parts.append(compact)
                iban = "".join(parts)

        groups = {}
        if iban:
            iban_groups = re.findall(r".{1,4}", iban)
            for index, value in enumerate(iban_groups[:7], start=1):
                groups[f"iban_segment_{index}"] = value

        return self.build_entry(block_config.get("description"), "heuristic_iban", iban or None, groups)

    def _extract_bic(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_bic"]
        bic = ""
        start = self.find_token_index(rec_texts, r"BIC|SWIFT")
        
        if start is not None:
            for token in rec_texts[start + 1 : start + 4]:
                compact = re.sub(r"\s+", "", token)
                if self.BIC_RE.fullmatch(compact) and not compact.startswith("FR") and re.search(r"[A-Z]", compact):
                    bic = compact
                    break

        if not bic:
            for token in rec_texts:
                compact = re.sub(r"\s+", "", token)
                if self.BIC_RE.fullmatch(compact) and not compact.startswith("FR") and re.search(r"[A-Z]", compact):
                    bic = compact
                    break

        return self.build_entry(block_config.get("description"), "heuristic_bic", bic or None, {"bic_swift": bic})

    def _extract_titulaire_compte(self, rec_texts: list[str]) -> dict:
        block_config = self.config["bloc_titulaire_compte"]
        inline_holder = next((token for token in rec_texts if "Titulaire du compte" in token), "")
        inline_match = re.search(r"Titulaire du compte\s*:\s*(.+)", inline_holder, flags=re.IGNORECASE)
        start = self.find_token_index(rec_texts, r"Titulaire du compte|TITULAIRE DU COMPTE")
        tokens = rec_texts[start + 1 :] if start is not None else rec_texts

        name = self.normalize_text(inline_match.group(1)) if inline_match else ""
        address, city, country = "", "", ""

        for token in tokens:
            if token in {"〉", ">", ""}: continue
            if not name and re.search(r"(titulaire du compte)", token, re.IGNORECASE): continue
            if not name and re.search(r"[A-Za-z]", token) and len(token) > 3:
                name = token
                continue
            if name and not address and re.search(r"\d", token):
                address = token
                continue
            if name and not city and self.POSTAL_CITY_RE.search(token):
                city = token
                continue
            if name and not country and city and re.fullmatch(r"[A-Z][A-Z ]+", token):
                country = token

        return self.build_entry(
            block_config.get("description"), "heuristic_account_holder", self.join_tokens(tokens) or None,
            {"nom_titulaire": name, "adresse_titulaire": address, "ville_titulaire": city, "pays_titulaire": country}
        )

    def analyze_from_data(self, raw_rec_texts: list[str], raw_records: list[dict] = None) -> dict:
        """Traite les données OCR déjà extraites par l'API principale."""
        rec_texts = []
        for item in raw_rec_texts:
            normalized = self.normalize_text(item)
            if normalized:
                rec_texts.append(normalized)

        joined_text = self.join_tokens(rec_texts)

        # extraction des différets blocs
        return {
            "document_type": self._extract_document_type(joined_text),
            "bloc_intro_fr": self._extract_simple_regex_block("bloc_intro_fr", joined_text),
            "bloc_partie_reservee": self._extract_simple_regex_block("bloc_partie_reservee", joined_text),
            "bloc_intro_en": self._extract_simple_regex_block("bloc_intro_en", joined_text),
            "bloc_rib_national": self._extract_rib_national(rec_texts),
            "bloc_domiciliation": self._extract_domiciliation(rec_texts),
            "bloc_iban": self._extract_iban(rec_texts),
            "bloc_bic": self._extract_bic(rec_texts),
            "bloc_titulaire_compte": self._extract_titulaire_compte(rec_texts),
        }