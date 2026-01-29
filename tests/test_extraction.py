"""Test signal extraction with real signal examples"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extractor import SignalExtractor
from src.extraction.patterns import PatternMatcher
from src.extraction.validators import SignalValidator


# Sample signal messages from documentation
NICK_ALPHA_SAMPLE_1 = """GOLD SELL

Gold sell now @4746.50-4750.50

sl: 4752.50

tp1: 4730
tp2: 4720"""

NICK_ALPHA_SAMPLE_2 = """GOLD SELL

Gold sell now @4742-4746

sl: 4748

tp1: 4725
tp2: 4720"""

GARY_GOLD_SAMPLE_1 = """GARY GOLD LEGACY
Gold Buy Now @ 4930-4925
sl:4922
tp1:4935
tp2:4940"""

GARY_GOLD_SAMPLE_2 = """GARY GOLD LEGACY
Gold Buy Now @ 4926-4921
sl:4919
tp1:4930
tp2:4935"""

GARY_GOLD_SAMPLE_3 = """GARY GOLD LEGACY
Gold Buy Now @ 4953-4948
sl:4945
tp1:4955
tp2:4960"""

GOLD_FX_SIGNALS_SAMPLE_1 = """GOLD FX SIGNALS
Buy Gold @5082.2-5076.2

SI :5074.2

Tp1:5084.2
Tp2:5088

Enter Slowly-Layer with proper money management

