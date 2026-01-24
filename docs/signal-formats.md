# Signal Format Analysis

This document captures the actual signal formats observed from the target Telegram channels to inform extraction pattern development.

## 1. Nick Alpha Trader Channel

### 1.1 Format Analysis (Based on Screenshots)

**Channel**: @nickalphatrader

#### Example 1:
```
GOLD SELL

Gold sell now @4746.50-4750.50

sl: 4752.50

tp1: 4730
tp2: 4720
```

#### Example 2:
```
GOLD SELL

Gold sell now @4742-4746

sl: 4748

tp1: 4725
tp2: 4720
```

### 1.2 Pattern Observations

| Element | Pattern | Notes |
|---------|---------|-------|
| **Symbol** | Text in graphic + message | "GOLD" appears in both image and text |
| **Direction** | "SELL" or "BUY" | In graphic and text ("sell now") |
| **Entry** | `@[price1]-[price2]` | Range format, uses @ symbol |
| **Entry Format** | Both decimal and integer | Sometimes 4746.50, sometimes 4742 |
| **Stop Loss** | `sl: [price]` | Lowercase "sl" with colon |
| **Take Profit** | `tp1: [price]`, `tp2: [price]` | Numbered tp1, tp2, etc. |
| **Spacing** | Line breaks between elements | Each element on new line |

### 1.3 Extraction Rules for Nick Alpha Trader

#### Symbol Extraction
```regex
Pattern: \b(GOLD|EUR\/?USD|GBP\/?USD|XAU\/?USD|BTC\/?USD|[A-Z]{3}\/?[A-Z]{3})\b
Case: Case-insensitive
Priority: First match in message
```

#### Direction Extraction
```regex
Pattern: \b(BUY|SELL)\b
Case: Case-insensitive
Context: Look for "buy now" or "sell now" phrases
```

#### Entry Price Extraction
```regex
Pattern 1 (Range): @(\d+\.?\d*)-(\d+\.?\d*)
  Captures: entry_min and entry_max
  Example: @4746.50-4750.50 → min=4746.50, max=4750.50

Pattern 2 (Single): @(\d+\.?\d*)(?!-)
  Captures: entry_price
  Example: @4746.50 → entry=4746.50
```

#### Stop Loss Extraction
```regex
Pattern: (?:sl|stop\s*loss|stop):\s*(\d+\.?\d*)
Case: Case-insensitive
Captures: 4752.50 from "sl: 4752.50"
```

#### Take Profit Extraction
```regex
Pattern: tp(\d+):\s*(\d+\.?\d*)
Case: Case-insensitive
Captures: TP number and price
Example: "tp1: 4730" → tp_num=1, price=4730
```

### 1.4 Special Considerations

1. **Price Precision**: Supports both integer (4742) and decimal (4746.50) formats
2. **Range Entries**: Always uses dash separator between prices
3. **Ordering**: Signal elements appear in consistent order (symbol/direction → entry → sl → tps)
4. **Graphics**: Images contain symbol and direction but extraction should focus on text

## 2. Gary Gold Legacy Channel

### 2.1 Format Analysis (Based on Screenshots)

**Channel**: @GaryGoldLegacy

#### Example 1:
```
GARY GOLD LEGACY
Gold Buy Now @ 4930-4925
sl:4922
tp1:4935
tp2:4940
```

#### Example 2:
```
GARY GOLD LEGACY
Gold Buy Now @ 4926-4921
sl:4919
tp1:4930
tp2:4935
```

#### Example 3:
```
GARY GOLD LEGACY
Gold Buy Now @ 4953-4948
sl:4945
tp1:4955
tp2:4960
```

### 2.2 Pattern Observations

| Element | Pattern | Notes |
|---------|---------|-------|
| **Symbol** | "Gold" in message | Always GOLD signals |
| **Direction** | "Buy Now" or "Sell Now" | Capitalized format |
| **Entry** | `@ [price1]-[price2]` | Range format, @ symbol, space after @ |
| **Entry Format** | Integer prices only | No decimals observed (4930, 4925) |
| **Stop Loss** | `sl:[price]` | Lowercase "sl" with colon, **NO space** after colon |
| **Take Profit** | `tp1:[price]`, `tp2:[price]` | Lowercase, numbered, **NO space** after colon |
| **Spacing** | Minimal line breaks | More compact than Nick Alpha Trader |
| **Entry Range** | Higher-to-lower or lower-to-higher | Order varies, represents entry zone |

