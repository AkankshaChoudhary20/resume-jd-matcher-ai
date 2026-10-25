from resume_jd_matcher.cli import run

def test_directory_input_reports_error_without_traceback(tmp_path, capsys):
    assert run(["--resume", str(tmp_path), "--jd", str(tmp_path), "--no-ai"]) == 1
    assert "Error:" in capsys.readouterr().err
