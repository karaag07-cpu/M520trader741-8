import os
import unittest
from unittest.mock import patch

from config.config_loader import _expand_env_vars, load_config


class TestConfigEnvExpansion(unittest.TestCase):
    def test_expands_known_var(self):
        with patch.dict(os.environ, {'ALPACA_API_KEY': 'pk_live_123'}):
            out = _expand_env_vars({'exchanges': {'alpaca': {'api_key': '${ALPACA_API_KEY}'}}})
        self.assertEqual(out['exchanges']['alpaca']['api_key'], 'pk_live_123')

    def test_unset_var_becomes_empty_string(self):
        with patch.dict(os.environ, {}, clear=True):
            out = _expand_env_vars({'api_key': '${NOPE_MISSING}'})
        # Empty (falsy) so `if cfg.get('api_key')` treats it as absent.
        self.assertEqual(out['api_key'], '')
        self.assertFalse(out['api_key'])

    def test_expands_inside_lists_and_nested(self):
        with patch.dict(os.environ, {'A': '1', 'B': '2'}):
            out = _expand_env_vars({'k': ['${A}', {'inner': '${B}'}]})
        self.assertEqual(out['k'], ['1', {'inner': '2'}])

    def test_non_placeholder_strings_untouched(self):
        out = _expand_env_vars({'a': 'plain', 'b': 3, 'c': True})
        self.assertEqual(out, {'a': 'plain', 'b': 3, 'c': True})

    def test_load_config_expands_real_settings_file(self):
        with patch.dict(os.environ, {'ALPACA_API_KEY': 'k1', 'ALPACA_API_SECRET': 's1'}):
            cfg = load_config()  # co-located settings.yaml
        alpaca = cfg['exchanges']['alpaca']
        self.assertEqual(alpaca['api_key'], 'k1')
        self.assertEqual(alpaca['api_secret'], 's1')
        # An unset provider key resolves to empty, not a literal "${...}".
        self.assertNotIn('${', alpaca['api_key'])


if __name__ == '__main__':
    unittest.main()
