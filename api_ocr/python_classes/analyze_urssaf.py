import json
import os
import re
from pathlib import Path
import tempfile
import base64
import numpy as np
import cv2

class AnalyzeURSSAF:
    def __init__(self, ocr_model, config_path: str | Path = "analyse/urssaf.json"):
        """Initialise l'analyseur d'attestation de vigilance URSSAF avec son fichier de configuration."""
        self.config_path = Path(config_path)
        self.ocr_model = ocr_model
        
        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.OCR_REGEX_OVERRIDES = {
            "bloc_emetteur": {
                "regex": (
                    r"(Urssaf)\s+Au service de notre protection sociale\s+"
                    r"([A-Z]+,?le\s+[0-9]{2}/[0-9]{2}/[0-9]{4}\s+\d+\s+rue du\s+\d+\s+Mars\s+\d+\s+URSSAF RHONE-ALPES\s+\d{5}\s+VENISSIEUX CEDEX)\s+"
                    r"POUR NOUS CONTACTER\s+Courriel:?\s+(.+?)\s+Tel:?\s+(\d{4})\s+"
                    r"SAS ELYOTHERM\s+REFERENCES\s+TRAVINSTALEQUIPEMENTS THERMIQUE\s+\d+\s+BD\s+AMBROISE\s+PARE\s+N.?SIREN\s+(\d{9})"
                )
            },
            "bloc_date_destinataire": {
                "regex": (
                    r"([A-Z]+,?le\s+[0-9]{2}/[0-9]{2}/[0-9]{4})\s+\d+\s+rue du\s+\d+\s+Mars\s+\d+\s+URSSAF RHONE-ALPES\s+\d{5}\s+VENISSIEUX CEDEX\s+"
                    r"POUR NOUS CONTACTER\s+Courriel:?\s+.+?\s+Tel:?\s+\d{4}\s+"
                    r"(SAS\s+ELYOTHERM)\s+REFERENCES\s+(TRAVINSTALEQUIPEMENTS\s+THERMIQUE)\s+(\d+\s+BD\s+AMBROISE\s+PARE)\s+N.?SIREN\s+\d{9}\s+(\d{5}\s+MEYZIEU)"
                )
            },
            "bloc_cadre_legal": {
                "regex": (
                    r"ArticleL?\.?243-15\s+du\s+code\s+de\s+la\s+Securit[ée]\s+sociale\s+Madame,\s+Monsieur,\s+CODE DE SECURITE\s+.*?\s+([A-Z0-9]{10,20})\s+En votre"
                )
            },
            "bloc_message_principal": {
                "regex": (
                    r"Madame,\s+Monsieur,\s+CODE DE SECURITE\s+"
                    r"(Je vous adresse.+?Pour tout renseignement complementaire,nhesitez pas a prendre contact avec nos conseillers\s+Urssaf\.)"
                )
            },
            "bloc_signature": {
                "regex": r"Cordialement,\s+Le Directeur\s+([A-Za-zÉéÈèÊêËëÎîÏïÔôÖöÙùÛûÜüÇç\s]+?)\s+S\d"
            },
        }


    @staticmethod
    def normalize_text(joined_text: str) -> str:
        """Nettoie et corrige les erreurs fréquentes d'OCR spécifiques à l'URSSAF."""
        joined_text = re.sub(r"\s+", " ", joined_text).strip()
        
        replacements = {
            "VENUSSIEUX": "VENISSIEUX",
            "VENrSSTEUX": "VENISSIEUX",
            "wars": "mars",
            "palement": "paiement",
            "cotisations et contrib tions sociales": "cotisations et contributions sociales",
            "cotisations et contrib ns sociales": "cotisations et contributions sociales",
            "SAcuite soca": "Sécurité sociale",
            "vérntcation": "vérification",
            "authenticté": "authenticité",
            "valdie": "validité",
            "selfectue": "s'effectue",
            "THERMIQU": "THERMIQUE",
            "A VENUSSIEUX": "A VENISSIEUX",
            "1e 26/01/2022": "le 26/01/2022"
        }
        
        for old, new in replacements.items():
            joined_text = joined_text.replace(old, new)
            
        return joined_text

    def _extract_blocks(self, joined_text: str) -> dict:
        """Applique les regex sur le texte."""
        extracted = {}
        
        for block_name, block_config in self.config.items():
            if block_name == "blocs_unitaires_utiles":
                continue

            override = self.OCR_REGEX_OVERRIDES.get(block_name, {})
            pattern = override.get("regex", block_config["regex"])
            match = re.search(pattern, joined_text, flags=re.IGNORECASE | re.DOTALL)

            entry = {
                "description": block_config.get("description"),
                "regex": pattern,
                "matched": bool(match),
                "full_match": match.group(0) if match else None,
                "groups": {},
            }

            group_mapping = block_config.get("groups", {})
            if match:
                for index, value in enumerate(match.groups(), start=1):
                    key = group_mapping.get(str(index), str(index))
                    entry["groups"][key] = value

            extracted[block_name] = entry

        return extracted
    
    def analyze_base64(self, base64_string: str) -> dict:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        img_bytes = base64.b64decode(base64_string)
        np_array = np.frombuffer(img_bytes, np.uint8)
        img_cv2 = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        results = self.ocr_model.predict(input=img_cv2)

        rec_texts = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            for index, res in enumerate(results):
                result_path = temp_dir_path / f"temp_result_{index}.json"
                res.save_to_json(str(result_path))
                
                with result_path.open("r", encoding="utf-8") as handle:
                    page_data = json.load(handle)
                    
                page_texts = page_data.get("rec_texts", [])
                
                if isinstance(page_texts, list):
                    for item in page_texts:
                        text_str = str(item).strip()
                        if text_str:
                            rec_texts.append(text_str)

        raw_joined_text = " ".join(rec_texts)
        joined_text = self.normalize_text(raw_joined_text)

        return self._extract_blocks(joined_text)


    def analyze_from_data(self, raw_rec_texts: list[str], raw_records: list[dict] = None) -> dict:
        rec_texts = []
        for item in raw_rec_texts:
            text_str = item.strip()
            if text_str:
                rec_texts.append(text_str)

        raw_joined_text = " ".join(rec_texts)
        joined_text = self.normalize_text(raw_joined_text)

        # Extraction dynamique à partir du JSON
        return self._extract_blocks(joined_text)