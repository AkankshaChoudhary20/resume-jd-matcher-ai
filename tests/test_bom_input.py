from resume_jd_matcher.cli import _read_text_file, run

def test_bom_is_removed_from_resume_input(tmp_path):
    p = tmp_path / 'resume.txt'
    p.write_bytes('Python'.encode('utf-8-sig'))
    assert _read_text_file(str(p)) == 'Python'

def test_bom_only_resume_is_empty(tmp_path, capsys):
    resume, jd = tmp_path / 'resume.txt', tmp_path / 'jd.txt'
    resume.write_bytes(b'\xef\xbb\xbf')
    jd.write_text('Python')
    assert run(['--resume', str(resume), '--jd', str(jd), '--no-ai']) == 1
    assert 'non-whitespace' in capsys.readouterr().err
