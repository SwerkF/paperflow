import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://localhost:8000/Extrait_KBIS.pdf"
OUTPUT_DIR = Path("output6")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "kbis_result.json"
REGEX_CONFIG_PATH = Path("analyse/kbis.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "kbis_blocks.json"

OCR_REGEX_OVERRIDES = {
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


def run_ocr() -> None:
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
        enable_mkldnn=False,
    )

    results = ocr.predict(input=str(IMAGE_PATH))

    json_results = []
    for index, res in enumerate(results):
        res.print()
        res.save_to_img(str(OUTPUT_DIR))

        result_path = OUTPUT_DIR / f"kbis_result_{index}.json"
        res.save_to_json(str(result_path))

        with result_path.open("r", encoding="utf-8") as handle:
            json_results.append(json.load(handle))

    with OCR_RESULT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(json_results, handle, ensure_ascii=False, indent=2)


def load_joined_rec_texts(result_path: Path) -> tuple[list[str], str]:
    with result_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rec_texts: list[str] = []
    for page in data:
        page_texts = page.get("rec_texts", [])
        if isinstance(page_texts, list):
            rec_texts.extend(str(item) for item in page_texts)

    joined_text = " ".join(text.strip() for text in rec_texts if str(text).strip())
    joined_text = re.sub(r"\s+", " ", joined_text).strip()
    joined_text = joined_text.replace("N°de gestion", "N° de gestion")
    joined_text = joined_text.replace("CONTROLE,ASSOCIES", "CONTROLE, ASSOCIES")
    joined_text = joined_text.replace("23/12/1974à", "23/12/1974 à")
    return rec_texts, joined_text


def extract_blocks(joined_text: str, config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    extracted = {}
    for block_name, block_config in config.items():
        if block_name == "blocs_unitaires_utiles":
            continue

        override = OCR_REGEX_OVERRIDES.get(block_name, {})
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


def main() -> None:
    run_ocr()

    rec_texts, joined_text = load_joined_rec_texts(OCR_RESULT_PATH)
    extracted_blocks = extract_blocks(joined_text, REGEX_CONFIG_PATH)

    payload = {
        "source_image": IMAGE_PATH,
        "ocr_result_file": str(OCR_RESULT_PATH),
        "regex_config_file": str(REGEX_CONFIG_PATH),
        "rec_texts": rec_texts,
        "joined_text": joined_text,
        "extracted_blocks": extracted_blocks,
    }

    with EXTRACTED_BLOCKS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"Extraction enregistrée dans {EXTRACTED_BLOCKS_PATH}")


if __name__ == "__main__":
    main()
