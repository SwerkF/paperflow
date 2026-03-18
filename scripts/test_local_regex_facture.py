import json
import os
import re
import unicodedata
from pathlib import Path


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

DEFAULT_IMAGE_PATH = Path("documents/facture/facture3.png")
IMAGE_PATH = os.environ.get("PAPERFLOW_INPUT_PATH", str(DEFAULT_IMAGE_PATH))
OUTPUT_DIR = Path(os.environ.get("PAPERFLOW_OUTPUT_DIR", "output8"))
OUTPUT_DIR.mkdir(exist_ok=True)

OCR_RESULT_PATH = OUTPUT_DIR / "facture_result.json"
REGEX_CONFIG_PATH = Path("analyse/facture.json")
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "facture_blocks.json"

CIVILITY_RE = re.compile(r"^(M(?:onsieur|me|adame)?|Mme|Madame|Mr)\b", re.IGNORECASE)
LEGAL_FORM_RE = re.compile(r"\b(SA|SAS|SARL|SCI|EURL|EI|SNC|GMBH|LLC|LTD|INC|BV|NV)\b", re.IGNORECASE)
POSTAL_CITY_RE = re.compile(r"\b\d{5}\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
STREET_HINT_RE = re.compile(
    r"(^\d)|\b(rue|avenue|av\.?|boulevard|bd\.?|chemin|impasse|route|place|cours|all[ée]e)\b",
    re.IGNORECASE,
)
NOISE_TOKEN_RE = re.compile(
    r"^(SC|page \d+|NV-[0-9-]+|[0-9]{2}-[0-9]{2}-[0-9]{4}|t[ée]l[ée]phone|email|:contact@)",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "％": "%",
        "€ ": "€",
        "N°client": "N° client",
        "N°Siret": "N° Siret",
        "IBANDE": "IBAN DE",
        "Mode de palement": "Mode de paiement",
        "Details banguaires": "Détails bancaires",
        "Détails banquaires": "Détails bancaires",
        "CodeAPE": "Code APE ",
        "N'TVAIntracom.": "N° TVA Intracom. ",
        "MaxMustermann": "Max Mustermann",
        "Avenuedes": "Avenue des",
        "Allemegne": "Allemagne",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def is_noise_token(token: str) -> bool:
    return bool(NOISE_TOKEN_RE.search(token.strip()))


def is_postal_city(token: str) -> bool:
    return bool(POSTAL_CITY_RE.search(token))


def join_tokens(tokens: list[str]) -> str:
    return normalize_text(" ".join(token.strip() for token in tokens if token.strip()))


def find_token_index(tokens: list[str], pattern: str) -> int | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for index, token in enumerate(tokens):
        if regex.search(token):
            return index
    return None


def looks_like_company_token(token: str) -> bool:
    stripped = token.strip()
    if LEGAL_FORM_RE.search(stripped):
        return True
    letters_only = re.sub(r"[^A-Za-zÀ-ÿ-]", "", stripped)
    return bool(letters_only) and stripped.upper() == stripped and len(letters_only) > 3


def split_city_token(token: str) -> tuple[str, str]:
    match = re.search(r"(.*?)(\b\d{5}\s+.+)", token)
    if not match:
        return "", token.strip()
    address_tail = match.group(1).strip(" ,")
    city = match.group(2).strip()
    return address_tail, city


def build_entry(description: str, regex: str, full_match: str | None, groups: dict[str, str]) -> dict:
    non_empty_groups = {key: value for key, value in groups.items() if value}
    return {
        "description": description,
        "regex": regex,
        "matched": bool(full_match or non_empty_groups),
        "full_match": full_match,
        "groups": non_empty_groups,
    }


def parse_party_block(tokens: list[str], prefer_person: bool) -> dict[str, str]:
    if not tokens:
        return {}

    city_index = next((index for index in range(len(tokens) - 1, -1, -1) if is_postal_city(tokens[index])), None)
    if city_index is None:
        return {}

    city_token = tokens[city_index]
    address_tail, city = split_city_token(city_token)

    address_start = None
    for index, token in enumerate(tokens[:city_index]):
        if STREET_HINT_RE.search(token):
            address_start = index
            break

    if address_start is None:
        address_start = max(1, city_index - 1)

    head_tokens = [token for token in tokens[:address_start] if not is_noise_token(token)]
    address_tokens = tokens[address_start:city_index]
    if address_tail:
        address_tokens.append(address_tail)

    name = ""
    company = ""

    if prefer_person and head_tokens and CIVILITY_RE.search(head_tokens[0]):
        split_index = len(head_tokens)
        for index in range(1, len(head_tokens)):
            if looks_like_company_token(head_tokens[index]):
                split_index = index
                break
        name = join_tokens(head_tokens[:split_index])
        company = join_tokens(head_tokens[split_index:])
    else:
        name = join_tokens(head_tokens)

    return {
        "name": name,
        "company": company,
        "address": join_tokens(address_tokens),
        "city": city,
    }


def extract_document_type(joined_text: str, config: dict) -> dict:
    block_config = config["document_type"]
    pattern = block_config["regex"]
    match = re.search(pattern, joined_text, flags=re.IGNORECASE)
    groups = {"1": match.group(1)} if match else {}
    return build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)


def extract_client_and_vendor(rec_texts: list[str], config: dict) -> tuple[dict, dict]:
    facture_index = find_token_index(rec_texts, r"\bfacture\b")
    postal_indices = [index for index, token in enumerate(rec_texts) if is_postal_city(token)]

    vendor_entry = build_entry(config["bloc_vendeur"].get("description"), "heuristic_vendor_segment", None, {})
    client_entry = build_entry(config["bloc_client"].get("description"), "heuristic_client_segment", None, {})

    if facture_index is None:
        return vendor_entry, client_entry

    header_postal_indices = [index for index in postal_indices if index < facture_index]
    if not header_postal_indices:
        return vendor_entry, client_entry

    client_city_index = header_postal_indices[-1]
    vendor_city_index = header_postal_indices[-2] if len(header_postal_indices) >= 2 else None

    client_start = vendor_city_index + 1 if vendor_city_index is not None else 0
    client_tokens = [token for token in rec_texts[client_start:facture_index] if not is_noise_token(token)]
    client_data = parse_party_block(client_tokens, prefer_person=True)
    if client_data:
        client_entry = build_entry(
            config["bloc_client"].get("description"),
            "heuristic_client_segment",
            join_tokens(client_tokens),
            {
                "nom_client": client_data.get("name", ""),
                "societe_client": client_data.get("company", ""),
                "adresse_client": client_data.get("address", ""),
                "code_postal_ville_client": client_data.get("city", ""),
            },
        )

    if vendor_city_index is not None:
        vendor_tokens = [token for token in rec_texts[: vendor_city_index + 1] if not is_noise_token(token)]
        vendor_data = parse_party_block(vendor_tokens, prefer_person=False)
        if vendor_data:
            vendor_entry = build_entry(
                config["bloc_vendeur"].get("description"),
                "heuristic_vendor_segment",
                join_tokens(vendor_tokens),
                {
                    "nom_vendeur": vendor_data.get("name", ""),
                    "adresse_vendeur": vendor_data.get("address", ""),
                    "code_postal_ville_vendeur": vendor_data.get("city", ""),
                },
            )

    return vendor_entry, client_entry


def extract_infos_facture(joined_text: str, config: dict) -> dict:
    block_config = config["bloc_infos_facture"]
    pattern = (
        r"Num[ée]ro de facture\s*:?\s*([A-Z0-9-]+)\s+"
        r"Date de facture\s*:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s+"
        r"N.?\s*client\s*:?\s*([A-Z0-9-]+)"
    )
    match = re.search(pattern, joined_text, flags=re.IGNORECASE)
    groups = {}
    if match:
        groups = {
            "numero_facture": match.group(1),
            "date_facture": match.group(2),
            "numero_client": match.group(3),
        }
    return build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)