### 2.3 Key Differences from Nick Alpha Trader

| Feature | Nick Alpha Trader | Gary Gold Legacy |
|---------|-------------------|------------------|
| Direction format | "sell now" (lowercase) | "Buy Now" (capitalized) |
| SL/TP spacing | `sl: 4752` (space after colon) | `sl:4922` (no space) |
| Entry spacing | `@4746-4750` (no space) | `@ 4930-4925` (space after @) |
| Price format | Decimals common (4746.50) | Integers only (4930) |
| Layout | Line breaks between elements | Compact format |

### 2.4 Extraction Rules for Gary Gold Legacy

#### Symbol Extraction
```regex
Pattern: \b(GOLD|Gold)\b
Case: Case-insensitive
Note: All observed signals are GOLD/XAUUSD
```

#### Direction Extraction
```regex
Pattern 1 (Capitalized): (Buy|Sell)\s+Now
Pattern 2 (Fallback): \b(BUY|SELL)\b
Case: Case-insensitive
Context: Look for "Buy Now" or "Sell Now" phrases
```

#### Entry Price Extraction
```regex
Pattern: @\s*(\d+\.?\d*)-(\d+\.?\d*)
  Captures: entry_min and entry_max
  Example: @ 4930-4925 → captures 4930 and 4925
  Note: Space after @ is optional, order may vary
  Processing: Normalize to min/max (min = smaller value, max = larger value)
```

#### Stop Loss Extraction
```regex
Pattern: sl:\s*(\d+\.?\d*)
Case: Case-insensitive
Note: No space after colon in typical format, but pattern allows optional space
Captures: 4922 from "sl:4922"
```

#### Take Profit Extraction
```regex
Pattern: tp(\d+):\s*(\d+\.?\d*)
Case: Case-insensitive
Note: No space after colon in typical format, but pattern allows optional space
Captures: TP number and price
Example: "tp1:4935" → tp_num=1, price=4935
```

### 2.5 Special Considerations

1. **Entry Range Normalization**: Range may be written in either order (4930-4925 or 4925-4930)
   - Always normalize to min/max regardless of order
   - Use `min(price1, price2)` and `max(price1, price2)`

2. **Integer Prices**: No decimal points observed, but extraction should support both

3. **Compact Format**: Less whitespace than Nick Alpha Trader, all info on consecutive lines

4. **Consistent Structure**: Very consistent format across all samples

## 3. Common Pattern Variations Across Channels

### 3.1 Symbol Notations

| Variation | Normalized | Examples |
|-----------|-----------|----------|
| GOLD | XAUUSD | GOLD, Gold, gold |
| XAU/USD | XAUUSD | XAU/USD, XAUUSD, XAU-USD |
| EUR/USD | EURUSD | EUR/USD, EURUSD, EUR-USD, EURO |
| BTC/USD | BTCUSD | BTC/USD, BITCOIN, BTC |

### 3.2 Direction Keywords

| Buy Signals | Sell Signals |
|-------------|--------------|
| BUY | SELL |
| Buy now | Sell now |
| LONG | SHORT |
| Go long | Go short |
| Buy limit | Sell limit |

### 3.3 Entry Price Formats

```
Format Type              Example                    Pattern
─────────────────────────────────────────────────────────────
Single price             @4746.50                   @(\d+\.?\d*)
Range with dash          @4746-4750                 @(\d+)-(\d+)
Range with "to"          Entry: 4746 to 4750        (\d+\.?\d*)\s*to\s*(\d+\.?\d*)
Range with "or"          4746 or better             (\d+\.?\d*)\s*or\s*better
Zone                     Entry zone: 4746-4750      zone:\s*(\d+)-(\d+)
```

### 3.4 Stop Loss Formats

```
Format                   Example                    Pattern
─────────────────────────────────────────────────────────────
sl: price                sl: 4752.50               sl:\s*(\d+\.?\d*)
SL: price                SL: 4752.50               sl:\s*(\d+\.?\d*)
Stop Loss: price         Stop Loss: 4752.50        stop\s*loss:\s*(\d+\.?\d*)
Stop: price              Stop: 4752.50             stop:\s*(\d+\.?\d*)
Stop @ price             Stop @ 4752.50            stop\s*@\s*(\d+\.?\d*)
SL @ price               SL @ 4752.50              sl\s*@\s*(\d+\.?\d*)
```

