import requests

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "crypto_fiat_price",
        "description": (
            "Get live price for a cryptocurrency or fiat currency. "
            "For crypto use CoinGecko (e.g. 'bitcoin', 'ethereum'). "
            "For fiat use Frankfurter (e.g. 'EUR', 'GBP', 'JPY')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "CoinGecko coin id (e.g. 'bitcoin', 'ethereum') or "
                        "ISO-4217 currency code (e.g. 'EUR', 'GBP')."
                    ),
                }
            },
            "required": ["symbol"],
        },
    },
}

_CRYPTO_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "ether": "ethereum",
    "xrp": "ripple", "doge": "dogecoin", "ltc": "litecoin",
    "sol": "solana", "ada": "cardano", "usdt": "tether",
    "usdc": "usd-coin", "avax": "avalanche-2", "dot": "polkadot",
    "matic": "matic-network", "link": "chainlink", "bnb": "binancecoin",
}

_FIAT_CODES = {
    "usd", "eur", "gbp", "jpy", "cny", "cad", "aud", "chf",
    "inr", "brl", "krw", "try", "rub", "sar", "sek", "nok",
    "mxn", "zar", "pln", "huf", "czk", "dkk", "sek", "hkd",
    "sgd", "nzd", "thb", "myr", "php", "idr", "vnd", "btc",
}

_SESSION = requests.Session()
_SESSION.headers["Accept"] = "application/json"


def _try_crypto(symbol: str) -> str | None:
    coin_id = _CRYPTO_IDS.get(symbol.lower().replace(" ", "_"))
    if coin_id is None:
        coin_id = symbol.lower().replace(" ", "-")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_change": "true",
    }
    try:
        resp = _SESSION.get(url, params=params, timeout=8)
        if resp.status_code == 429:
            return "CoinGecko rate-limited. Try again later."
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return f"Could not reach CoinGecko API: {exc}"
    if coin_id not in data:
        return None
    info = data[coin_id]
    price = info.get("usd", "N/A")
    cap = info.get("usd_market_cap")
    change = info.get("usd_24h_change")
    result = f"{coin_id.upper()}: ${price:,.2f} USD"
    if cap:
        result += f"  |  Market cap: ${cap:,.0f}"
    if change is not None:
        direction = "+" if change >= 0 else ""
        result += f"  |  24h: {direction}{change:.2f}%"
    return result


def _try_fiat(symbol: str) -> str | None:
    code = symbol.upper().strip()
    if code == "USD" or len(code) != 3:
        return None
    try:
        url = "https://api.frankfurter.app/latest"
        params = {"from": code, "to": "USD"}
        resp = _SESSION.get(url, params=params, timeout=8)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception as exc:
        return f"Could not reach Frankfurter API: {exc}"
    rate = data.get("rates", {}).get("USD")
    if rate is None:
        return None
    return f"{code}/USD: {rate:.4f} (as of {data.get('date', 'N/A')})"


def execute(**kwargs) -> str:
    symbol = (kwargs.get("symbol") or "").strip()
    if not symbol:
        return "Error: symbol is required."

    crypto_result = _try_crypto(symbol)
    if crypto_result:
        return crypto_result

    fiat_result = _try_fiat(symbol)
    if fiat_result:
        return fiat_result

    return f"Currency '{symbol}' not found. Try a CoinGecko id (bitcoin, ethereum) or ISO-4217 code (EUR, GBP)."
