import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://127.0.0.1:8000/Devis.png"
OUTPUT_DIR = Path("output2")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "facture_result.json"
REGEX_CONFIG_PATH = Path("analyse/devis.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "devis_blocks.json"


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
    return rec_texts, joined_text


def extract_blocks(joined_text: str, config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    extracted = {}
    for block_name, block_config in config.items():
        if block_name == "blocs_unitaires_utiles":
            continue

        pattern = block_config["regex"]
        match = re.search(pattern, joined_text, flags=re.IGNORECASE)

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
