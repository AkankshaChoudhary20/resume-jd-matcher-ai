from resume_jd_matcher.cli import run

def test_invalid_utf8_is_reported_without_scoring_corrupted_text(tmp_path, capsys):
    resume = tmp_path / 'resume.txt'; jd = tmp_path / 'jd.txt'
    resume.write_bytes(b'Python \xff developer'); jd.write_text('Python developer')
    assert run(['--resume', str(resume), '--jd', str(jd), '--no-ai']) == 1
    captured = capsys.readouterr()
    assert 'Error:' in captured.err
    assert 'Overall match score:' not in captured.out
