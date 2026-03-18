import json
import os
import re
from pathlib import Path

class AnalyzeKBIS:
    def __init__(self,ocr_model, config_path: str | Path = "analyse/kbis.json"):
        """Initialise l'analyseur d'Extrait KBIS avec son fichier de configuration."""
        self.config_path = Path(config_path)

        self.ocr_model = ocr_model

        with self.config_path.open("r", encoding="utf-8") as handle:
            self.config = json.load(handle)

        self.OCR_REGEX_OVERRIDES = {
            "bloc_greffe": {
                "regex": (
                    r"Greffe du Tribunal de Commerce de\s+(.+?)\s+Code de vérification\s*:\s*([A-Za-z0-9]+)\s+"
                    r"4 RUE PABLO NERUDA\s+(https?://\S+)\s+\.?\s*92020 NANTERRE CEDEX\s+N.?\s*de gestion\s+([0-9A-Z]+)"
                )
            },
            "bloc_identification_personne_morale": {
                "regex": (
                    r"IDENTIFICATION DE LA PERSONNE MORALE\s+Immatriculation au RCS, numéro\s+([0-9 ]+R\.C\.S\.\s+.+?)\s+"
                    r"Date d'immatriculation\s+([0-9]{2}/[0-9]{2}/[0-9]{4})\s+Transfert du\s+(.+?)\s+"
                    r"Dénomination ou raison sociale\s+(.+?)\s+Forme juridique\s+(.+?)\s+Capital social\s+([0-9 ,.]+\s+Euros)\s+"
                    r"Adresse du sige\s+(.+?)\s+Durée de la personne morale\s+(.+?)\s+Date de clôture de l'exercice social\s+(.+?)\s+GESTION, DIRECTION"
                )
            },
            "bloc_president": {
                "regex": (
                    r"Président\s+Nom, prénoms\s+(.+?)\s+Date et lieu de naissance\s+(.+?)\s+"
                    r"Nationalité\s+(.+?)\s+Domicile personnel\s+(.+?)\s+Directeur général"
                )
            },
            "bloc_directeur_general": {
                "regex": (
                    r"Directeur général\s+Nom, prénoms\s+(.+?)\s+Date et lieu de naissance\s+(.+?)\s+"
                    r"Nationalité\s+(.+?)\s+Domicile personnel\s+(.+?)\s+Commissaire aux comptes titulaire"
                )
            },
            "bloc_commissaires_aux_comptes": {
                "regex": (
                    r"Commissaire aux comptes titulaire\s+Nom, prénoms\s+(.+?)\s+Domicile personnel ou adresse\s+(.+?)\s+professionnelle\s+"
                    r"Commissaire aux comptes suppléant\s+Nom, prénoms\s+(.+?)\s+Domicile personnel ou adresse\s+(.+?)\s+professionnelle\s+RENSEIGNEMENTS RELATIFS"
                )
            },
            "bloc_activite_etablissement_principal": {
                "regex": (
                    r"RENSEIGNEMENTS RELATIFS A L'ACTIVITE ET A L'ETABLISSEMENT PRINCIPAL\s+Adresse de .+?tablissement\s+(.+?)\s+"
                    r"Activité\(s\) exercée\(s\)\s+(.+?)\s+Date de commencement d'activité\s+([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
                    r"Origine du fonds ou de l'activité\s+(.+?)\s+Mode d'exploitation\s+(.+?)\s+IMMATRICULATION HORS RESSORT\s+(.+?)\s+R\.C\.S\."
                )
            },
            "bloc_observations": {
                "regex": (
                    r"OBSERVATIONS ET RENSEIGNEMENTS COMPLEMENTAIRES\s+- Mention n°\s*([0-9]+) du ([0-9]{2}/[0-9]{2}/[0-9]{4})\s+(.+?)\s+"
                    r"- Mention n°\s*([0-9]+) du ([0-9]{2}/[0-9]{2}/[0-9]{4})\s+(.+?)\s+Le Greffier"
                )
            },
        }


    @staticmethod
    def normalize_text(joined_text: str) -> str:
        """Nettoie et corrige les erreurs fréquentes d'OCR spécifiques au KBIS."""
        joined_text = re.sub(r"\s+", " ", joined_text).strip()
        
        replacements = {
            "N°de gestion": "N° de gestion",
            "CONTROLE,ASSOCIES": "CONTROLE, ASSOCIES",
            "23/12/1974à": "23/12/1974 à"
        }
        
        for old, new in replacements.items():
            joined_text = joined_text.replace(old, new)
            
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
        """Exécute l'OCR sur un extrait KBIS et extrait tous les blocs configurés."""

        results = self.ocr_model.predict(input=str(image_path))
        
        rec_texts = []
        for page in results:
            if not page: continue
            for item in page:
                rec_texts.append(str(item[1][0]))
                
        raw_joined_text = " ".join(text.strip() for text in rec_texts if text.strip())
        joined_text = self.normalize_text(raw_joined_text)

        return self._extract_blocks(joined_text)