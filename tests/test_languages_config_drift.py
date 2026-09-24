"""A new config must not freeze the language set on the day it was written.

An active `languages` list in the template disabled every language shipped
after the config was generated. Configs that already carry such a list are not
migrated here.
"""

from jcodemunch_mcp import config


def test_template_does_not_write_an_active_languages_key():
    assert config._find_active_lang_block(config.generate_template()) is None


def test_template_documents_the_key_on_one_line():
    # `set_key` uncomments a commented key; a multi-line array would strand
    # its continuation lines behind `//`.
    lines = [ln for ln in config.generate_template().splitlines() if '// "languages":' in ln]
    assert len(lines) == 1
    assert lines[0].rstrip().endswith("],")


def test_absent_languages_means_every_language_enabled(tmp_path, monkeypatch):
    storage = tmp_path / "store"
    storage.mkdir()
    monkeypatch.setenv("CODE_INDEX_PATH", str(storage))
    (storage / "config.jsonc").write_text(config.generate_template(), encoding="utf-8")
    config.load_config(storage_path=str(storage))

    from jcodemunch_mcp.parser.languages import LANGUAGE_REGISTRY

    assert config.get("languages", None) is None
    for language in LANGUAGE_REGISTRY:
        assert config.is_language_enabled(language) is True, language


def test_commented_example_is_not_parsed_as_active():
    assert config._parse_active_languages(config.generate_template()) is None


def test_adaptive_mode_writes_a_list_into_the_template(tmp_path, monkeypatch):
    storage = tmp_path / "store"
    storage.mkdir()
    monkeypatch.setenv("CODE_INDEX_PATH", str(storage))
    (storage / "config.jsonc").write_text(config.generate_template(), encoding="utf-8")
    monkeypatch.setattr(config, "_GLOBAL_CONFIG", {"languages_adaptive": True})

    project = tmp_path / "proj"
    project.mkdir()
    # Same set as the commented example, so a parser that reads the example
    # as active would report "no change" and write nothing.
    assert config.apply_adaptive_languages(str(project), {"python", "typescript"}) is True

    config.load_project_config(str(project))
    assert sorted(config.get("languages", None, repo=str(project))) == ["python", "typescript"]
    assert config.is_language_enabled("sql", repo=str(project)) is False


def test_adaptation_never_splices_into_a_commented_block():
    commented = (
        "// header\n{\n"
        '  // "languages": [\n  //   "python",\n  // ],\n'
        '  "meta_fields": []\n}\n'
    )
    out = config._apply_languages_adaptation(commented, {"python"})
    assert out is not None
    assert '// "languages": [\n  //   "python",' in out
    assert config._find_active_lang_block(out) is not None


def test_one_line_object_still_adapts():
    out = config._apply_languages_adaptation('{"languages": ["rust"]}', {"python"})
    assert config._parse_active_languages(out) == {"python"}


def test_a_slash_pair_inside_a_string_does_not_hide_the_key():
    content = '{"path_map": "http://a=/b", "languages": ["rust"]}'
    assert config._parse_active_languages(content) == {"rust"}
    out = config._apply_languages_adaptation(content, {"python"})
    assert out.count('"languages"') == 1
    assert config._parse_active_languages(out) == {"python"}


def test_a_bracket_in_a_comment_inside_the_list_is_skipped():
    content = '{\n  "languages": [\n    "go", // see note [1]\n    "rust"\n  ]\n}\n'
    assert config._parse_active_languages(content) == {"go", "rust"}


def test_a_block_comment_inside_the_list_is_not_a_language():
    assert config._parse_active_languages('{"languages": [/* "go", */ "rust"]}') == {"rust"}


def test_insertion_keeps_a_trailing_line_comment_valid():
    import json

    out = config._apply_languages_adaptation(
        '{\n  "languages_adaptive": true // keep on\n}\n', {"python"}
    )
    parsed = json.loads(config._strip_jsonc(out))
    assert parsed["languages"] == ["python"]
    assert "// keep on" in out


def test_insertion_uses_the_objects_own_closing_brace():
    import json

    out = config._apply_languages_adaptation(
        '{\n  "languages_adaptive": true\n}\n// see {docs}\n', {"python"}
    )
    assert json.loads(config._strip_jsonc(out))["languages"] == ["python"]
    assert out.endswith("// see {docs}\n")


def test_unwalkable_config_is_left_unchanged():
    assert config._apply_languages_adaptation('{"languages_adaptive": true', {"python"}) is None


def test_a_leading_bom_does_not_stop_adaptation():
    out = config._apply_languages_adaptation('﻿{\n  "languages_adaptive": true\n}\n', {"python"})
    assert config._parse_active_languages(out) == {"python"}
