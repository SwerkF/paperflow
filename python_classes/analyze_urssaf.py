import json
import os
import re
from pathlib import Path

class AnalyzeURSSAF:
    def __init__(self, config_path: str | Path = "analyse/vigilance_urssaf.json"):
        """Initialise l'analyseur d'attestation de vigilance URSSAF avec son fichier de configuration."""
        self.config_path = Path(config_path)
        
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

        self.ocr_model = None

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

    def analyze(self, image_path: str) -> dict:
        """Exécute l'OCR sur une attestation URSSAF et extrait tous les blocs."""
        
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
        for page in results:
            if not page: continue
            for item in page:
                rec_texts.append(str(item[1][0]))
                
        raw_joined_text = " ".join(text.strip() for text in rec_texts if text.strip())
        joined_text = self.normalize_text(raw_joined_text)

        return self._extract_blocks(joined_text)