"""Quick test for is_signal and signal extraction"""
from datetime import datetime
from src.extraction.extractor import SignalExtractor

# Test text
test_text = """GARY GOLD LEGACY
Gold Buy Now @ 5092-5087

sl:5085

tp1:5100
tp2:5105"""

# Initialize extractor with default config
config = {
    'min_confidence': 0.75,
    'symbol_mapping': {
        'GOLD': 'XAUUSD',
        'Gold': 'XAUUSD',
    },
    'confidence_weights': {
        'symbol': 0.25,
        'direction': 0.25,
        'entry': 0.20,
        'stop_loss': 0.15,
        'take_profit': 0.15
    }
}

extractor = SignalExtractor(config)

# Test is_signal
print("=" * 60)
print("Testing is_signal()")
print("=" * 60)
print(f"Text:\n{test_text}\n")
print(f"is_signal() result: {extractor.is_signal(test_text)}")
print()

# Test full extraction
print("=" * 60)
print("Testing extract_signal()")
print("=" * 60)
try:
    signal = extractor.extract_signal(
        text=test_text,
        message_id=12345,
        channel_username="test_channel",
        timestamp=datetime.now()
    )

    print(f"[SUCCESS] Signal extracted successfully!")
    print(f"\nSignal Details:")
    print(f"  Symbol: {signal.symbol}")
    print(f"  Direction: {signal.direction}")
    print(f"  Entry Price: {signal.entry_price}")
    print(f"  Entry Range: {signal.entry_price_min} - {signal.entry_price_max}")
    print(f"  Stop Loss: {signal.stop_loss}")
    print(f"  Take Profits: {signal.take_profits}")
    print(f"  Confidence Score: {signal.confidence_score:.2f}")
    if signal.extraction_notes:
        print(f"  Notes: {signal.extraction_notes}")

except ValueError as e:
    print(f"[FAILED] Extraction failed: {e}")

print()