### 3.5 Take Profit Formats

```
Format                   Example                    Pattern
─────────────────────────────────────────────────────────────
tp1: price               tp1: 4730                 tp(\d+):\s*(\d+\.?\d*)
TP1: price               TP1: 4730                 tp(\d+):\s*(\d+\.?\d*)
Target 1: price          Target 1: 4730            target\s*(\d+):\s*(\d+\.?\d*)
T1: price                T1: 4730                  t(\d+):\s*(\d+\.?\d*)
Take profit 1: price     Take profit 1: 4730       take\s*profit\s*(\d+):\s*(\d+\.?\d*)
Multiple on one line     TP: 4730, 4720, 4710      tp:\s*([\d.,\s]+)
```

## 4. Extraction Strategy

### 4.1 Multi-Pattern Approach

For each field, try patterns in order of specificity:

```python
SYMBOL_PATTERNS = [
    r'\b(GOLD|XAUUSD|XAU/USD)\b',           # Specific metals
    r'\b([A-Z]{3}/[A-Z]{3})\b',             # Slash notation
    r'\b([A-Z]{6})\b',                      # 6-letter pairs
    # ... more patterns
]

def extract_symbol(text):
    for pattern in SYMBOL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return normalize_symbol(match.group(1))
    return None
```

### 4.2 Confidence Scoring

Assign confidence based on extraction success:

```python
def calculate_confidence(extracted_fields):
    score = 0.0
    weights = {
        'symbol': 0.25,
        'direction': 0.25,
        'entry': 0.20,
        'stop_loss': 0.15,
        'take_profit': 0.15
    }

    if extracted_fields.get('symbol'):
        score += weights['symbol']
    if extracted_fields.get('direction'):
        score += weights['direction']
    if extracted_fields.get('entry') or (
        extracted_fields.get('entry_min') and
        extracted_fields.get('entry_max')
    ):
        score += weights['entry']
    if extracted_fields.get('stop_loss'):
        score += weights['stop_loss']
    if extracted_fields.get('take_profits'):
        score += weights['take_profit']

    return score
```

### 4.3 Validation Rules

After extraction, validate logical consistency:

```python
def validate_signal(signal):
    """Validate extracted signal makes trading sense"""

    # 1. Required fields present
    if not all([signal.symbol, signal.direction]):
        raise ValidationError("Missing required fields")

    # 2. Price logic for BUY signals
    if signal.direction == "BUY":
        if signal.stop_loss and signal.entry_price:
            if signal.stop_loss >= signal.entry_price:
                raise ValidationError("BUY: SL should be below entry")

        if signal.take_profits and signal.entry_price:
            if any(tp <= signal.entry_price for tp in signal.take_profits):
                raise ValidationError("BUY: TP should be above entry")

    # 3. Price logic for SELL signals
    if signal.direction == "SELL":
        if signal.stop_loss and signal.entry_price:
            if signal.stop_loss <= signal.entry_price:
                raise ValidationError("SELL: SL should be above entry")

        if signal.take_profits and signal.entry_price:
            if any(tp >= signal.entry_price for tp in signal.take_profits):
                raise ValidationError("SELL: TP should be below entry")

    # 4. Range entry validation
    if signal.entry_min and signal.entry_max:
        if signal.entry_min >= signal.entry_max:
            raise ValidationError("Entry min should be less than max")

    return True
```

## 5. Test Cases

### 5.1 Nick Alpha Trader Test Cases

#### Test Case 1: Standard GOLD SELL
```
Input:
---
GOLD SELL

Gold sell now @4746.50-4750.50

sl: 4752.50

tp1: 4730
tp2: 4720
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "SELL",
    "entry_min": 4746.50,
    "entry_max": 4750.50,
    "stop_loss": 4752.50,
    "take_profits": [4730, 4720],
    "confidence": 1.0
}
```

#### Test Case 2: Integer Prices
```
Input:
---
GOLD SELL

Gold sell now @4742-4746

sl: 4748

tp1: 4725
tp2: 4720
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "SELL",
    "entry_min": 4742,
    "entry_max": 4746,
    "stop_loss": 4748,
    "take_profits": [4725, 4720],
    "confidence": 1.0
}
```

