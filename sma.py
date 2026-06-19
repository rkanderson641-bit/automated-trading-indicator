def calculate_sma(prices, window):
    """Return the simple moving average series for the given window size."""
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if window > len(prices):
        return []

    sma_values = []
    for i in range(window - 1, len(prices)):
        chunk = prices[i - window + 1:i + 1]
        sma_values.append(sum(chunk) / window)
    return sma_values
