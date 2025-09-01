import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_dressup_properties_unit_aware():
    p = os.path.join(ROOT, 'Entities', 'Dressup.py')
    s = read(p)
    assert 'App::PropertyDistance", "Radius"' in s
    assert 'App::PropertyDistance", "Length"' in s
    assert 'App::PropertyDistance", "Diameter"' in s
    assert 'App::PropertyAngle", "Angle"' in s


def test_pattern_generate_uses_value():
    p = os.path.join(ROOT, 'Entities', 'Pattern.py')
    s = read(p)
    assert 'obj.YAxisLength.Value' in s
    assert 'obj.XAxisLength.Value' in s


def test_dressup_geometry_uses_value():
    p = os.path.join(ROOT, 'Entities', 'Dressup.py')
    s = read(p)
    assert 'obj.Radius.Value' in s
    assert 'obj.Length.Value' in s
    assert 'obj.Diameter.Value' in s
    assert 'obj.Angle.Value' in s


def test_extrusion_starting_offset_uses_value():
    p = os.path.join(ROOT, 'Entities', 'Extrusion.py')
    s = read(p)
    assert 'StartingOffsetLength.Value' in s


def test_pattern_panel_uses_axis_lengths_and_counts():
    p = os.path.join(ROOT, 'Entities', 'Pattern.py')
    s = read(p)
    assert 'xInput' in s and 'yInput' in s
    assert 'xCountInput' in s and 'yCountInput' in s
