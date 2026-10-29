import pytest
from resume_jd_matcher.cli import run

@pytest.mark.parametrize('empty', ['resume', 'jd'])
def test_blank_document_cannot_report_a_successful_match(tmp_path, capsys, empty):
    paths = {name: tmp_path / (name + '.txt') for name in ('resume', 'jd')}
    for name, path in paths.items():
        path.write_text(' \t\n' if name == empty else 'Python developer')
    assert run(['--resume', str(paths['resume']), '--jd', str(paths['jd']), '--no-ai']) == 1
    captured = capsys.readouterr()
    assert 'must contain non-whitespace text' in captured.err
    assert 'Overall match score' not in captured.out
