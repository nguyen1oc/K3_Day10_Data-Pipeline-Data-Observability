from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FIELDS = {
    "id",
    "question_type",
    "question",
    "ground_truth",
    "ground_truth_doc_ids",
}


def _load_frozen_test_set(test_set_path: Path) -> list[dict[str, Any]]:
    """Load and validate frozen evaluation set from JSON file."""
    if not test_set_path.exists():
        raise FileNotFoundError(
            f"Frozen test set not found: {test_set_path.resolve()}"
        )

    try:
        with test_set_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in frozen test set: {test_set_path}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError("Frozen test set must be a JSON list.")

    if not data:
        raise ValueError("Frozen test set is empty.")

    validated_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"Test item at index {index} must be a JSON object."
            )

        missing_fields = REQUIRED_FIELDS - item.keys()
        if missing_fields:
            raise ValueError(
                f"Test item at index {index} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        item_id = item["id"]
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(
                f"Test item at index {index} has invalid id."
            )

        if item_id in seen_ids:
            raise ValueError(f"Duplicate test item id: {item_id}")

        seen_ids.add(item_id)

        if not isinstance(item["question_type"], str):
            raise ValueError(
                f"Item {item_id}: question_type must be a string."
            )

        if not isinstance(item["question"], str) or not item["question"].strip():
            raise ValueError(
                f"Item {item_id}: question must be a non-empty string."
            )

        if not isinstance(item["ground_truth"], str):
            raise ValueError(
                f"Item {item_id}: ground_truth must be a string."
            )

        doc_ids = item["ground_truth_doc_ids"]
        if not isinstance(doc_ids, list) or not all(
            isinstance(doc_id, str) and doc_id.strip()
            for doc_id in doc_ids
        ):
            raise ValueError(
                f"Item {item_id}: ground_truth_doc_ids "
                "must be a list of non-empty strings."
            )

        validated_items.append(item)

    return validated_items


def build_test_set(
    df: pd.DataFrame,
    output_path,
) -> list[dict[str, Any]]:
    """Load frozen evaluation set from data/eval/test_set.json.

    Args:
        df:
            Cleaned DataFrame. Được giữ trong signature để tương thích
            với pipeline hiện tại và dùng để kiểm tra document ID.
        output_path:
            Tham số được giữ để tương thích với code cũ. Frozen test set
            luôn được đọc từ data/eval/test_set.json.

    Returns:
        Danh sách các câu hỏi evaluation đã được đóng băng.

    Raises:
        FileNotFoundError:
            Nếu không tìm thấy data/eval/test_set.json.
        ValueError:
            Nếu file sai JSON, sai schema hoặc tham chiếu paper_id
            không có trong cleaned DataFrame.
    """
    project_root = Path(__file__).resolve().parents[2]
    test_set_path = project_root / "data" / "eval" / "test_set.json"

    test_items = _load_frozen_test_set(test_set_path)

    # Kiểm tra các document ID trong test set có tồn tại trong clean data.
    if not df.empty and "paper_id" in df.columns:
        available_doc_ids = set(
            df["paper_id"].dropna().astype(str).tolist()
        )

        missing_doc_ids = sorted(
            {
                doc_id
                for item in test_items
                for doc_id in item["ground_truth_doc_ids"]
                if doc_id not in available_doc_ids
            }
        )

        if missing_doc_ids:
            raise ValueError(
                "Frozen test set references document IDs that do not "
                f"exist in cleaned data: {missing_doc_ids}"
            )

    return test_items

if __name__ == "__main__":
    from pathlib import Path

    # Resolve project root
    project_root = Path(__file__).resolve().parents[2]

    clean_csv_path = project_root / "data" / "clean" / "papers_clean.csv"
    frozen_testset_path = project_root / "data" / "eval" / "test_set.json"

    print(f"[testset] Loading cleaned data from: {clean_csv_path}")
    df = pd.read_csv(clean_csv_path)
    print(f"[testset] Loaded {len(df)} cleaned records")

    print(f"[testset] Loading frozen evaluation set...")
    test_items = build_test_set(df, frozen_testset_path)

    print(f"[testset] Loaded {len(test_items)} evaluation questions")
    print()

    # Print sample questions
    print("[testset] Sample questions:")
    for item in test_items[:5]:
        print(f"  [{item['id']}] ({item['question_type']})")
        print(f"    Q: {item['question']}")
        print(f"    GT: {item['ground_truth']}")
        print(f"    Docs: {', '.join(item['ground_truth_doc_ids'])}")
        print()

    print("[testset] Validation successful!")