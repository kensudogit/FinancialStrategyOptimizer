from app.services.adapters import parse_stooq_csv, parse_yahoo_chart, to_stooq_symbol, to_yahoo_symbol
from app.services.market_data import load_bars


def test_stooq_symbol_mapping():
    assert to_stooq_symbol("7203.T", "stock") == "7203.jp"
    assert to_stooq_symbol("USDJPY", "fx") == "usdjpy"
    assert to_yahoo_symbol("7203.T", "stock") == "7203.T"
    assert to_yahoo_symbol("USDJPY", "fx") == "USDJPY=X"


def test_parse_yahoo_chart():
    stamps = [1_704_067_200 + i * 86400 for i in range(90)]
    closes = [1800 + i for i in range(90)]
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": stamps,
                    "indicators": {
                        "quote": [
                            {
                                "open": closes,
                                "high": closes,
                                "low": closes,
                                "close": closes,
                                "volume": [1] * 90,
                            }
                        ]
                    },
                }
            ]
        }
    }
    df = parse_yahoo_chart(payload, 80)
    assert df is not None
    assert len(df) == 80
    assert df["close"].iloc[-1] == 1889


def test_parse_stooq_csv_needs_enough_rows():
    header = "Date,Open,High,Low,Close,Volume\n"
    short = header + "\n".join(f"2024-01-{i:02d},100,101,99,100.5,1000" for i in range(1, 28))
    assert parse_stooq_csv(short, 80) is None
    text = header + "\n".join(f"2020-03-{(i % 28) + 1:02d},{100 + i},101,99,{100 + i},1" for i in range(90))
    df = parse_stooq_csv(text, 80)
    assert df is not None
    assert len(df) == 80
    assert {"ts", "open", "high", "low", "close", "volume"} <= set(df.columns)


def test_load_bars_uses_sample_under_pytest():
    df, source = load_bars("7203.T", "stock", bars=120, seed=1)
    assert len(df) == 120
    assert source.startswith("sample:")


def test_unknown_symbol():
    try:
        load_bars("NOPE.T", "stock")
    except ValueError as exc:
        assert "未知" in str(exc)
    else:
        raise AssertionError("should fail")