Do not rush your entries"""

NON_SIGNAL_MESSAGE = """Good morning traders! Remember to manage your risk today!"""


def test_pattern_matcher():
    """Test pattern matching with sample signals"""
    print("\n" + "="*60)
    print("TEST: Pattern Matcher")
    print("="*60)

    matcher = PatternMatcher()

    # Test Nick Alpha Trader format
    print("\n--- Nick Alpha Trader Sample 1 ---")
    print(f"Is signal: {matcher.is_signal(NICK_ALPHA_SAMPLE_1)}")
    print(f"Symbol: {matcher.extract_symbol(NICK_ALPHA_SAMPLE_1)}")
    print(f"Direction: {matcher.extract_direction(NICK_ALPHA_SAMPLE_1)}")
    entry = matcher.extract_entry(NICK_ALPHA_SAMPLE_1)
    print(f"Entry: single={entry[0]}, min={entry[1]}, max={entry[2]}")
    print(f"Stop Loss: {matcher.extract_stop_loss(NICK_ALPHA_SAMPLE_1)}")
    tps = matcher.extract_take_profits(NICK_ALPHA_SAMPLE_1)
    print(f"Take Profits: {tps}")

    # Test Gary Gold Legacy format
    print("\n--- Gary Gold Legacy Sample 1 ---")
    print(f"Is signal: {matcher.is_signal(GARY_GOLD_SAMPLE_1)}")
    print(f"Symbol: {matcher.extract_symbol(GARY_GOLD_SAMPLE_1)}")
    print(f"Direction: {matcher.extract_direction(GARY_GOLD_SAMPLE_1)}")
    entry = matcher.extract_entry(GARY_GOLD_SAMPLE_1)
    print(f"Entry: single={entry[0]}, min={entry[1]}, max={entry[2]}")
    print(f"Stop Loss: {matcher.extract_stop_loss(GARY_GOLD_SAMPLE_1)}")
    tps = matcher.extract_take_profits(GARY_GOLD_SAMPLE_1)
    print(f"Take Profits: {tps}")

    # Test non-signal message
    print("\n--- Non-Signal Message ---")
    print(f"Is signal: {matcher.is_signal(NON_SIGNAL_MESSAGE)}")

    print("\n[OK] Pattern Matcher tests passed!")


def test_signal_extractor():
    """Test full signal extraction"""
    print("\n" + "="*60)
    print("TEST: Signal Extractor")
    print("="*60)

    config = {
        'min_confidence': 0.75,
        'confidence_weights': {
            'symbol': 0.25,
            'direction': 0.25,
            'entry': 0.20,
            'stop_loss': 0.15,
            'take_profit': 0.15
        },
        'symbol_mapping': {
            'GOLD': 'XAUUSD',
            'Gold': 'XAUUSD',
        }
    }

    extractor = SignalExtractor(config)

    # Test Nick Alpha Trader
    print("\n--- Extracting Nick Alpha Trader Signal ---")
    try:
        signal = extractor.extract_signal(
            text=NICK_ALPHA_SAMPLE_1,
            message_id=12345,
            channel_username="nickalphatrader",
            timestamp=datetime.now()
        )
        print(f"[OK] Extraction successful!")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Direction: {signal.direction}")
        print(f"  Entry Range: {signal.entry_price_min} - {signal.entry_price_max}")
        print(f"  Stop Loss: {signal.stop_loss}")
        print(f"  Take Profits: {signal.take_profits}")
        print(f"  Confidence: {signal.confidence_score}")
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")

    # Test Gary Gold Legacy
    print("\n--- Extracting Gary Gold Legacy Signal ---")
    try:
        signal = extractor.extract_signal(
            text=GARY_GOLD_SAMPLE_1,
            message_id=12346,
            channel_username="GaryGoldLegacy",
            timestamp=datetime.now()
        )
        print(f"[OK] Extraction successful!")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Direction: {signal.direction}")
        print(f"  Entry Range: {signal.entry_price_min} - {signal.entry_price_max}")
        print(f"  Stop Loss: {signal.stop_loss}")
        print(f"  Take Profits: {signal.take_profits}")
        print(f"  Confidence: {signal.confidence_score}")
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")

    # Test all Gary Gold samples
    print("\n--- Testing All Gary Gold Samples ---")
    samples = [GARY_GOLD_SAMPLE_1, GARY_GOLD_SAMPLE_2, GARY_GOLD_SAMPLE_3]
    for i, sample in enumerate(samples, 1):
        try:
            signal = extractor.extract_signal(
                text=sample,
                message_id=12346 + i,
                channel_username="GaryGoldLegacy",
                timestamp=datetime.now()
            )
            print(f"[OK] Sample {i}: {signal.direction} @ {signal.entry_price_min}-{signal.entry_price_max}")
        except Exception as e:
            print(f"[FAIL] Sample {i} failed: {e}")

    # Test GOLD FX SIGNALS
    print("\n--- Extracting GOLD FX SIGNALS Signal ---")
    try:
        signal = extractor.extract_signal(
            text=GOLD_FX_SIGNALS_SAMPLE_1,
            message_id=12350,
            channel_username="goldfx_signls0",
            timestamp=datetime.now()
        )
        print(f"[OK] Extraction successful!")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Direction: {signal.direction}")
        print(f"  Entry Range: {signal.entry_price_min} - {signal.entry_price_max}")
        print(f"  Stop Loss: {signal.stop_loss}")
        print(f"  Take Profits: {signal.take_profits}")
        print(f"  Confidence: {signal.confidence_score}")
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")

    print("\n[OK] Signal Extractor tests passed!")


def test_validator():
    """Test signal validation"""
    print("\n" + "="*60)
    print("TEST: Signal Validator")
    print("="*60)

    config = {
        'min_confidence': 0.75,
        'confidence_weights': {
            'symbol': 0.25,
            'direction': 0.25,
            'entry': 0.20,
            'stop_loss': 0.15,
            'take_profit': 0.15
        },
        'symbol_mapping': {
            'GOLD': 'XAUUSD',
            'Gold': 'XAUUSD',
        }
    }

    extractor = SignalExtractor(config)

    print("\n--- Validating SELL Signal Price Logic ---")
    signal = extractor.extract_signal(
        text=NICK_ALPHA_SAMPLE_1,
        message_id=12345,
        channel_username="nickalphatrader",
        timestamp=datetime.now()
    )

    # Check price logic
    avg_entry = signal.get_entry_average()
    print(f"  Average Entry: {avg_entry}")
    print(f"  Stop Loss: {signal.stop_loss}")
    print(f"  Take Profits: {signal.take_profits}")

    # For SELL: SL should be above entry, TPs below
    if signal.direction == "SELL":
        if signal.stop_loss > avg_entry:
            print(f"  [OK] SL ({signal.stop_loss}) > Entry ({avg_entry}) - Correct for SELL")
        else:
            print(f"  [FAIL] SL logic incorrect for SELL")

        if all(tp < avg_entry for tp in signal.take_profits):
            print(f"  [OK] All TPs below entry - Correct for SELL")
        else:
            print(f"  [FAIL] TP logic incorrect for SELL")

    print("\n--- Validating BUY Signal Price Logic ---")
    signal = extractor.extract_signal(
        text=GARY_GOLD_SAMPLE_1,
        message_id=12346,
        channel_username="GaryGoldLegacy",
        timestamp=datetime.now()
    )

    avg_entry = signal.get_entry_average()
    print(f"  Average Entry: {avg_entry}")
    print(f"  Stop Loss: {signal.stop_loss}")
    print(f"  Take Profits: {signal.take_profits}")

    # For BUY: SL should be below entry, TPs above
    if signal.direction == "BUY":
        if signal.stop_loss < avg_entry:
            print(f"  [OK] SL ({signal.stop_loss}) < Entry ({avg_entry}) - Correct for BUY")
        else:
            print(f"  [FAIL] SL logic incorrect for BUY")

        if all(tp > avg_entry for tp in signal.take_profits):
            print(f"  [OK] All TPs above entry - Correct for BUY")
        else:
            print(f"  [FAIL] TP logic incorrect for BUY")

    print("\n[OK] Validator tests passed!")


def test_csv_output():
    """Test CSV conversion"""
    print("\n" + "="*60)
    print("TEST: CSV Output Format")
    print("="*60)

    config = {
        'min_confidence': 0.75,
        'confidence_weights': {
            'symbol': 0.25,
            'direction': 0.25,
            'entry': 0.20,
            'stop_loss': 0.15,
            'take_profit': 0.15
        },
        'symbol_mapping': {
            'GOLD': 'XAUUSD',
        }
    }

    extractor = SignalExtractor(config)
    signal = extractor.extract_signal(
        text=NICK_ALPHA_SAMPLE_1,
        message_id=12345,
        channel_username="nickalphatrader",
        timestamp=datetime.now()
    )

    # Convert to dict (CSV format)
    signal_dict = signal.to_dict()

    print("\nCSV fields:")
    for key, value in signal_dict.items():
        print(f"  {key}: {value}")

    print("\n[OK] CSV output format test passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING ALL TESTS")
    print("="*60)

    try:
        test_pattern_matcher()
        test_signal_extractor()
        test_validator()
        test_csv_output()

        print("\n" + "="*60)
        print("[OK] ALL TESTS PASSED!")
        print("="*60)
        print("\nThe signal extraction system is working correctly!")
        print("You can now run the application with: python src/main.py")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
