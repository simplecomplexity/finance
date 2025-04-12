#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
getStockInfo.py     2025-04-15

TSE 上場銘柄（証券コード）の配当・株価・EPS・BPS を yfinance から取得するスクリプト
--------------------------------------------------------------------
使い方例：
# トヨタ(7203) と ソニー(6758) の株価と EPS を取得
python getStockInfo.py 7203 6758 --price --eps --market TSE

# 5016(新日石) の配当履歴だけ取得
python getStockInfo.py 5016 --div --market TSE

# 3 銘柄の株価・EPS・BPS を取得し CSV 出力
python getStockInfo.py 7203 6758 5016 --market TSE --price --eps --bps --csv result.csv

# ファイル codes.txt に列挙したコードで配当を取得
python getStockInfo.py --file codes.txt --div --market TSE

# 直接指定＋ファイル指定を混在させ CSV 出力
python getStockInfo.py --market TSE 7203 --file codes.txt --price --eps --csv result.csv

# ニューヨーク市場
python getStockInfo.py AAPL MSFT --market US --price --eps --csv result.csv

# 日米両市場を同時に取得する場合
python getStockInfo.py --file codes.txt --price --market US
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
def _infer_market(code: str) -> str:
    """数字のみなら 'TSE'、それ以外は 'US' とみなす"""
    return "TSE" if code.isdigit() else "US"


def _yf_ticker(code: str, market: str = "TSE") -> yf.Ticker:
    """
    Returns a yfinance Ticker object for the given stock code and market.
    - TSE (Tokyo Stock Exchange): Appends '.T' to the code.
    - US (U.S. markets): Uses the code as-is.
    """
    mkt = market or _infer_market(code)

    if mkt == "TSE":
        return yf.Ticker(f"{code}.T")
    elif mkt == "US":
        return yf.Ticker(code)
    else:
        raise ValueError(f"Unsupported market: {mkt}")


def _latest_close(code: str, market: str = "TSE") -> float | None:
    try:
        hist = _yf_ticker(code, market).history(period="1d", interval="1d")
        if hist.empty:
            print(f"Warning: No price data found for {code} in market {market}")
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching latest close for {code} in market {market}: {e}")
        return None


def _eps(code: str, market: str = "TSE") -> float | None:
    try:
        info = _yf_ticker(code, market).info
        for k in ("trailingEps", "epsTrailingTwelveMonths", "forwardEps"):
            if (v := info.get(k)) is not None:
                return float(v)
        print(f"Warning: No EPS data found for {code} in market {market}")
        return None
    except Exception as e:
        print(f"Error fetching EPS for {code} in market {market}: {e}")
        return None


def _bps(code: str, market: str = "TSE") -> float | None:
    try:
        info = _yf_ticker(code, market).info
        for k in ("bookValuePerShare", "bookValue"):
            if (v := info.get(k)) is not None:
                return float(v)
        print(f"Warning: No BPS data found for {code} in market {market}")
        return None
    except Exception as e:
        print(f"Error fetching BPS for {code} in market {market}: {e}")
        return None


def _dividends(code: str, market: str = "TSE") -> pd.DataFrame:
    try:
        ser = _yf_ticker(code, market).dividends
        if ser.empty:
            print(f"Warning: No dividend data found for {code} in market {market}")
            return pd.DataFrame()
        return ser.to_frame("Dividend").reset_index().rename(columns={"Date": "PayDate"})
    except Exception as e:
        print(f"Error fetching dividends for {code} in market {market}: {e}")
        return pd.DataFrame()


# ------------------------------------------------------------------
# 高レベル API
# ------------------------------------------------------------------
def fetch(
    code: str,
    market: str | None = None,  # Noneを許容
    want_price: bool = False,
    want_eps: bool = False,
    want_bps: bool = False,
    want_div: bool = False,
) -> dict[str, Any]:
    mkt = market or _infer_market(code) # 自動判定
    res: dict[str, Any] = {"Code": code, "Market": mkt}

    if want_price:
        res["Price"] = _latest_close(code, mkt)
    if want_eps:
        res["EPS"] = _eps(code, mkt)
    if want_bps:
        res["BPS"] = _bps(code, mkt)
    if want_div:
        res["Dividends"] = _dividends(code, mkt)
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
    p = argparse.ArgumentParser(description="TSE/US 上場銘柄情報取得ツール")
    p.add_argument("codes", nargs="*", help="証券コード（スペース区切りで複数可）")
    p.add_argument("--file", metavar="PATH", help="証券コードを列挙したテキストファイル")
    p.add_argument("--market", choices=["TSE", "US"], help="市場を強制指定 (未指定ならコードから自動判定)")
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
            market=args.market, # Noneを許容
            want_price=args.price,
            want_eps=args.eps,
            want_bps=args.bps,
            want_div=args.div,
        )

        # 表示
        print(f"\n=== {code} ({args.market}) ===")
        for k, v in data.items():
            if k == "Dividends":
                if args.div:
                    print("  Dividends:")
                    print(v if not v.empty else "    <no data>")
            elif k not in ("Code", "Market"):
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
