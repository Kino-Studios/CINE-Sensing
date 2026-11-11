from dataclasses import replace

CANONICAL_BAG = 'datasets/vio_bags/canonical'


def test_vio_record_defaults_to_the_canonical_bag(invoke):
    result = invoke('vio', 'record', '--dry-run')

    assert result.stdout == f'bash tools/vio_record_bag.sh {CANONICAL_BAG}\n'


def test_vio_record_passes_the_output_directory(invoke, runner, repository_root):
    invoke('vio', 'record', '--out', 'bags/today')

    assert runner.commands == [(['bash', 'tools/vio_record_bag.sh', 'bags/today'], repository_root)]


def test_vio_record_without_ros2_exits_3_and_starts_nothing(invoke, runner, environment):
    without_ros2 = replace(environment, which=lambda name: None)

    result = invoke('vio', 'record', environment=without_ros2)

    assert result.exit_code == 3
    assert runner.commands == []


def test_vio_compare_passes_label_bag_duration_and_profile(invoke, runner, repository_root):
    invoke('vio', 'compare', 'maxcnt250', '--duration', '45', '--profile', 'rpi_v3_tune_maxcnt250')

    assert runner.commands == [
        (
            [
                'bash',
                'tools/vio_ab_run.sh',
                'maxcnt250',
                CANONICAL_BAG,
                '45',
                'rpi_v3_tune_maxcnt250',
            ],
            repository_root,
        )
    ]


def test_vio_compare_requires_a_label(invoke, runner):
    result = invoke('vio', 'compare')

    assert result.exit_code == 2
    assert "Missing argument 'label'" in result.output
    assert runner.commands == []


def test_vio_compare_with_unknown_profile_exits_2_and_lists_profiles(invoke, runner):
    result = invoke('vio', 'compare', 'maxcnt250', '--profile', 'nope')

    assert result.exit_code == 2
    assert 'rpi_v3_wide' in result.output
    assert runner.commands == []


def test_vio_record_marks_ctrl_c_as_its_normal_stop(invoke, runner):
    invoke('vio', 'record')
    invoke('vio', 'compare', 'baseline')

    assert runner.normal_stop_flags == [True, False]
