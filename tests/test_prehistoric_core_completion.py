from aegis_py.prehistoric_completion import build_prehistoric_completion_report


def test_prehistoric_core_completion_gate_passes():
    report = build_prehistoric_completion_report()

    assert report['total_beasts'] == 23
    assert report['signal_surface_count'] == 0
    assert report['pipeline_active_count'] == 0
    assert report['core_deep_count'] == 23
    assert not report['missing_required_core_deep']
    assert report['passed'] is True
