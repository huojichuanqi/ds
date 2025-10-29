import re
from datetime import datetime
from typing import List, Dict, Any
import ast


HEADER_LINE = "============================================================"


def _safe_float(val: str):
    try:
        return float(val)
    except Exception:
        return None


def _parse_price(line: str):
    # ETH当前价格: $3,975.97
    m = re.search(r"\$\s*([0-9,]+\.?[0-9]*)", line)
    if m:
        return _safe_float(m.group(1).replace(",", ""))
    return None


def _parse_exec_time(line: str):
    # 执行时间: 2025-10-29 08:08:06
    ts = line.split("执行时间:", 1)[-1].strip()
    # Return raw string for display and also an iso if parsable
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return ts, dt.isoformat()
    except Exception:
        return ts, None


def _parse_position(text: str):
    try:
        return ast.literal_eval(text)
    except Exception:
        return text.strip()


def split_records(log_text: str) -> List[str]:
    # A record starts at a line with 执行时间: and ends before the next HEADER_LINE section
    lines = log_text.splitlines()
    records: List[List[str]] = []
    cur: List[str] = []
    in_record = False
    for ln in lines:
        if ln.strip().startswith("执行时间:"):
            if cur:
                records.append(cur)
                cur = []
            in_record = True
            cur.append(ln)
        elif ln.strip() == HEADER_LINE:
            # separator line; close previous record if any
            if cur and in_record:
                records.append(cur)
                cur = []
                in_record = False
        else:
            if in_record:
                cur.append(ln)
    if cur:
        records.append(cur)
    # Convert list of lines back to strings
    return ["\n".join(r).strip() for r in records if any(s.strip() for s in r)]


def parse_plus_log(log_text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for rec in split_records(log_text):
        lines = rec.splitlines()
        data: Dict[str, Any] = {
            "raw": rec,
        }
        # Extract fields
        i = 0
        # exec time
        if lines and lines[0].strip().startswith("执行时间:"):
            raw_ts, iso_ts = _parse_exec_time(lines[0])
            data["exec_time"] = raw_ts
            data["exec_time_iso"] = iso_ts
            i = 1
        # Scan rest
        # Capture DeepSeek block if present (brace-balanced after the marker)
        ds_raw = None
        brace_depth = 0
        in_ds = False
        ds_lines: List[str] = []

        # Helper to finish ds block
        def finish_ds():
            nonlocal ds_raw, in_ds, ds_lines, brace_depth
            if ds_lines:
                ds_raw = "\n".join(ds_lines).strip()
            in_ds = False
            brace_depth = 0
            ds_lines = []

        while i < len(lines):
            line = lines[i]
            s = line.strip()
            if s.startswith("ETH当前价格:"):
                data["eth_price"] = _parse_price(s)
            elif s.startswith("数据周期:"):
                data["timeframe"] = s.split(":", 1)[-1].strip()
            elif s.startswith("价格变化:"):
                data["price_change"] = s.split(":", 1)[-1].strip()
            elif s.startswith("DeepSeek原始回复:"):
                # everything after the colon could include a JSON-like block
                after = line.split(":", 1)[-1].lstrip()
                if after:
                    # Count braces in the same line
                    in_ds = True
                    ds_lines.append(after)
                    brace_depth += after.count("{") - after.count("}")
                    if brace_depth <= 0:
                        finish_ds()
                else:
                    in_ds = True
                # continue
            elif in_ds:
                ds_lines.append(line)
                brace_depth += line.count("{") - line.count("}")
                if brace_depth <= 0:
                    finish_ds()
            elif s.startswith("信号统计:"):
                data["signal_stats"] = s.split(":", 1)[-1].strip()
            elif s.startswith("⚠️") or s.startswith("⚠"):
                data["warning"] = s
            elif s.startswith("交易信号:"):
                data["signal"] = s.split(":", 1)[-1].strip()
            elif s.startswith("信心程度:"):
                data["confidence"] = s.split(":", 1)[-1].strip()
            elif s.startswith("理由:"):
                data["reason"] = s.split(":", 1)[-1].strip()
            elif s.startswith("止损:"):
                data["stop_loss"] = _parse_price(s)
            elif s.startswith("止盈:"):
                data["take_profit"] = _parse_price(s)
            elif s.startswith("当前持仓:"):
                pos_text = s.split(":", 1)[-1].strip()
                data["position"] = _parse_position(pos_text)
            elif s.startswith("根据账户余额调整下单数量为"):
                # 根据账户余额调整下单数量为 0.02 ETH (原始配置: 0.05 ETH)
                m = re.search(r"为\s+([0-9.]+)\s*ETH.*原始配置:\s*([0-9.]+)\s*ETH", s)
                if m:
                    data["adjusted_size"] = _safe_float(m.group(1))
                    data["original_size"] = _safe_float(m.group(2))
                data["sizing_note"] = s
            elif s:
                # Heuristic: capture last non-empty line as action/suggestion
                data["action"] = s

            i += 1

        if ds_raw:
            data["deepseek_raw"] = ds_raw

        # Generate an id for record (prefer exec_time)
        rec_id = data.get("exec_time") or data.get("exec_time_iso") or str(len(items))
        data["id"] = rec_id

        items.append(data)

    # Sort by time if iso available; else keep order
    def sort_key(x):
        return x.get("exec_time_iso") or x.get("exec_time") or ""

    items.sort(key=sort_key)
    return items

