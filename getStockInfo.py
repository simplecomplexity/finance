#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
getStockInfo.py     2025-04-15

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

# ファイル codes.txt に列挙したコードで配当を取得
python getStockInfo.py --file codes.txt --div

# 直接指定＋ファイル指定を混在させ CSV 出力
python getStockInfo.py 7203 --file codes.txt --price --eps --csv result.csv
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yfinance as yf


# ------------------------------------------------------------------
# 低レベル API
# ------------------------------------------------------------------
def _yf_ticker(code: str) -> yf.Ticker:
    return yf.Ticker(f"{code}.T")


def _latest_close(code: str) -> float | None:
    hist = _yf_ticker(code).history(period="1d", interval="1d")
    return None if hist.empty else float(hist["Close"].iloc[-1])


def _eps(code: str) -> float | None:
    info = _yf_ticker(code).info
    for k in ("trailingEps", "epsTrailingTwelveMonths", "forwardEps"):
        if (v := info.get(k)) is not None:
            return float(v)
    return None


def _bps(code: str) -> float | None:
    info = _yf_ticker(code).info
    for k in ("bookValuePerShare", "bookValue"):
        if (v := info.get(k)) is not None:
            return float(v)
    return None


def _dividends(code: str) -> pd.DataFrame:
    ser = _yf_ticker(code).dividends
    if ser.empty:
        return pd.DataFrame()
    return ser.to_frame("Dividend").reset_index().rename(columns={"Date": "PayDate"})


# ------------------------------------------------------------------
# 高レベル API
# ------------------------------------------------------------------
def fetch(
    code: str,
    want_price: bool = False,
    want_eps: bool = False,
    want_bps: bool = False,
    want_div: bool = False,
) -> dict[str, Any]:
    res: dict[str, Any] = {"Code": code}
    if want_price:
        res["Price"] = _latest_close(code)
    if want_eps:
        res["EPS"] = _eps(code)
    if want_bps:
        res["BPS"] = _bps(code)
    if want_div:
        res["Dividends"] = _dividends(code)
    return res


# ------------------------------------------------------------------
# CLI (Command Line Interface)
# ------------------------------------------------------------------
def _read_code_file(path: str | Path) -> list[str]:
    """テキストファイルから証券コードを抽出（改行／カンマ区切り対応）"""
    text = Path(path).expanduser().read_text(encoding="utf-8")
    raw: Iterable[str] = (
        s.strip() for part in text.splitlines() for s in part.split(",")
    )
    # 4 桁の数字だけを抽出
    return [s for s in raw if s.isdigit() and len(s) <= 5]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="TSE 上場銘柄情報取得ツール")
    p.add_argument("codes", nargs="*", help="証券コード（スペース区切りで複数可）")
    p.add_argument("--file", metavar="PATH", help="証券コードを列挙したテキストファイル")
    p.add_argument("--price", action="store_true", help="株価を取得")
    p.add_argument("--eps", action="store_true", help="EPS を取得")
    p.add_argument("--bps", action="store_true", help="BPS を取得")
    p.add_argument("--div", action="store_true", help="配当履歴を取得")
    p.add_argument("--csv", metavar="FILE", help="結果を CSV 保存（配当履歴は含まず）")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not (args.price or args.eps or args.bps or args.div):
        raise SystemExit("少なくとも 1 つの取得オプション (--price/--eps/--bps/--div) を指定してください")

    # --- コード一覧を組み立てる ---------------------------------
    codes: list[str] = list(dict.fromkeys(args.codes))  # 直接指定（重複除去）

    if args.file:
        codes_from_file = _read_code_file(args.file)
        if not codes_from_file:
            raise SystemExit(f"ファイル '{args.file}' から有効なコードが読み取れませんでした")
        codes.extend(codes_from_file)

    if not codes:
        raise SystemExit("証券コードをコマンドラインまたは --file で指定してください")

    # 重複を除いてソート
    codes = sorted(set(codes))

    # --- 取得ループ ---------------------------------------------
    rows: list[dict[str, Any]] = []

    for code in codes:
        data = fetch(
            code,
            want_price=args.price,
            want_eps=args.eps,
            want_bps=args.bps,
            want_div=args.div,
        )

        # 表示
        print(f"\n=== {code} ===")
        for k, v in data.items():
            if k == "Dividends":
                if args.div:
                    print("  Dividends:")
                    print(v if not v.empty else "    <no data>")
            elif k != "Code":
                print(f"  {k}: {v}")

        # CSV 用
        rows.append({k: v for k, v in data.items() if k != "Dividends"})

    # --- CSV 出力 -----------------------------------------------
    if args.csv:
        df_out = pd.DataFrame(rows)
        Path(args.csv).expanduser().write_text(df_out.to_csv(index=False, encoding="utf-8"))
        print(f"\n→ CSV 保存: {args.csv}")


if __name__ == "__main__":
    main()