#### Test Case 3: BUY Signal (Hypothetical)
```
Input:
---
GOLD BUY

Gold buy now @4740-4745

sl: 4730

tp1: 4755
tp2: 4760
tp3: 4765
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_min": 4740,
    "entry_max": 4745,
    "stop_loss": 4730,
    "take_profits": [4755, 4760, 4765],
    "confidence": 1.0
}
```

### 5.2 Gary Gold Legacy Test Cases

#### Test Case 1: Standard BUY Signal
```
Input:
---
GARY GOLD LEGACY
Gold Buy Now @ 4930-4925
sl:4922
tp1:4935
tp2:4940
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_min": 4925,
    "entry_max": 4930,
    "stop_loss": 4922,
    "take_profits": [4935, 4940],
    "confidence": 1.0
}
```

#### Test Case 2: Range Order Normalization
```
Input:
---
GARY GOLD LEGACY
Gold Buy Now @ 4926-4921
sl:4919
tp1:4930
tp2:4935
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_min": 4921,  # Normalized: min(4926, 4921)
    "entry_max": 4926,  # Normalized: max(4926, 4921)
    "stop_loss": 4919,
    "take_profits": [4930, 4935],
    "confidence": 1.0
}
```

#### Test Case 3: SELL Signal (Hypothetical)
```
Input:
---
GARY GOLD LEGACY
Gold Sell Now @ 4950-4955
sl:4958
tp1:4940
tp2:4935
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "SELL",
    "entry_min": 4950,
    "entry_max": 4955,
    "stop_loss": 4958,
    "take_profits": [4940, 4935],
    "confidence": 1.0
}
```

### 5.3 Edge Cases

#### Edge Case 1: Missing TP2
```
Input:
---
Gold sell now @4746-4750
sl: 4752
tp1: 4730
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "SELL",
    "entry_min": 4746,
    "entry_max": 4750,
    "stop_loss": 4752,
    "take_profits": [4730],
    "confidence": 0.90,
    "notes": "Only 1 TP found"
}
```

#### Edge Case 2: Single Entry Price
```
Input:
---
GOLD SELL @4746
SL: 4752
TP1: 4730
TP2: 4720
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "SELL",
    "entry_price": 4746,
    "stop_loss": 4752,
    "take_profits": [4730, 4720],
    "confidence": 0.95
}
```

#### Edge Case 3: No Stop Loss
```
Input:
---
Gold buy now @4740
tp1: 4755
tp2: 4760
---

Expected Output:
{
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_price": 4740,
    "take_profits": [4755, 4760],
    "confidence": 0.75,
    "notes": "No stop loss provided"
}
```

#### Edge Case 4: Non-Signal Message
```
Input:
---
Good morning traders! Remember to manage your risk today!
---

Expected Output:
Should not be identified as signal (is_signal() returns False)
```

## 6. Implementation Recommendations

### 6.1 Pattern Priority

1. **Start with most specific patterns** (exact formats from screenshots)
2. **Add fallback patterns** for variations
3. **Log pattern matches** to improve accuracy over time

### 6.2 Iterative Improvement

```python
class PatternLearner:
    """Track which patterns match most often"""

    def __init__(self):
        self.pattern_stats = {}

    def record_match(self, field, pattern_id, success):
        if pattern_id not in self.pattern_stats:
            self.pattern_stats[pattern_id] = {'matches': 0, 'total': 0}

        self.pattern_stats[pattern_id]['total'] += 1
        if success:
            self.pattern_stats[pattern_id]['matches'] += 1

    def get_pattern_accuracy(self, pattern_id):
        stats = self.pattern_stats.get(pattern_id)
        if not stats or stats['total'] == 0:
            return 0.0
        return stats['matches'] / stats['total']
```

### 6.3 Channel-Specific Overrides

Allow configuration of channel-specific patterns:

```yaml
channels:
  - username: "nickalphatrader"
    patterns:
      entry: '@(\d+\.?\d*)-(\d+\.?\d*)'  # Always range format
      sl_prefix: 'sl:'                    # Lowercase sl
      tp_prefix: 'tp'                     # Lowercase tp

  - username: "GaryGoldLegacy"
    patterns:
      entry: 'Entry:?\s*(\d+\.?\d*)'     # May differ
      sl_prefix: 'Stop Loss:'
      tp_prefix: 'Target'
```

