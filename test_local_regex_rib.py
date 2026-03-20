import json
import os
import re
import unicodedata
from pathlib import Path


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

DEFAULT_IMAGE_PATH = Path("documents/rib/rib1.png")
IMAGE_PATH = os.environ.get("PAPERFLOW_INPUT_PATH", str(DEFAULT_IMAGE_PATH))
OUTPUT_DIR = Path(os.environ.get("PAPERFLOW_OUTPUT_DIR", "output1"))
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "rib_result.json"
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "rib_blocks.json"
REGEX_CONFIG_PATH = Path("analyse/rib.json")

DOC_TYPE_RE = re.compile(r"(Relev[ée]\s*d[’']?Identit[ée]\s+Bancaire|RIB)", re.IGNORECASE)
IBAN_RE = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", re.IGNORECASE)
BIC_RE = re.compile(r"\b[A-Z0-9]{8,11}\b")
POSTAL_CITY_RE = re.compile(r"\b\d{4,5}[A-Z ]{2,}|\b\d{5}\s+[A-Za-zÀ-ÿ-]+", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "–": "-",
        "—": "-",
        "RELEVED'IDENTITE BANCAIRE": "RELEVE D'IDENTITE BANCAIRE",
        "IBAN(": "IBAN (",
        "Domicilliation": "Domiciliation",
        "N de compte": "Numero de compte",
        "$N° compt": "Numero de compte",
        "Clé": "Cle",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def build_entry(description: str, regex: str, full_match: str | None, groups: dict[str, str]) -> dict:
    non_empty_groups = {key: value for key, value in groups.items() if value}
    return {
        "description": description,
        "regex": regex,
        "matched": bool(full_match or non_empty_groups),
        "full_match": full_match,
        "groups": non_empty_groups,
    }


def join_tokens(tokens: list[str]) -> str:
    return normalize_text(" ".join(token for token in tokens if normalize_text(token)))


def find_token_index(tokens: list[str], pattern: str) -> int | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for index, token in enumerate(tokens):
        if regex.search(token):
            return index
    return None


def run_ocr() -> None:
    from paddleocr import PaddleOCR

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


def load_rec_texts_from_existing_blocks(blocks_path: Path) -> tuple[list[str], str] | None:
    if not blocks_path.exists():
        return None

    with blocks_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rec_texts = data.get("rec_texts")
    if not isinstance(rec_texts, list):
        return None

    normalized = [normalize_text(str(item)) for item in rec_texts if normalize_text(str(item))]
    return normalized, join_tokens(normalized)


def load_rec_texts_from_ocr_result(result_path: Path) -> tuple[list[str], str]:
    with result_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rec_texts: list[str] = []
    for page in data:
        page_texts = page.get("rec_texts", [])
        if isinstance(page_texts, list):
            rec_texts.extend(normalize_text(str(item)) for item in page_texts if normalize_text(str(item)))

    return rec_texts, join_tokens(rec_texts)


def load_joined_rec_texts() -> tuple[list[str], str]:
    if os.environ.get("PAPERFLOW_USE_EXISTING_BLOCKS", "1") == "1":
        existing = load_rec_texts_from_existing_blocks(EXTRACTED_BLOCKS_PATH)
        if existing is not None:
            return existing

    return load_rec_texts_from_ocr_result(OCR_RESULT_PATH)


def extract_document_type(joined_text: str, config: dict) -> dict:
    block_config = config["document_type"]
    match = DOC_TYPE_RE.search(joined_text)
    groups = {"1": match.group(1)} if match else {}
    return build_entry(block_config.get("description"), block_config["regex"], match.group(0) if match else None, groups)


def extract_simple_regex_block(block_name: str, joined_text: str, config: dict) -> dict:
    block_config = config[block_name]
    pattern = block_config["regex"]
    match = re.search(pattern, joined_text, flags=re.IGNORECASE | re.DOTALL)
    entry = build_entry(block_config.get("description"), pattern, match.group(0) if match else None, {})
    if match:
        for index, value in enumerate(match.groups(), start=1):
            key = block_config.get("groups", {}).get(str(index), str(index))
            entry["groups"][key] = value
    return entry


def extract_rib_national(rec_texts: list[str], config: dict) -> dict:
    block_config = config["bloc_rib_national"]
    bank_code = ""
    branch_code = ""
    account_number = ""
    rib_key = ""
    currency = ""
    bank_name = ""
    domicile = ""

    start = find_token_index(rec_texts, r"Identifiant national de compte bancaire|Code banque|Banque")
    end = find_token_index(rec_texts, r"Identifiant international de compte bancaire|\bIBAN\b")
    segment = rec_texts[start:end] if start is not None and end is not None and start < end else rec_texts

    headers = {
        "Identifiant national de compte bancaire - RIB",
        "Identifiant national de compte bancaire-RIB",
        "Code banque",
        "Code Guichet",
        "Numero de compte",
        "Cle RIB",
        "Banque",
        "Guichet",
        "Cle",
        "Devise",
        "Domiciliation",
        "RIB",
    }

    numbers = [token for token in segment if re.fullmatch(r"\d{2,14}", token)]
    if len(numbers) >= 4:
        five_digit_values = [token for token in numbers if len(token) == 5]
        if five_digit_values:
            bank_code = five_digit_values[0]
        if len(five_digit_values) > 1:
            branch_code = five_digit_values[1]
        account_candidates = [token for token in numbers if len(token) >= 10]
        account_number = account_candidates[0] if account_candidates else ""
        two_digit_candidates = [token for token in numbers if len(token) == 2]
        rib_key = two_digit_candidates[0] if two_digit_candidates else ""

    currency_match = next((token for token in segment if re.fullmatch(r"[A-Z]{3}", token)), "")
    currency = currency_match

    first_bank_code_index = next((i for i, token in enumerate(segment) if token == bank_code), None)
    currency_index = next((i for i, token in enumerate(segment) if token == currency), None)

    before_code_candidates = [
        token
        for token in (segment[:first_bank_code_index] if first_bank_code_index is not None else [])
        if token not in headers and re.search(r"[A-Za-z]", token)
    ]
    after_currency_candidates = [
        token
        for token in (segment[currency_index + 1 :] if currency_index is not None else [])
        if token not in headers and re.search(r"[A-Za-z]", token)
    ]

    if any("citibank" in token.lower() for token in segment):
        bank_name = next(token for token in segment if "citibank" in token.lower())
    elif "WorldRemit" in rec_texts:
        bank_name = "WorldRemit"
    elif after_currency_candidates:
        bank_name = after_currency_candidates[0]
    elif before_code_candidates:
        bank_name = before_code_candidates[-1]
    else:
        bank_name = next(
            (
                token
                for token in segment
                if re.search(r"(banque|credit|citi|worldremit|caisse)", token, re.IGNORECASE)
                and not re.fullmatch(r"(Banque|Guichet|Code banque|Code Guichet|Numero de compte|Cle|Devise|Domiciliation|RIB)", token, re.IGNORECASE)
            ),
            "",
        )

    domicile_tokens = []
    for token in segment:
        if token in headers or token in {bank_code, branch_code, account_number, rib_key, currency}:
            continue
        if token == bank_name and not any(part.isdigit() for part in token):
            continue
        if re.search(r"[A-Za-z]", token):
            domicile_tokens.append(token)
    domicile = join_tokens(domicile_tokens)

    return build_entry(
        block_config.get("description"),
        "heuristic_rib_national",
        join_tokens(segment) or None,
        {
            "code_banque": bank_code,
            "code_guichet": branch_code,
            "cle_rib": rib_key,
            "devise": currency,
            "numero_compte": account_number,
            "domiciliation": domicile or bank_name,
            "nom_banque": bank_name,
        },
    )


def extract_domiciliation(rec_texts: list[str], config: dict) -> dict:
    block_config = config["bloc_domiciliation"]
    start = find_token_index(rec_texts, r"Domiciliation")
    end = find_token_index(rec_texts, r"Identifiant international de compte bancaire|\bIBAN\b")
    if start is not None and end is not None and start < end:
        tokens = rec_texts[start + 1 : end]
    elif start is not None:
        tokens = rec_texts[start + 1 :]
    else:
        tokens = []

    segment = join_tokens(tokens)
    return build_entry(
        block_config.get("description"),
        "heuristic_domiciliation",
        segment or None,
        {"domiciliation": segment},
    )


def extract_iban(rec_texts: list[str], joined_text: str, config: dict) -> dict:
    block_config = config["bloc_iban"]
    iban = ""

    for token in rec_texts:
        compact = re.sub(r"\s+", "", token)
        if IBAN_RE.fullmatch(compact):
            iban = compact
            break

    if not iban:
        start = find_token_index(rec_texts, r"IBAN")
        if start is not None:
            parts: list[str] = []
            for token in rec_texts[start + 1 : start + 9]:
                compact = re.sub(r"\s+", "", token)
                if re.fullmatch(r"[A-Z]{2}\d{2}", compact) or re.fullmatch(r"\d{3,4}", compact):
                    parts.append(compact)
            iban = "".join(parts)

    groups = {}
    if iban:
        iban_groups = re.findall(r".{1,4}", iban)
        for index, value in enumerate(iban_groups[:7], start=1):
            groups[f"iban_segment_{index}"] = value

    return build_entry(block_config.get("description"), "heuristic_iban", iban or None, groups)


def extract_bic(rec_texts: list[str], config: dict) -> dict:
    block_config = config["bloc_bic"]
    bic = ""
    start = find_token_index(rec_texts, r"BIC|SWIFT")
    if start is not None:
        for token in rec_texts[start + 1 : start + 4]:
            compact = re.sub(r"\s+", "", token)
            if BIC_RE.fullmatch(compact) and not compact.startswith("FR") and re.search(r"[A-Z]", compact):
                bic = compact
                break

    if not bic:
        for token in rec_texts:
            compact = re.sub(r"\s+", "", token)
            if BIC_RE.fullmatch(compact) and not compact.startswith("FR") and re.search(r"[A-Z]", compact):
                bic = compact
                break

    return build_entry(
        block_config.get("description"),
        "heuristic_bic",
        bic or None,
        {"bic_swift": bic},
    )


def extract_titulaire_compte(rec_texts: list[str], config: dict) -> dict:
    block_config = config["bloc_titulaire_compte"]
    inline_holder = next((token for token in rec_texts if "Titulaire du compte" in token), "")
    inline_match = re.search(r"Titulaire du compte\s*:\s*(.+)", inline_holder, flags=re.IGNORECASE)
    start = find_token_index(rec_texts, r"Titulaire du compte|TITULAIRE DU COMPTE")
    tokens = rec_texts[start + 1 :] if start is not None else rec_texts

    name = normalize_text(inline_match.group(1)) if inline_match else ""
    address = ""
    city = ""
    country = ""

    for index, token in enumerate(tokens):
        if token in {"〉", ">", ""}:
            continue
        if not name and re.search(r"(titulaire du compte)", token, re.IGNORECASE):
            continue
        if not name and re.search(r"[A-Za-z]", token) and len(token) > 3:
            name = token
            continue
        if name and not address and re.search(r"\d", token):
            address = token
            continue
        if name and not city and POSTAL_CITY_RE.search(token):
            city = token
            continue
        if name and not country and city and re.fullmatch(r"[A-Z][A-Z ]+", token):
            country = token

    return build_entry(
        block_config.get("description"),
        "heuristic_account_holder",
        join_tokens(tokens) or None,
        {
            "nom_titulaire": name,
            "adresse_titulaire": address,
            "ville_titulaire": city,
            "pays_titulaire": country,
        },
    )


def extract_blocks(rec_texts: list[str], joined_text: str, config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    return {
        "document_type": extract_document_type(joined_text, config),
        "bloc_intro_fr": extract_simple_regex_block("bloc_intro_fr", joined_text, config),
        "bloc_partie_reservee": extract_simple_regex_block("bloc_partie_reservee", joined_text, config),
        "bloc_intro_en": extract_simple_regex_block("bloc_intro_en", joined_text, config),
        "bloc_rib_national": extract_rib_national(rec_texts, config),
        "bloc_domiciliation": extract_domiciliation(rec_texts, config),
        "bloc_iban": extract_iban(rec_texts, joined_text, config),
        "bloc_bic": extract_bic(rec_texts, config),
        "bloc_titulaire_compte": extract_titulaire_compte(rec_texts, config),
    }


def main() -> None:
    if os.environ.get("PAPERFLOW_SKIP_OCR") != "1" and not (
        os.environ.get("PAPERFLOW_USE_EXISTING_BLOCKS", "1") == "1" and EXTRACTED_BLOCKS_PATH.exists()
    ):
        run_ocr()

    rec_texts, joined_text = load_joined_rec_texts()
    extracted_blocks = extract_blocks(rec_texts, joined_text, REGEX_CONFIG_PATH)

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

    print(f"Extraction enregistree dans {EXTRACTED_BLOCKS_PATH}")


if __name__ == "__main__":
    main()