def extract_lignes_facture(rec_texts: list[str], config: dict) -> dict:
    block_config = config["bloc_lignes_facture"]
    start_index = find_token_index(rec_texts, r"Description")
    end_index = None
    if start_index is not None:
        total_ht_seen = 0
        for index in range(start_index + 1, len(rec_texts)):
            if re.search(r"^Total HT$", rec_texts[index], re.IGNORECASE):
                total_ht_seen += 1
                if total_ht_seen == 2:
                    end_index = index
                    break

    lines_tokens = rec_texts[start_index + 1 : end_index] if start_index is not None and end_index is not None else []
    full_match = join_tokens(lines_tokens) if lines_tokens else None
    return build_entry(
        block_config.get("description"),
        "heuristic_lines_between_description_and_total_ht",
        full_match,
        {"lignes": full_match or ""},
    )


def extract_totaux_tva(joined_text: str, config: dict) -> dict:
    block_config = config["bloc_totaux_tva"]
    pattern = r"(Total HT.+?Total TTC\s*[0-9 ]+[.,][0-9]{2}\s*€?)"
    match = re.search(pattern, joined_text, flags=re.IGNORECASE)
    if not match:
        return build_entry(block_config.get("description"), pattern, None, {})

    segment = match.group(1)
    total_ht_match = re.search(r"Total HT\s+([0-9 ]+[.,][0-9]{2}\s*€?)", segment, flags=re.IGNORECASE)
    total_ttc_match = re.search(r"Total TTC\s*([0-9 ]+[.,][0-9]{2}\s*€?)", segment, flags=re.IGNORECASE)
    tva_amounts = re.findall(
        r"TVA(?:\s*\([0-9]{1,2}%\)|\s*[0-9]{1,2}\s*%)?\s+([0-9 ]+[.,][0-9]{2}\s*€?)",
        segment,
        flags=re.IGNORECASE,
    )

    return build_entry(
        block_config.get("description"),
        pattern,
        segment,
        {
            "total_ht": total_ht_match.group(1) if total_ht_match else "",
            "montant_tva20_tableau_gauche": tva_amounts[0] if len(tva_amounts) > 0 else "",
            "montant_tva20_tableau_droite": tva_amounts[1] if len(tva_amounts) > 1 else "",
            "montant_tva10_tableau_gauche": tva_amounts[2] if len(tva_amounts) > 2 else "",
            "montant_tva10_tableau_droite": tva_amounts[3] if len(tva_amounts) > 3 else "",
            "total_ttc": total_ttc_match.group(1) if total_ttc_match else "",
        },
    )


