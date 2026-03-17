import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://localhost:8000/Attestation%20SIRET.pdf"
OUTPUT_DIR = Path("output4")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "attestation_siret_result.json"
REGEX_CONFIG_PATH = Path("analyse/attestation_siret.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "attestation_siret_blocks.json"

OCR_REGEX_OVERRIDES = {
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

        result_path = OUTPUT_DIR / f"attestation_siret_result_{index}.json"
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
    joined_text = joined_text.replace("F.O.R.Dà", "F.O.R.D à")
    joined_text = joined_text.replace("I'entreprise", "l'entreprise")
    joined_text = joined_text.replace("I'objet", "l'objet")
    joined_text = joined_text.replace("mise a jour", "mise à jour")
    joined_text = joined_text.replace("l'adresse", "l’adresse")
    joined_text = re.sub(r"(\d)O\b", r"\g<1>0", joined_text)
    joined_text = joined_text.replace("44120 VERTOU ANCE", "44120 VERTOU FRANCE")
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
