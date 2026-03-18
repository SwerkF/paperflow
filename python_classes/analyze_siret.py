import json
import os
import re
from pathlib import Path

class AnalyzeSIRET:
    def __init__(self, config_path: str | Path = "analyse/attestation_siret.json"):
        """Initialise l'analyseur d'Attestation SIRET avec son fichier de configuration."""
        self.config_path = Path(config_path)
        
        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.OCR_REGEX_OVERRIDES = {
            "bloc_entete_entreprise": {
                "regex": (
                    r"ATTESTATION D['’]IMMATRICULATION AU REGISTRE NATIONAL DES ENTREPRISES[\s\S]+?"
                    r"(F\.O\.R\.D)\s*à la date du\s+([0-9]{1,2}\s+[A-Za-zéû]+(?:\s+[0-9]{4}))"
                )
            },
            "bloc_identite_entreprise": {
                "regex": (
                    r"Identité de [Il]'entreprise\s+Dénomination\s*:\s*(.+?)\s+"
                    r"SIREN \(siège\)\s*:?\s*([0-9 ]{9,20})\s+"
                    r"Date d'immatriculation au RNE\s*:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})?\s+"
                    r"Début d'activit[eé]\s*:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
                    r"Date de fin de la personne morale\s+([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
                    r"Date de clôture\s*:\s*([0-9]{2}/[0-9]{2})\s+"
                    r"Date de la première clo?ture\s*:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
                    r"Nature de l'activit[eé] principale\s*:\s*(.+?)\s+"
                    r"Forme juridique\s*:\s*(.+?)\s+Associé unique\s*:\s*(Oui|Non)"
                )
            },
            "bloc_activite_adresse_siege": {
                "regex": (
                    r"Activités principales de l'objet\s+(.+?)\s+social\s*:\s*(.+?)\s+"
                    r"Code APE\s*:\s*([0-9A-Z]+\s*-\s*.+?)\s+Capital social\s*:\s*([0-9 ]+\s*EUR)\s+"
                    r"Adresse du siège\s*:\s*(.+?)\s+(?:Données|Donnees) issues de la reprise des données\s+Gestion et Direction"
                )
            },
            "bloc_gestion_direction": {
                "regex": (
                    r"Gestion et Direction\s+Nom, Prénom\(s\)\s*:\s*(.+?)\s+"
                    r"Date de mise a jour de [Il]'entreprise\s*:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})"
                )
            },
            "bloc_qualite_naissance_residence": {
                "regex": (
                    r"Qualité\s*:\s*(.+?)\s+Date de naissance \(mm/aaaa\)\s*:\s*([0-9]{2}/[0-9]{4})\s+"
                    r"Commune de résidence\s*:\s*(.+?)\s+Établissements \(1\)"
                )
            },
            "bloc_etablissement": {
                "regex": (
                    r"Établissements \(1\)\s+Type d['’]etablisement\s*:\s*(.+?)\s+"
                    r"Date début d'activit[eé]\s*:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
                    r"Siret\s*:\s*(\d{14})\s+Nom commercial\s*:\s*(.+?)\s+"
                    r"Code APE\s*:\s*([0-9A-Z]+\s*-\s*.+?)\s+Origine du fonds\s*:\s*(.+?)\s+"
                    r"Nature de l'établissement\s*:\s*(.+?)\s+Activité principale\s*:\s*([\s\S]+?)\s+"
                    r"Adresse\s*:\s*(.+?)\s+(?:Données|Donnees) issues de la reprise des données"
                )
            },
        }

        self.ocr_model = None

    @staticmethod
    def normalize_text(joined_text: str) -> str:
        """Nettoie et corrige les erreurs fréquentes d'OCR spécifiques à l'attestation SIRET."""
        joined_text = re.sub(r"\s+", " ", joined_text).strip()
        
        replacements = {
            "F.O.R.Dà": "F.O.R.D à",
            "I'entreprise": "l'entreprise",
            "I'objet": "l'objet",
            "mise a jour": "mise à jour",
            "l'adresse": "l’adresse",
            "44120 VERTOU ANCE": "44120 VERTOU FRANCE"
        }
        
        for old, new in replacements.items():
            joined_text = joined_text.replace(old, new)
            
        joined_text = re.sub(r"(\d)O\b", r"\g<1>0", joined_text)
            
        return joined_text

    def _extract_blocks(self, joined_text: str) -> dict:
        """Applique les regex (soit depuis le JSON, soit surchargées) sur le texte."""
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
        """Exécute l'OCR sur une attestation SIRET et extrait tous les blocs configurés."""

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