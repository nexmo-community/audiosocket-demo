import sys

# This isn't very nice:
sys.path.insert(0, '.')

import server


def test_format_number():
    assert server.format_number('447700900704') == '07700 900704'
