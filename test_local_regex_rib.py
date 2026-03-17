import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://127.0.0.1:8000/RIB.pdf"
OUTPUT_DIR = Path("output3")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "rib_result.json"
REGEX_CONFIG_PATH = Path("analyse/rib.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "rib_blocks.json"

OCR_REGEX_OVERRIDES = {
    "bloc_rib_national": {
        "regex": (
            r"Identifiant national de compte bancaire\s+[–-]\s+RIB\s+"
            r"Code Banque\s+Code Guichet\s+Num[ée]ro de compte\s+Cl[ée] RIB\s+Devise\s+Domiciliation\s+"
            r"(.+?)\s+(\d{5})\s+(\d{5})\s+(\d{2})\s+(.+?)\s+(\d{10,11})\s+([A-Z]{3})\s+"
            r"(\d{5}\s+.+?\s+CEDEX\s+\d+\s+France)\s+Identifiant international de compte bancaire"
        ),
        "groups": {
            "1": "nom_banque",
            "2": "code_banque",
            "3": "code_guichet",
            "4": "cle_rib",
            "5": "adresse_domiciliation",
            "6": "numero_compte",
            "7": "devise",
            "8": "ville_domiciliation",
        },
    },
    "bloc_domiciliation": {
        "regex": (
            r"Domiciliation\s+((?:[A-Za-z].+?)\s+\d{5}\s+\d{5}\s+\d{2}\s+.+?\s+"
            r"\d{10,11}\s+[A-Z]{3}\s+\d{5}\s+.+?\s+CEDEX\s+\d+\s+France)\s+"
            r"Identifiant international de compte bancaire"
        ),
        "groups": {
            "1": "domiciliation",
        },
    },
    "bloc_iban": {
        "regex": (
            r"IBAN \(International Bank Account Number\)\s+BIC \(Bank Identifier Code\)\s+"
            r"([A-Z]{2}\d{2})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{3})\s+"
            r"[A-Z0-9]{8,11}\s+TITULAIRE DU COMPTE"
        ),
        "groups": {
            "1": "iban_segment_1",
            "2": "iban_segment_2",
            "3": "iban_segment_3",
            "4": "iban_segment_4",
            "5": "iban_segment_5",
            "6": "iban_segment_6",
            "7": "iban_segment_7",
        },
    },
    "bloc_bic": {
        "regex": (
            r"BIC \(Bank Identifier Code\)\s+[A-Z]{2}\d{2}\s+(?:\d{4}\s+){5}\d{3}\s+([A-Z0-9]{8,11})\s+"
            r"TITULAIRE DU COMPTE"
        ),
        "groups": {
            "1": "bic_swift",
        },
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

        result_path = OUTPUT_DIR / f"rib_result_{index}.json"
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
        group_mapping = override.get("groups", block_config.get("groups", {}))
        match = re.search(pattern, joined_text, flags=re.IGNORECASE | re.DOTALL)

        entry = {
            "description": block_config.get("description"),
            "regex": pattern,
            "matched": bool(match),
            "full_match": match.group(0) if match else None,
            "groups": {},
        }

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
