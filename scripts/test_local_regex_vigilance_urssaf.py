import json
import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_PATH = "http://localhost:8000/Attestation_Vigilance_URSSAF.png"
OUTPUT_DIR = Path("output5")
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "vigilance_urssaf_result.json"
REGEX_CONFIG_PATH = Path("analyse/vigilance_urssaf.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "vigilance_urssaf_blocks.json"

OCR_REGEX_OVERRIDES = {
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

        result_path = OUTPUT_DIR / f"vigilance_urssaf_result_{index}.json"
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
    joined_text = joined_text.replace("VENUSSIEUX", "VENISSIEUX")
    joined_text = joined_text.replace("VENrSSTEUX", "VENISSIEUX")
    joined_text = joined_text.replace("wars", "mars")
    joined_text = joined_text.replace("palement", "paiement")
    joined_text = joined_text.replace("cotisations et contrib tions sociales", "cotisations et contributions sociales")
    joined_text = joined_text.replace("cotisations et contrib ns sociales", "cotisations et contributions sociales")
    joined_text = joined_text.replace("SAcuite soca", "Sécurité sociale")
    joined_text = joined_text.replace("vérntcation", "vérification")
    joined_text = joined_text.replace("authenticté", "authenticité")
    joined_text = joined_text.replace("valdie", "validité")
    joined_text = joined_text.replace("selfectue", "s'effectue")
    joined_text = joined_text.replace("THERMIQU", "THERMIQUE")
    joined_text = joined_text.replace("A VENUSSIEUX", "A VENISSIEUX")
    joined_text = joined_text.replace("1e 26/01/2022", "le 26/01/2022")
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
