"""Configuration precedence and validation (SPEC section 18.1, section 20)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from somnus import config
from somnus.config import ConfigError


class ConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.work = self.tmp / "work"
        self.nested = self.work / "a" / "b"
        self.nested.mkdir(parents=True)
        self._saved = os.environ.get("SOMNUS_HOME")
        os.environ["SOMNUS_HOME"] = str(self.home)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("SOMNUS_HOME", None)
        else:
            os.environ["SOMNUS_HOME"] = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def global_cfg(self, text: str) -> Path:
        return self.write(self.home / "config.toml", text)

    def local_cfg(self, text: str, where: Path | None = None) -> Path:
        return self.write((where or self.work) / ".somnus.toml", text)


class TestPrecedence(ConfigTestCase):
    def test_builtin_defaults(self) -> None:
        cfg = config.load(self.nested)
        self.assertEqual(cfg.actor, "operator")
        self.assertEqual(cfg.defaults, config.BUILTIN["defaults"])
        self.assertEqual(cfg.sources, [])
        self.assertEqual(cfg.roots, [self.nested])
        self.assertEqual(cfg.exclude, config.BUILTIN["index"]["exclude"])

    def test_builtins_are_not_mutated(self) -> None:
        self.global_cfg('[defaults]\nrole = "informative"\n')
        config.load(self.nested)
        self.assertEqual(config.BUILTIN["defaults"]["role"], "normative")

    def test_global_overrides_builtin(self) -> None:
        self.global_cfg('actor = "global"\n[defaults]\nrole = "informative"\n')
        cfg = config.load(self.nested)
        self.assertEqual(cfg.actor, "global")
        self.assertEqual(cfg.defaults["role"], "informative")
        self.assertEqual(cfg.defaults["category"], "engineering")
        self.assertEqual(cfg.sources, [self.home / "config.toml"])

    def test_local_overrides_global(self) -> None:
        self.global_cfg('actor = "global"\n[defaults]\nrole = "informative"\nscope = "module"\n')
        local = self.local_cfg('actor = "local"\n[defaults]\nscope = "repository"\n')
        cfg = config.load(self.nested)
        self.assertEqual(cfg.actor, "local")
        self.assertEqual(cfg.defaults["scope"], "repository")
        self.assertEqual(cfg.defaults["role"], "informative")
        self.assertEqual(cfg.sources, [self.home / "config.toml", local])

    def test_cli_actor_overrides_everything(self) -> None:
        self.global_cfg('actor = "global"\n')
        self.local_cfg('actor = "local"\n')
        self.assertEqual(config.load(self.nested, actor="cli").actor, "cli")

    def test_cli_actor_over_builtin(self) -> None:
        self.assertEqual(config.load(self.nested, actor="cli").actor, "cli")

    def test_nearest_local_config_wins(self) -> None:
        self.local_cfg('actor = "outer"\n')
        inner = self.local_cfg('actor = "inner"\n', self.work / "a")
        cfg = config.load(self.nested)
        self.assertEqual(cfg.actor, "inner")
        self.assertIn(inner, cfg.sources)
        self.assertNotIn(self.work / ".somnus.toml", cfg.sources)

    def test_find_local_config(self) -> None:
        self.assertIsNone(config.find_local_config(self.nested))
        local = self.local_cfg('actor = "x"\n')
        self.assertEqual(config.find_local_config(self.nested), local)
        f = self.write(self.nested / "doc.md", "x\n")
        self.assertEqual(config.find_local_config(f), local)
        self.assertEqual(config.find_local_config(self.work), local)

    def test_start_file_uses_parent_as_root(self) -> None:
        f = self.write(self.nested / "doc.md", "x\n")
        self.assertEqual(config.load(f).roots, [self.nested])


class TestRoots(ConfigTestCase):
    def test_roots_relative_to_local_config(self) -> None:
        self.local_cfg('[index]\nroots = ["src", "../other", "."]\n')
        cfg = config.load(self.nested)
        self.assertEqual(cfg.roots, [(self.work / "src").resolve(), (self.tmp / "other").resolve(), self.work])

    def test_roots_relative_to_global_config(self) -> None:
        self.global_cfg('[index]\nroots = ["library"]\n')
        self.assertEqual(config.load(self.nested).roots, [self.home / "library"])

    def test_empty_roots_keep_start(self) -> None:
        self.global_cfg('[index]\nroots = []\n')
        self.assertEqual(config.load(self.nested).roots, [self.nested])

    def test_exclude_replaced(self) -> None:
        self.local_cfg('[index]\nexclude = ["build/**"]\n')
        self.assertEqual(config.load(self.nested).exclude, ["build/**"])

    def test_db_path_and_home(self) -> None:
        cfg = config.load(self.nested)
        self.assertEqual(cfg.home, self.home)
        self.assertEqual(cfg.db_path, self.home / "somnus.db")

    def test_somnus_home_default(self) -> None:
        os.environ.pop("SOMNUS_HOME", None)
        self.assertEqual(config.somnus_home(), (Path.home() / ".somnus").resolve())

    def test_somnus_home_env(self) -> None:
        self.assertEqual(config.somnus_home(), self.home)


class TestValidation(ConfigTestCase):
    def assertConfigError(self, text: str) -> None:
        self.local_cfg(text)
        with self.assertRaises(ConfigError):
            config.load(self.nested)

    def test_unknown_top_level_key(self) -> None:
        self.assertConfigError('colour = "blue"\n')

    def test_unknown_defaults_key(self) -> None:
        self.assertConfigError('[defaults]\nlicense = "MIT"\n')

    def test_unknown_index_key(self) -> None:
        self.assertConfigError('[index]\ndepth = ["3"]\n')

    def test_invalid_enum_values(self) -> None:
        for key, value in [("category", "novel"), ("role", "canon"), ("scope", "planet"),
                           ("visibility", "secret"), ("standing", "maybe"), ("disposition", "keep"),
                           ("body_role", "poem")]:
            with self.subTest(key=key):
                self.assertConfigError(f'[defaults]\n{key} = "{value}"\n')

    def test_valid_enum_values(self) -> None:
        self.local_cfg('[defaults]\ncategory = "research"\nrole = "working"\nscope = "module"\n'
                       'visibility = "public"\nstanding = "unasserted"\ndisposition = "archive-only"\n'
                       'body_role = "narrative"\nallowed_uses = ["archive", "training"]\n')
        cfg = config.load(self.nested)
        self.assertEqual(cfg.defaults["visibility"], "public")
        self.assertEqual(cfg.defaults["allowed_uses"], ["archive", "training"])

    def test_invalid_allowed_uses(self) -> None:
        self.assertConfigError('[defaults]\nallowed_uses = ["archive", "sell"]\n')
        self.assertConfigError('[defaults]\nallowed_uses = "archive"\n')

    def test_actor_must_be_nonempty_string(self) -> None:
        self.assertConfigError('actor = "  "\n')
        self.assertConfigError("actor = 3\n")

    def test_tables_must_be_tables(self) -> None:
        self.assertConfigError('defaults = "x"\n')
        self.assertConfigError('index = 1\n')

    def test_index_values_must_be_string_arrays(self) -> None:
        self.assertConfigError("[index]\nroots = [1]\n")
        self.assertConfigError('[index]\nexclude = "x"\n')

    def test_malformed_toml(self) -> None:
        self.assertConfigError("actor = \n")

    def test_global_errors_are_reported(self) -> None:
        self.global_cfg('[defaults]\ncategory = "nope"\n')
        with self.assertRaises(ConfigError):
            config.load(self.nested)

    def test_template_is_valid(self) -> None:
        self.global_cfg(config.CONFIG_TEMPLATE)
        cfg = config.load(self.nested)
        self.assertEqual(cfg.actor, "operator")
        self.assertEqual(cfg.roots, [self.nested])


if __name__ == "__main__":
    unittest.main()
