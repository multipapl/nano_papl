import unittest
from ui.tab_batch import RESOLUTION_TABLE

class TestOptimization(unittest.TestCase):
    def test_resolution_linearity(self):
        """
        Verify that 2K is exactly 2x 1K, and 4K is exactly 2x 2K
        as discovered in empirical testing.
        """
        for ratio, buckets in RESOLUTION_TABLE.items():
            with self.subTest(ratio=ratio):
                w1, h1 = buckets["1K"]
                w2, h2 = buckets["2K"]
                w4, h4 = buckets["4K"]
                
                self.assertEqual(w2, w1 * 2, f"2K Width mismatch for {ratio}")
                self.assertEqual(h2, h1 * 2, f"2K Height mismatch for {ratio}")
                self.assertEqual(w4, w2 * 2, f"4K Width mismatch for {ratio}")
                self.assertEqual(h4, h2 * 2, f"4K Height mismatch for {ratio}")

    def test_aspect_ratio_accuracy(self):
        """
        Verify that pixel dimensions roughly match the implementation ratio.
        """
        for ratio_key, buckets in RESOLUTION_TABLE.items():
            # Parse '16:9' -> 1.777
            target_w, target_h = map(int, ratio_key.split(':'))
            target_ratio = target_w / target_h
            
            # Check 1K bucket (others are multiples so ratio is same)
            w_px, h_px = buckets["1K"]
            actual_ratio = w_px / h_px
            
            # Tolerance 0.05 is safe for integer snapping
            self.assertAlmostEqual(actual_ratio, target_ratio, delta=0.05, 
                                   msg=f"Ratio deviation for {ratio_key} (Got {actual_ratio:.3f}, Expected {target_ratio:.3f})")

    def test_divisible_by_16(self):
        """
        Ensure all dimensions are at least divisible by 16 (often AI requirement, usually 64).
        """
        for ratio, buckets in RESOLUTION_TABLE.items():
            for res_name, (w, h) in buckets.items():
                self.assertTrue(w % 16 == 0, f"{ratio} {res_name} Width {w} not div by 16")
                self.assertTrue(h % 16 == 0, f"{ratio} {res_name} Height {h} not div by 16")

if __name__ == '__main__':
    unittest.main()
