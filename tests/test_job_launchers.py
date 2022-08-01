import pytest, os
from mljob.job_manager import generate_job_id
from mljob.job_manager import LocalLauncher

# from mljob.results_storage import ResultsFileStore

@pytest.fixture()
def job_name():
    j = generate_job_id()
    print(f"using job id {j} for testing")
    yield j


def test_job_launcher_local(job_name):
    test_job_config = {'jobname': job_name}

    launcher = LocalLauncher()
    assert launcher is not None
    assert str(type(launcher)) == "<class 'mljob.job_manager.LocalLauncher'>"

    test_response = launcher.launch(test_job_config)