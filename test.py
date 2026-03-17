import json
import os
from pathlib import Path

from paddleocr import PaddleOCR


os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

IMAGE_URL = "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/general_ocr_002.png"
OUTPUT_DIR = Path("output2")
OUTPUT_DIR.mkdir(exist_ok=True)

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)

results = ocr.predict(input=IMAGE_URL)

json_results = []
for index, res in enumerate(results):
    res.print()
    res.save_to_img(str(OUTPUT_DIR))

    result_path = OUTPUT_DIR / f"result_{index}.json"
    res.save_to_json(str(result_path))

    with result_path.open("r", encoding="utf-8") as handle:
        json_results.append(json.load(handle))

with (OUTPUT_DIR / "result.json").open("w", encoding="utf-8") as handle:
    json.dump(json_results, handle, ensure_ascii=False, indent=2)
