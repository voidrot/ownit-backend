# Content Security Policy
from csp.constants import NONE, SELF

CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    'EXCLUDE_URL_PREFIXES': ['/excluded-path/'],
    'DIRECTIVES': {
        'default-src': [NONE],
        'connect-src': [SELF],
        'img-src': [SELF],
        'form-action': [SELF],
        'frame-ancestors': [SELF],
        'script-src': [SELF],
        'style-src': [SELF],
        'upgrade-insecure-requests': True,
        # 'report-uri': '/csp-report/',
    },
}
