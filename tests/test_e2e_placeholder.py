import pytest


@pytest.mark.skip(reason='E2E tests require integration setup; enabled when RUN_INTEGRATION=1')
def test_e2e_send_generate_execute_get_output():
    pass
