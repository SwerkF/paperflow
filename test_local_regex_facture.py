import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://127.0.0.1:8000/modele-facture-gratuit.pdf"
OUTPUT_DIR = Path("output7")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "facture_result.json"
REGEX_CONFIG_PATH = Path("analyse/facture.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "facture_blocks.json"

OCR_REGEX_OVERRIDES = {
    "bloc_client": {
        "regex": r"(Monsieur Jean Dupont)\s+(Acheteur SA)\s+(.+?)\s+(\d{5}\s+.+?)\s+FACTURE"
    },
    "bloc_infos_facture": {
        "regex": r"Num[ée]ro de facture:?\s*(\d+)\s+Date de facture:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+N.?\s*client:?\s*(\d+)"
    },
    "bloc_signature_coordonnees": {
        "regex": (
            r"Cordialement\s+(Sevenit GmbH)\s+Details banguaires\s+Directeur:?\s+(.+?)\s+IBAN\s*([A-Z]{2}\d{2}[0-9 ]+)\s+"
            r"(.+?)\s+(\d{5}\s+.+?)\s+BIC\s+([A-Z0-9]+)\s+(.+?)\s+NSiret\s+(.+?)\s+"
            r"Tel\.?\s*:?\s*(.+?)\s+Code APE\s+(.+?)\s+E-?Mail:?\s*(.+?)\s+N.?TVA.?Intracom\.?\s*(.+)"
        ),
        "groups": {
            "1": "nom_societe",
            "2": "adresse",
            "3": "iban",
            "4": "contact_nom",
            "5": "code_postal_ville",
            "6": "bic",
            "7": "pays",
            "8": "siret",
            "9": "telephone",
            "10": "code_ape",
            "11": "email",
            "12": "tva_intracom"
        }
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

        result_path = OUTPUT_DIR / f"facture_result_{index}.json"
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
    joined_text = joined_text.replace("N°client", "N° client")
    joined_text = joined_text.replace("IBANDE", "IBAN DE")
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

        group_mapping = override.get("groups", block_config.get("groups", {}))
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
