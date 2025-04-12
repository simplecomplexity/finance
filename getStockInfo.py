#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TSE 上場銘柄（証券コード）の配当・株価・EPS・BPS を yfinance から取得するスクリプト
--------------------------------------------------------------------
使い方例：
# トヨタ(7203) と ソニー(6758) の株価と EPS を取得
python getStockInfo.py 7203 6758 --price --eps

# 5016(新日石) の配当履歴だけ取得
python getStockInfo.py 5016 --div

# 3 銘柄の株価・EPS・BPS を取得し CSV 出力
python getStockInfo.py 7203 6758 5016 --price --eps --bps --csv result.csv
python getStockInfo.py 7203 6758 5016 --price --eps --csv result.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


# ------------------------------------------------------------------
# 低レベル API ------------------------------------------------------
# ------------------------------------------------------------------
def _yf_ticker(code: str) -> yf.Ticker:
    """証券コード -> yfinance ティッカー"""
    return yf.Ticker(f"{code}.T")


def _latest_close(code: str) -> float | None:
    """直近終値（株価）"""
    hist = _yf_ticker(code).history(period="1d", interval="1d")
    return None if hist.empty else float(hist["Close"].iloc[-1])


def _eps(code: str) -> float | None:
    """EPS"""
    info = _yf_ticker(code).info
    for k in ("trailingEps", "epsTrailingTwelveMonths", "forwardEps"):
        if (v := info.get(k)) is not None:
            return float(v)
    return None


def _bps(code: str) -> float | None:
    """BPS"""
    info = _yf_ticker(code).info
    for k in ("bookValuePerShare", "bookValue"):
        if (v := info.get(k)) is not None:
            return float(v)
    return None


def _dividends(code: str) -> pd.DataFrame:
    """配当履歴（DataFrame, 空なら取得不可）"""
    ser = _yf_ticker(code).dividends
    if ser.empty:
        return pd.DataFrame()
    df = ser.to_frame("Dividend").reset_index().rename(columns={"Date": "PayDate"})
    return df


# ------------------------------------------------------------------
# 高レベル API ------------------------------------------------------
# ------------------------------------------------------------------
def fetch(
    code: str,
    want_price: bool = False,
    want_eps: bool = False,
    want_bps: bool = False,
    want_div: bool = False,
) -> dict[str, Any]:
    """指定コードについて要求された項目を取得し dict で返す"""
    result: dict[str, Any] = {"Code": code}

    if want_price:
        result["Price"] = _latest_close(code)

    if want_eps:
        result["EPS"] = _eps(code)

    if want_bps:
        result["BPS"] = _bps(code)

    if want_div:
        # 配当は DataFrame をそのまま格納
        result["Dividends"] = _dividends(code)

    return result


# ------------------------------------------------------------------
# CLI ---------------------------------------------------------------
# ------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="TSE 上場銘柄の株価・指標・配当を取得するツール"
    )
    p.add_argument("codes", nargs="+", help="証券コード（複数可）")
    p.add_argument("--price", action="store_true", help="株価を取得")
    p.add_argument("--eps", action="store_true", help="EPS を取得")
    p.add_argument("--bps", action="store_true", help="BPS を取得")
    p.add_argument("--div", action="store_true", help="配当履歴を取得")
    p.add_argument(
        "--csv", metavar="FILE", help="結果を CSV 保存（配当履歴は含めません）"
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not (args.price or args.eps or args.bps or args.div):
        raise SystemExit("少なくとも 1 つの取得オプションを指定してください")

    rows: list[dict[str, Any]] = []

    for code in args.codes:
        data = fetch(
            code,
            want_price=args.price,
            want_eps=args.eps,
            want_bps=args.bps,
            want_div=args.div,
        )

        # --- 表示 ---
        print(f"\n=== {code} ===")
        for k, v in data.items():
            if k == "Dividends":
                if args.div:
                    print("  Dividends:")
                    print(v if not v.empty else "    <no data>")
            elif k != "Code":
                print(f"  {k}: {v}")

        # CSV 用（Dividends は列挙しない）
        rows.append({k: v for k, v in data.items() if k != "Dividends"})

    # --- CSV 出力 ---
    if args.csv:
        df_out = pd.DataFrame(rows)
        path = Path(args.csv).expanduser()
        df_out.to_csv(path, index=False, encoding="utf-8")
        print(f"\n→ CSV 保存: {path}")


if __name__ == "__main__":
    main()
