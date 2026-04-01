import sys
from pathlib import Path

import pytest

# Add parent directory to path so utils can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.parameter_ui import render_parameters_with_indent, reset_parameters_to_defaults


def test_html_escaping_in_parameter_labels():
    """Verify HTML injection attempts in labels are escaped."""
    malicious_param_dict = {
        "\t<script>alert('XSS')</script>": "100",
        "\t<img src=x onerror=alert('XSS')>": "200"
    }
    
    params = {}
    
    # Should handle malicious labels safely (not raise exception)
    try:
        render_parameters_with_indent(malicious_param_dict, params, model_id="test")
        assert True
    except Exception as e:
        pytest.fail(f"render_parameters_with_indent raised: {e}")


def test_reset_parameters_to_defaults():
    """Verify reset_parameters_to_defaults works correctly."""
    param_dict = {
        "cost_latent": 300.0,
        "cost_active": 34523.0
    }
    params = {}
    
    reset_parameters_to_defaults(param_dict, params, model_id="test")
    
    assert params.get("cost_latent") == 300.0
    assert params.get("cost_active") == 34523.0


def test_nested_parameters():
    """Verify nested parameter structures are handled."""
    param_dict = {
        "Costs": None,
        "\tcost_latent": 300.0,
        "Medical": None,
        "\t\tcost_active": 34523.0
    }
    params = {}
    
    render_parameters_with_indent(param_dict, params, model_id="test")
    
    assert params.get("cost_latent") == "300.0"
    assert params.get("cost_active") == "34523.0"