def extract_conditions_paiement(joined_text: str, config: dict) -> dict:
    block_config = config["bloc_conditions_paiement"]
    pattern = (
        r"Conditions de paiement\s*:\s*(.+?)\s+"
        r"(?:[0-9 ]+[.,][0-9]{2}\s*€?)?\s*"
        r"Mode de pai?ement\s*:\s*(.+?)\s+"
        r"Nous vous remercions"
    )
    match = re.search(pattern, joined_text, flags=re.IGNORECASE)
    groups = {}
    if match:
        groups = {
            "conditions_paiement": match.group(1),
            "mode_paiement": match.group(2),
        }
    return build_entry(block_config.get("description"), pattern, match.group(0) if match else None, groups)


def extract_signature_coordonnees(rec_texts: list[str], joined_text: str, config: dict) -> dict:
    block_config = config["bloc_signature_coordonnees"]
    pattern = "heuristic_signature_from_rec_texts"
    start_index = find_token_index(rec_texts, r"^Cordialement$")
    if start_index is None:
        return build_entry(block_config.get("description"), pattern, None, {})

    segment_tokens = rec_texts[start_index:]
    segment = join_tokens(segment_tokens)

    def token_value(token_pattern: str, cleanup_pattern: str) -> str:
        index = find_token_index(segment_tokens, token_pattern)
        if index is None:
            return ""
        return normalize_text(re.sub(cleanup_pattern, "", segment_tokens[index], flags=re.IGNORECASE)).strip()

    details_index = find_token_index(segment_tokens, r"D[ée]tails?\s+bancaires")
    directeur_index = find_token_index(segment_tokens, r"^Directeur:?\s*$")
    iban_index = find_token_index(segment_tokens, r"^IBAN\b")
    bic_index = find_token_index(segment_tokens, r"^BIC\b")

    company = join_tokens(segment_tokens[1:details_index]) if details_index is not None else ""
    address = segment_tokens[directeur_index + 1] if directeur_index is not None and directeur_index + 1 < len(segment_tokens) else ""
    iban = token_value(r"^IBAN\b", r"^IBAN\s*")
    contact = segment_tokens[iban_index + 1] if iban_index is not None and iban_index + 1 < len(segment_tokens) else ""
    city = ""

    if iban_index is not None:
        for token in segment_tokens[iban_index + 2 :]:
            if is_postal_city(token):
                city = token
                break
            
    bic = token_value(r"^BIC\b", r"^BIC\s*")
    country = segment_tokens[bic_index + 1] if bic_index is not None and bic_index + 1 < len(segment_tokens) else ""
    siret = token_value(r"Siret", r"^N.? ?Siret\s*")
    phone = token_value(r"T[ée]l|Tel", r"^T[ée]l\.?\s*:?\s*|^Tel\.?\s*:?\s*")
    code_ape = token_value(r"Code ?APE", r"^Code ?APE\s*")
    email = token_value(r"E-?Mail", r"^E-?Mail:?\s*")
    tva = token_value(r"TVA ?Intracom", r"^N.? ?TVA ?Intracom\.?\s*")

    return build_entry(
        block_config.get("description"),
        pattern,
        segment,
        {
            "nom_societe": company,
            "adresse": address,
            "iban": iban,
            "contact_nom": contact,
            "code_postal_ville": city,
            "bic": bic,
            "pays": country,
            "siret": siret,
            "telephone": phone,
            "code_ape": code_ape,
            "email": email,
            "tva_intracom": tva,
        },
    )


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
            rec_texts.extend(normalize_text(str(item)) for item in page_texts if normalize_text(str(item)))

    joined_text = normalize_text(" ".join(text.strip() for text in rec_texts if text.strip()))
    return rec_texts, joined_text


def extract_blocks(rec_texts: list[str], joined_text: str, config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    vendor_entry, client_entry = extract_client_and_vendor(rec_texts, config)
    return {
        "document_type": extract_document_type(joined_text, config),
        "bloc_vendeur": vendor_entry,
        "bloc_client": client_entry,
        "bloc_infos_facture": extract_infos_facture(joined_text, config),
        "bloc_lignes_facture": extract_lignes_facture(rec_texts, config),
        "bloc_totaux_tva": extract_totaux_tva(joined_text, config),
        "bloc_conditions_paiement": extract_conditions_paiement(joined_text, config),
        "bloc_signature_coordonnees": extract_signature_coordonnees(rec_texts, joined_text, config),
    }


def main() -> None:
    if os.environ.get("PAPERFLOW_SKIP_OCR") != "1":
        run_ocr()

    rec_texts, joined_text = load_joined_rec_texts(OCR_RESULT_PATH)
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

    print(f"Extraction enregistrée dans {EXTRACTED_BLOCKS_PATH}")


if __name__ == "__main__":
    main()
