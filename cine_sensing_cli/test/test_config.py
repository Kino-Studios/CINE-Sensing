import json
from dataclasses import replace


def write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content))


def build_tree(tmp_path):
    config_directory = tmp_path / 'cine_sensing_config' / 'config'
    write_json(config_directory / 'vins.json', {'a': 1})
    (config_directory / 'profiles' / 'p').mkdir(parents=True)

    return config_directory


def test_config_profiles_lists_every_profile_directory(invoke):
    result = invoke('config', 'profiles', '--json')

    assert json.loads(result.stdout) == {
        'profiles': ['rpi_v3_fullfov', 'rpi_v3_tune_maxcnt250', 'rpi_v3_wide']
    }


def test_config_show_without_profile_returns_the_base_files(invoke, repository_root):
    result = invoke('config', 'show', '--json')

    base_vins = json.loads((repository_root / 'cine_sensing_config/config/vins.json').read_text())
    assert json.loads(result.stdout)['config']['vins'] == base_vins


def test_config_show_profile_file_replaces_the_base_file(invoke, environment, tmp_path):
    config_directory = build_tree(tmp_path)
    write_json(config_directory / 'profiles' / 'p' / 'vins.json', {'a': 2})
    isolated = replace(environment, repository_root=tmp_path)

    result = invoke('config', 'show', '--profile', 'p', '--json', environment=isolated)

    assert json.loads(result.stdout)['config']['vins'] == {'a': 2}


def test_config_show_includes_a_file_only_the_profile_has(invoke, environment, tmp_path):
    config_directory = build_tree(tmp_path)
    write_json(config_directory / 'profiles' / 'p' / 'extra.json', {'b': 1})
    isolated = replace(environment, repository_root=tmp_path)

    result = invoke('config', 'show', '--profile', 'p', '--json', environment=isolated)

    assert json.loads(result.stdout)['config']['extra'] == {'b': 1}


def test_config_show_unknown_profile_exits_2(invoke):
    result = invoke('config', 'show', '--profile', 'nope')

    assert result.exit_code == 2


def test_config_show_works_without_ros2(invoke, environment):
    without_ros2 = replace(environment, which=lambda name: None)

    result = invoke('config', 'show', environment=without_ros2)

    assert result.exit_code == 0


def test_config_show_defaults_the_profile_to_the_environment_variable(
    invoke, environment, tmp_path
):
    config_directory = build_tree(tmp_path)
    write_json(config_directory / 'profiles' / 'p' / 'vins.json', {'a': 2})
    isolated = replace(
        environment, repository_root=tmp_path, variables={'CINE_SENSING_PROFILE': 'p'}
    )

    result = invoke('config', 'show', '--json', environment=isolated)

    assert json.loads(result.stdout) == {'profile': 'p', 'config': {'vins': {'a': 2}}}


def test_config_show_prints_each_file_name_then_its_indented_json(invoke, environment, tmp_path):
    build_tree(tmp_path)
    isolated = replace(environment, repository_root=tmp_path)

    result = invoke('config', 'show', environment=isolated)

    assert result.stdout == 'vins\n  {\n    "a": 1\n  }\n'
