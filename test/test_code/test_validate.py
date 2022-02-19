import unittest

from onthisday.db import validate_criteria


class ValidateTestCase(unittest.TestCase):

    TO_BE_VALIDATED = {
        'month': 'fEbRuARy',
        'date': '14',
        'event_category': 'Births'
    }

    VALIDATED = {
        'month': 'February',
        'date': 14,
        'event_category': 'Births'
    }

    CANNOT_BE_VALIDATED = (
        {
            'month': 'Smarch',
        },
        {
            'date': -4
        },
        {
            'month': 'February',
            'date': 40,
        },
        {
            'event_category': 'bad category'
        }
    )

    def test_01_validate(self):
        valid = validate_criteria(**self.TO_BE_VALIDATED)
        self.assertDictEqual(valid, self.VALIDATED)
        self.assertIsNot(valid, self.VALIDATED)

        valid2 = validate_criteria(**valid)
        self.assertDictEqual(valid, valid2)
        self.assertIsNot(valid, valid2)

    def test_02_cannot_validate(self):
        for c in self.CANNOT_BE_VALIDATED:
            self.assertRaises(ValueError, validate_criteria, **c)