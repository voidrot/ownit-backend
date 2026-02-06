import re
from pathlib import Path


def test_env_vars_documented():
    """
    Ensure all `env()` calls in the codebase are documented in .env.template.
    """
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / '.env.template'

    # Read variables from .env.template
    documented_vars = set()
    if template_path.exists():
        with open(template_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Remove leading # and whitespace to allow commented-out vars
                line = line.lstrip('#').strip()

                if line and '=' in line:
                    var_name = line.split('=')[0].strip()
                    documented_vars.add(var_name)

    # Find variables used in code
    # Regex to find env.str("VAR_NAME"), env.bool('VAR_NAME'), etc.
    # We look for env.[method]("VAR_NAME" or 'VAR_NAME'
    env_usage_pattern = re.compile(r'env\.[a-z_]+\(["\']([A-Z_0-9]+)["\']')

    found_vars = set()

    # Walk through config directory
    config_dir = base_dir / 'config'
    for path in config_dir.rglob('*.py'):
        with open(path, 'r') as f:
            content = f.read()
            matches = env_usage_pattern.findall(content)
            for var in matches:
                # Skip some known non-env strings if regex is too broad,
                # but the ALL_CAPS pattern typically catches env vars.
                found_vars.add(var)

    # Check for missing documentation
    # Some variables might be optional or internal, but usually all should be hinted.
    # We allow some exceptions if strictly internal, but for now let's enforce all.
    missing_vars = found_vars - documented_vars

    assert not missing_vars, (
        f'The following environment variables are used in config but not documented in .env.template: {missing_vars}'
    )
