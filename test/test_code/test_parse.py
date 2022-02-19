import unittest

from onthisday.get_data import parse_holidays

LISTS = (
    (
        [
            '*Test 1',
            '*Test 2',
            '**Test 2(a)',
            '*Test 3',
            '**Test 3(a)',
            '**Test 3(b)',
            '***Test 3(b)(i)',
            '*Test 4'
        ],
        [
            'Test 1',
            'Test 2 - Test 2(a)',
            'Test 3 - Test 3(a)',
            'Test 3 - Test 3(b) - Test 3(b)(i)',
            'Test 4'
        ]
    ),
)

class ParsingTestCase(unittest.TestCase):

    def test_01_parse_holidays(self):
        for in_list, out_list in LISTS:
            self.assertListEqual(parse_holidays(in_list), out_list)