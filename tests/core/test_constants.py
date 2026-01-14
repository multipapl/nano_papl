import pytest
from core.config.resolutions import RESOLUTION_TABLE

def test_resolution_linearity():
    """Verify that resolution buckets are proportional (1K -> 2K -> 4K)."""
    for ratio, buckets in RESOLUTION_TABLE.items():
        w1, h1 = buckets["1K"]
        w2, h2 = buckets["2K"]
        w4, h4 = buckets["4K"]
        
        assert w2 == w1 * 2, f"2K Width mismatch for {ratio}"
        assert h2 == h1 * 2, f"2K Height mismatch for {ratio}"
        assert w4 == w2 * 2, f"4K Width mismatch for {ratio}"
        assert h4 == h2 * 2, f"4K Height mismatch for {ratio}"

def test_aspect_ratio_accuracy():
    """Verify that pixel dimensions match the target aspect ratio."""
    for ratio_key, buckets in RESOLUTION_TABLE.items():
        # Parse '16:9' -> 1.777
        try:
            target_w, target_h = map(int, ratio_key.split(':'))
            target_ratio = target_w / target_h
            
            w_px, h_px = buckets["1K"]
            actual_ratio = w_px / h_px
            
            # Tolerance 0.05 for integer snapping
            assert actual_ratio == pytest.approx(target_ratio, abs=0.05), f"Ratio deviation for {ratio_key}"
        except ValueError:
            continue

def test_divisible_by_16():
    """Ensure all AI-facing dimensions are divisible by 16 for compatibility."""
    for ratio, buckets in RESOLUTION_TABLE.items():
        for res_name, (w, h) in buckets.items():
            assert w % 16 == 0, f"{ratio} {res_name} Width {w} not div by 16"
            assert h % 16 == 0, f"{ratio} {res_name} Height {h} not div by 16"
