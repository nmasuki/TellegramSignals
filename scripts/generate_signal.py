"""Generate random trading signals for testing purposes"""
import csv
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Common trading symbols with their typical price ranges
SYMBOLS = {
    "EURUSD": (1.0500, 1.1200, 4),   # (min, max, decimals)
    "GBPUSD": (1.2000, 1.3000, 4),
    "USDJPY": (140.00, 155.00, 2),
    "GBPJPY": (180.00, 195.00, 2),
    "XAUUSD": (1900.00, 2100.00, 2),
    "XAGUSD": (22.00, 28.00, 2),
    "US30": (38000, 42000, 0),
    "NAS100": (17000, 20000, 0),
    "BTCUSD": (40000, 70000, 0),
    "ETHUSD": (2000, 4000, 0),
    "AUDUSD": (0.6400, 0.6800, 4),
    "USDCAD": (1.3400, 1.3800, 4),
    "NZDUSD": (0.5800, 0.6200, 4),
    "USDCHF": (0.8600, 0.9000, 4),
}


def load_config() -> dict:
    """Load configuration from config/config.yaml"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def expand_path(path: str) -> Path:
    """Expand environment variables in path"""
    return Path(os.path.expandvars(path))


def get_channels_from_config(config: dict) -> list[str]:
    """Extract enabled channel usernames from config"""
    channels = []
    for channel in config.get("telegram", {}).get("channels", []):
        if channel.get("enabled", True):
            channels.append(channel["username"])
    return channels if channels else ["nickalphatrader", "GaryGoldLegacy"]


def get_allowed_symbols(config: dict) -> list[str]:
    """Get allowed symbols from config validation section"""
    symbols = config.get("validation", {}).get("symbol_validation", {}).get("allowed_symbols", [])
    return [s for s in symbols if s in SYMBOLS] if symbols else list(SYMBOLS.keys())


def generate_random_signal(config: dict) -> dict:
    """Generate a single random trading signal"""
    allowed_symbols = get_allowed_symbols(config)
    channels = get_channels_from_config(config)

    symbol = random.choice(allowed_symbols)
    price_min, price_max, decimals = SYMBOLS[symbol]

    direction = random.choice(["BUY", "SELL"])

    # Generate entry price
    entry_price = round(random.uniform(price_min, price_max), decimals)

    # Calculate pip/point size based on decimals
    pip_size = 10 ** (-decimals) * (10 if decimals >= 3 else 1)
    if symbol in ["XAUUSD", "US30", "NAS100", "BTCUSD", "ETHUSD"]:
        pip_size = 1.0 if symbol == "XAUUSD" else (10 if symbol in ["US30", "NAS100"] else 50)

    # Determine if using range entry (30% chance)
    use_range_entry = random.random() < 0.3

    if use_range_entry:
        entry_min = round(entry_price - pip_size * random.randint(5, 15), decimals)
        entry_max = round(entry_price + pip_size * random.randint(5, 15), decimals)
        entry_price = None
    else:
        entry_min = None
        entry_max = None

    # Calculate SL and TPs based on direction
    sl_pips = random.randint(20, 50)
    tp_pips = [random.randint(30, 60), random.randint(60, 100), random.randint(100, 150), random.randint(150, 200)]

    base_price = entry_price if entry_price else (entry_min + entry_max) / 2

    if direction == "BUY":
        stop_loss = round(base_price - pip_size * sl_pips, decimals)
        tp1 = round(base_price + pip_size * tp_pips[0], decimals)
        tp2 = round(base_price + pip_size * tp_pips[1], decimals)
        tp3 = round(base_price + pip_size * tp_pips[2], decimals)
        tp4 = round(base_price + pip_size * tp_pips[3], decimals)
    else:
        stop_loss = round(base_price + pip_size * sl_pips, decimals)
        tp1 = round(base_price - pip_size * tp_pips[0], decimals)
        tp2 = round(base_price - pip_size * tp_pips[1], decimals)
        tp3 = round(base_price - pip_size * tp_pips[2], decimals)
        tp4 = round(base_price - pip_size * tp_pips[3], decimals)

    # Randomly omit some TPs (realistic scenario)
    num_tps = random.choices([1, 2, 3, 4], weights=[10, 30, 40, 20])[0]
    if num_tps < 4:
        tp4 = None
    if num_tps < 3:
        tp3 = None
    if num_tps < 2:
        tp2 = None

    # Generate timestamps
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    extracted_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate other fields
    message_id = random.randint(10000, 99999)
    channel = random.choice(channels)
    confidence = round(random.uniform(0.75, 0.99), 2)

    # Notes based on conditions
    notes = ""
    if use_range_entry:
        notes = "Range entry detected"
    elif num_tps == 1:
        notes = "Single TP"
    elif num_tps == 2:
        notes = "TP3-TP4 not found"
    elif num_tps == 3:
        notes = "TP4 not found"

    return {
        "message_id": message_id,
        "channel_username": channel,
        "timestamp": timestamp,
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "entry_price_min": entry_min,
        "entry_price_max": entry_max,
        "stop_loss": stop_loss,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "take_profit_3": tp3,
        "take_profit_4": tp4,
        "confidence_score": confidence,
        "raw_message": "",
        "extraction_notes": notes,
        "extracted_at": extracted_at,
    }


def format_value(value):
    """Format a value for CSV output"""
    if value is None:
        return ""
    return str(value)


def save_signal(signal: dict, output_path: Path):
    """Save a signal to the CSV file"""
    fieldnames = [
        "message_id", "channel_username", "timestamp", "symbol", "direction",
        "entry_price", "entry_price_min", "entry_price_max", "stop_loss",
        "take_profit_1", "take_profit_2", "take_profit_3", "take_profit_4",
        "confidence_score", "raw_message", "extraction_notes", "extracted_at"
    ]

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists()

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        # Convert None values to empty strings
        row = {k: format_value(v) for k, v in signal.items()}
        writer.writerow(row)


def main():
    """Generate and save a random signal"""
    config = load_config()

    # Get output path from config
    csv_config = config.get("output", {}).get("csv", {})
    output_path = expand_path(csv_config.get("file_path", "output/signals.csv"))

    signal = generate_random_signal(config)
    save_signal(signal, output_path)

    # Print the generated signal
    print("Generated signal:")
    print(f"  Symbol:    {signal['symbol']}")
    print(f"  Direction: {signal['direction']}")
    if signal['entry_price']:
        print(f"  Entry:     {signal['entry_price']}")
    else:
        print(f"  Entry:     {signal['entry_price_min']} - {signal['entry_price_max']}")
    print(f"  SL:        {signal['stop_loss']}")
    print(f"  TP1:       {signal['take_profit_1']}")
    if signal['take_profit_2']:
        print(f"  TP2:       {signal['take_profit_2']}")
    if signal['take_profit_3']:
        print(f"  TP3:       {signal['take_profit_3']}")
    if signal['take_profit_4']:
        print(f"  TP4:       {signal['take_profit_4']}")
    print(f"  Confidence: {signal['confidence_score']}")
    print(f"  Channel:   {signal['channel_username']}")
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
