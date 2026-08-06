from __future__ import annotations

from pathlib import Path
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate realistic data corruption across clean records:
    1. Drop latest records.
    2. Blank summary on selected rows.
    3. Inject noise into summary text.
    4. Truncate title.
    5. Alter published date / age_days to make records stale.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Persist corruption log.
    """
    corrupted_df = df.copy()
    corruption_log: list[dict] = []

    total_initial = len(corrupted_df)
    if total_initial < 5:
        write_json(Path(output_log_path), {"total_initial": total_initial, "corruptions": corruption_log})
        return corrupted_df

    # 1. Drop latest records (e.g. drop 2 newest records)
    dropped_rows = corrupted_df.tail(2)
    corrupted_df = corrupted_df.iloc[:-2].reset_index(drop=True)
    for _, row in dropped_rows.iterrows():
        corruption_log.append({
            "type": "drop_latest_record",
            "paper_id": str(row.get("paper_id")),
            "details": "Dropped latest published record from dataset.",
        })

    # 2. Blank summary for 2 rows
    if len(corrupted_df) >= 2:
        idx_blank = [0, 1]
        for idx in idx_blank:
            paper_id = str(corrupted_df.loc[idx, "paper_id"])
            corrupted_df.loc[idx, "summary"] = ""
            corrupted_df.loc[idx, "summary_chars"] = 0
            corruption_log.append({
                "type": "blank_summary",
                "paper_id": paper_id,
                "details": "Cleared summary content to empty string.",
            })

    # 3. Inject noise text into summary for 2 rows
    if len(corrupted_df) >= 4:
        idx_noise = [2, 3]
        for idx in idx_noise:
            paper_id = str(corrupted_df.loc[idx, "paper_id"])
            orig = str(corrupted_df.loc[idx, "summary"])
            corrupted_df.loc[idx, "summary"] = "@@@GARBLED NOISE@@@ " + orig[:30] + " ###ERR###"
            corruption_log.append({
                "type": "inject_noise",
                "paper_id": paper_id,
                "details": "Injected garbled noise text into summary.",
            })

    # 4. Truncate title for 2 rows
    if len(corrupted_df) >= 6:
        idx_trunc = [4, 5]
        for idx in idx_trunc:
            paper_id = str(corrupted_df.loc[idx, "paper_id"])
            orig_title = str(corrupted_df.loc[idx, "title"])
            corrupted_df.loc[idx, "title"] = orig_title[:10]
            corruption_log.append({
                "type": "truncate_title",
                "paper_id": paper_id,
                "details": f"Truncated title from '{orig_title}' to '{orig_title[:10]}'.",
            })

    # 5. Make published date old (stale record corruption)
    if len(corrupted_df) >= 7:
        idx_stale = 6
        paper_id = str(corrupted_df.loc[idx_stale, "paper_id"])
        corrupted_df.loc[idx_stale, "published"] = "2010-01-01"
        corrupted_df.loc[idx_stale, "age_days"] = 5000
        corruption_log.append({
            "type": "make_stale_date",
            "paper_id": paper_id,
            "details": "Altered published date to 2010-01-01 and age_days to 5000.",
        })

    # 6. Add duplicate row
    if len(corrupted_df) >= 1:
        dup_row = corrupted_df.iloc[[0]].copy()
        paper_id = str(dup_row.iloc[0].get("paper_id"))
        corrupted_df = pd.concat([corrupted_df, dup_row], ignore_index=True)
        corruption_log.append({
            "type": "add_duplicate",
            "paper_id": paper_id,
            "details": "Duplicated record 0 to create duplicate entry.",
        })

    # 7. Rebuild `text_for_embedding`
    def _rebuild_text(row: pd.Series) -> str:
        title = str(row.get("title", ""))
        authors = str(row.get("authors_joined", ""))
        summary = str(row.get("summary", ""))
        parts = [f"Title: {title}"]
        if authors:
            parts.append(f"Authors: {authors}")
        if summary:
            parts.append(f"Summary: {summary}")
        return "\n".join(parts)

    corrupted_df["text_for_embedding"] = corrupted_df.apply(_rebuild_text, axis=1)

    # 8. Write log
    write_json(Path(output_log_path), {
        "total_initial": total_initial,
        "total_corrupted": len(corrupted_df),
        "corruptions": corruption_log,
    })

    return corrupted_df

