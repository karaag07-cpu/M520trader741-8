import unittest

from data.macro_features import derive_macro_params


class TestMacroFeatures(unittest.TestCase):
    def test_empty_input_returns_neutral_defaults(self):
        params = derive_macro_params({})
        self.assertEqual(params['yc_spread'], 1.0)
        self.assertEqual(params['inflation_yoy'], 2.0)
        self.assertEqual(params['fed_rate_trend'], 'Stable')
        self.assertEqual(params['unrate_trend'], 'Stable')

    def test_yield_curve_uses_latest_value(self):
        params = derive_macro_params({'T10Y2Y': [0.8, 0.3, -0.2]})
        self.assertAlmostEqual(params['yc_spread'], -0.2)

    def test_inflation_computed_as_year_over_year_percent(self):
        # 13 monthly CPI points: index rises 300 -> 315 over 12 months = +5%.
        cpi = [300.0, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 315.0]
        params = derive_macro_params({'CPIAUCSL': cpi})
        self.assertAlmostEqual(params['inflation_yoy'], (315.0 / 300.0 - 1) * 100)

    def test_raw_cpi_index_not_treated_as_inflation(self):
        # A single raw index level must NOT leak through as "inflation".
        params = derive_macro_params({'CPIAUCSL': 312.0})
        self.assertEqual(params['inflation_yoy'], 2.0)  # falls back to neutral

    def test_insufficient_cpi_history_falls_back(self):
        params = derive_macro_params({'CPIAUCSL': [300.0, 305.0]})  # < 13 points
        self.assertEqual(params['inflation_yoy'], 2.0)

    def test_fed_rate_trend_rising_and_falling(self):
        rising = derive_macro_params({'FEDFUNDS': [4.0, 4.25, 4.5, 4.75]})
        self.assertEqual(rising['fed_rate_trend'], 'Rising')
        falling = derive_macro_params({'FEDFUNDS': [5.0, 4.75, 4.5, 4.0]})
        self.assertEqual(falling['fed_rate_trend'], 'Falling')

    def test_fed_rate_trend_stable_within_deadband(self):
        params = derive_macro_params({'FEDFUNDS': [4.50, 4.51, 4.50, 4.52]})
        self.assertEqual(params['fed_rate_trend'], 'Stable')

    def test_scalar_value_accepted(self):
        params = derive_macro_params({'T10Y2Y': -0.5})
        self.assertAlmostEqual(params['yc_spread'], -0.5)

    def test_derived_params_drive_expected_regime(self):
        # An inverted curve should map to the Deflationary Bust regime downstream.
        from signals.macro_regime import MacroRegimeStrategy
        params = derive_macro_params({'T10Y2Y': [0.2, -0.3]})
        sig = MacroRegimeStrategy().generate_signal(None, **params)
        self.assertEqual(sig.metadata['regime'], 'Deflationary Bust')
        self.assertEqual(sig.metadata['position_size_modifier'], 0.0)


if __name__ == '__main__':
    unittest.main()