## 7. Next Steps

1. **Collect more samples** from both channels (1-2 weeks of messages)
2. **Document Gary Gold Legacy format** once samples available
3. **Build test corpus** with 20-30 real messages
4. **Implement extraction engine** with patterns above
5. **Test and refine** patterns based on accuracy metrics

## 8. Monitoring and Metrics

Track extraction performance:

```
Metrics to Monitor:
- Extraction success rate (target: >95%)
- Confidence score distribution
- Pattern match rates per field
- False positive rate (non-signals identified as signals)
- False negative rate (signals missed)
- Per-channel extraction accuracy
```

## Appendix: Regex Pattern Reference

### Complete Pattern Set for Nick Alpha Trader

```python
NICK_ALPHA_PATTERNS = {
    'symbol': [
        r'\b(GOLD)\b',
        r'\b(XAU/?USD)\b',
        r'\b([A-Z]{3}/?[A-Z]{3})\b',
    ],

    'direction': [
        r'\b(BUY|SELL)\s+now\b',
        r'\b(BUY|SELL)\b',
    ],

    'entry_range': [
        r'@(\d+\.?\d*)-(\d+\.?\d*)',
    ],

    'entry_single': [
        r'@(\d+\.?\d*)(?!-)',
    ],

    'stop_loss': [
        r'sl:\s*(\d+\.?\d*)',
        r'stop\s*loss:\s*(\d+\.?\d*)',
        r'stop:\s*(\d+\.?\d*)',
    ],

    'take_profit': [
        r'tp(\d+):\s*(\d+\.?\d*)',
        r'target\s*(\d+):\s*(\d+\.?\d*)',
    ]
}
```

### Complete Pattern Set for Gary Gold Legacy

```python
GARY_GOLD_PATTERNS = {
    'symbol': [
        r'\b(GOLD|Gold)\b',
        r'\b(XAU/?USD)\b',
    ],

    'direction': [
        r'\b(Buy|Sell)\s+Now\b',  # Capitalized format
        r'\b(BUY|SELL)\s+now\b',  # Fallback
        r'\b(BUY|SELL)\b',        # Generic fallback
    ],

    'entry_range': [
        r'@\s*(\d+\.?\d*)-(\d+\.?\d*)',  # Note: space after @ is optional
    ],

    'stop_loss': [
        r'sl:\s*(\d+\.?\d*)',
        r'stop\s*loss:\s*(\d+\.?\d*)',
    ],

    'take_profit': [
        r'tp(\d+):\s*(\d+\.?\d*)',
    ]
}
```

### Unified Pattern Set (Recommended)

For a system that handles both channels, use a unified pattern set that covers both formats:

```python
UNIFIED_PATTERNS = {
    'symbol': [
        r'\b(GOLD|Gold)\b',
        r'\b(XAU/?USD)\b',
        r'\b([A-Z]{3}/?[A-Z]{3})\b',
    ],

    'direction': [
        r'\b(Buy|Sell)\s+Now\b',      # Gary Gold format
        r'\b(BUY|SELL)\s+now\b',      # Nick Alpha format
        r'\b(BUY|SELL)\b',            # Generic fallback
    ],

    'entry_range': [
        r'@\s*(\d+\.?\d*)-(\d+\.?\d*)',  # Handles both with/without space
    ],

    'entry_single': [
        r'@\s*(\d+\.?\d*)(?!-)',
    ],

    'stop_loss': [
        r'sl:\s*(\d+\.?\d*)',         # Handles both with/without space
        r'stop\s*loss:\s*(\d+\.?\d*)',
        r'stop:\s*(\d+\.?\d*)',
    ],

    'take_profit': [
        r'tp(\d+):\s*(\d+\.?\d*)',    # Handles both with/without space
        r'target\s*(\d+):\s*(\d+\.?\d*)',
    ]
}

# Helper function for entry range normalization
def normalize_entry_range(price1, price2):
    """Normalize entry range to min/max regardless of order"""
    return {
        'entry_min': min(price1, price2),
        'entry_max': max(price1, price2)
    }
```
