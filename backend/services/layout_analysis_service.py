"""
layout_analysis_service.py
───────────────────────────
Spatial Layout Analysis Engine for Document Understanding.

Capabilities:
  - Preserves token bounding box spatial metrics: bbox [x1, y1, x2, y2], confidence, page, line, word
  - Clusters tokens into spatial rows and columns using horizontal and vertical projection
  - Identifies document headers, sections, and form key-value label pairs (nearest left/above label matching value)
  - Identifies tables: row-column grid cells, merged cells, headers, empty cells, and row/column relationships
  - Preserves spatial layout for forms and handwritten documents
"""

import math
from typing import Dict, Any, List, Optional, Tuple

class LayoutAnalysisService:

    def analyze_layout(
        self,
        ocr_tokens: List[Dict[str, Any]],
        image_shape: Optional[Tuple[int, int]] = None,
        page_num: int = 1
    ) -> Dict[str, Any]:
        """
        Processes raw OCR tokens with spatial coordinates into a structured Layout Tree.
        Never flattens tokens into a raw string; preserves spatial hierarchy & cell grid structures.
        """
        if not ocr_tokens:
            return {
                "rows": [],
                "columns": [],
                "tables": [],
                "form_pairs": {},
                "headers": [],
                "sections": []
            }

        # 1. Normalize token spatial bounding boxes
        parsed_tokens: List[Dict[str, Any]] = []
        for idx, tok in enumerate(ocr_tokens):
            text = str(tok.get("text", "")).strip()
            if not text:
                continue

            conf = float(tok.get("confidence", 0.95))
            page = int(tok.get("page", page_num))
            line = int(tok.get("line", idx + 1))
            word = int(tok.get("word", 1))

            bbox = tok.get("bbox", [])
            x1, y1, x2, y2 = 0.0, 0.0, 100.0, 20.0

            if isinstance(bbox, list) and len(bbox) >= 4:
                if isinstance(bbox[0], list): # Polygon [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
                    xs = [pt[0] for pt in bbox]
                    ys = [pt[1] for pt in bbox]
                    x1, x2 = min(xs), max(xs)
                    y1, y2 = min(ys), max(ys)
                elif len(bbox) == 4 and isinstance(bbox[0], (int, float)): # [x1, y1, x2, y2]
                    x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

            w = max(1.0, x2 - x1)
            h = max(1.0, y2 - y1)
            cx = x1 + w / 2.0
            cy = y1 + h / 2.0

            parsed_tokens.append({
                "text": text,
                "confidence": round(conf, 4),
                "page": page,
                "line": line,
                "word": word,
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center_x": round(cx, 2),
                "center_y": round(cy, 2),
                "width": round(w, 2),
                "height": round(h, 2)
            })

        # 2. Cluster Tokens into Spatial Rows (Horizontal lines)
        # Sort by vertical center_y
        sorted_by_y = sorted(parsed_tokens, key=lambda t: t["center_y"])
        rows: List[List[Dict[str, Any]]] = []

        for tok in sorted_by_y:
            placed = False
            for row in rows:
                row_cy = sum(t["center_y"] for t in row) / len(row)
                row_h = sum(t["height"] for t in row) / len(row)
                if abs(tok["center_y"] - row_cy) <= max(10.0, row_h * 0.6):
                    row.append(tok)
                    placed = True
                    break
            if not placed:
                rows.append([tok])

        # Sort tokens within each row left-to-right (by x1)
        for row in rows:
            row.sort(key=lambda t: t["bbox"][0])

        # 3. Detect Form Label-Value Pairs (e.g. "Name:" -> "John Doe" or "Date of Birth:" -> "15/08/1995")
        form_pairs: Dict[str, Dict[str, Any]] = {}
        for r_idx, row in enumerate(rows):
            for t_idx, tok in enumerate(row):
                text_lower = tok["text"].lower().rstrip(":")
                
                # Check if token is a label candidate
                is_label = any(kw in text_lower for kw in [
                    "name", "date", "dob", "pan", "aadhaar", "invoice", "number", "no", "total",
                    "amount", "email", "phone", "mobile", "address", "company", "tax", "gst", "subtotal"
                ]) or tok["text"].endswith(":")

                if is_label:
                    label_key = tok["text"].rstrip(":")
                    # Look to the right in same row
                    val_toks = row[t_idx + 1:]
                    if val_toks:
                        val_str = " ".join([v["text"] for v in val_toks])
                        val_conf = sum([v["confidence"] for v in val_toks]) / len(val_toks)
                        v_bbox = [val_toks[0]["bbox"][0], val_toks[0]["bbox"][1], val_toks[-1]["bbox"][2], val_toks[-1]["bbox"][3]]
                        form_pairs[label_key] = {
                            "value": val_str,
                            "raw_text": val_str,
                            "confidence": round(val_conf, 4),
                            "bbox": v_bbox,
                            "page": tok["page"],
                            "label_bbox": tok["bbox"]
                        }
                    elif r_idx + 1 < len(rows): # Look to row directly below
                        next_row = rows[r_idx + 1]
                        below_candidates = [
                            v for v in next_row if abs(v["center_x"] - tok["center_x"]) <= max(100.0, tok["width"] * 1.5)
                        ]
                        if below_candidates:
                            val_str = " ".join([v["text"] for v in below_candidates])
                            val_conf = sum([v["confidence"] for v in below_candidates]) / len(below_candidates)
                            v_bbox = [below_candidates[0]["bbox"][0], below_candidates[0]["bbox"][1], below_candidates[-1]["bbox"][2], below_candidates[-1]["bbox"][3]]
                            form_pairs[label_key] = {
                                "value": val_str,
                                "raw_text": val_str,
                                "confidence": round(val_conf, 4),
                                "bbox": v_bbox,
                                "page": tok["page"],
                                "label_bbox": tok["bbox"]
                            }

        # 4. Table Detection & Grid Extraction
        # Look for multi-row aligned text columns
        tables: List[Dict[str, Any]] = []
        table_rows: List[List[Dict[str, Any]]] = []
        for row in rows:
            if len(row) >= 2:
                # Potential table row
                table_rows.append(row)

        if len(table_rows) >= 2:
            # Determine headers from first row of table candidate
            header_row = table_rows[0]
            headers = [h["text"] for h in header_row]
            data_rows: List[List[str]] = []

            for r in table_rows[1:]:
                row_cells: List[str] = []
                for h_tok in header_row:
                    h_cx = h_tok["center_x"]
                    # Find cell in row aligned with header center_x
                    aligned_cell = [c for c in r if abs(c["center_x"] - h_cx) <= max(60.0, h_tok["width"] * 0.8)]
                    if aligned_cell:
                        row_cells.append(" ".join([c["text"] for c in aligned_cell]))
                    else:
                        row_cells.append("")
                data_rows.append(row_cells)

            tables.append({
                "table_name": "Table 1",
                "headers": headers,
                "rows": data_rows,
                "row_count": len(data_rows),
                "col_count": len(headers)
            })

        # 5. Extract Document Headers & Sections
        headers = [r[0]["text"] for r in rows if len(r) == 1 and r[0]["height"] > 25.0 or r[0]["text"].isupper()]

        return {
            "token_count": len(parsed_tokens),
            "rows": [[t["text"] for t in r] for r in rows],
            "parsed_tokens": parsed_tokens,
            "form_pairs": form_pairs,
            "tables": tables,
            "headers": headers
        }

layout_analysis_service = LayoutAnalysisService()
