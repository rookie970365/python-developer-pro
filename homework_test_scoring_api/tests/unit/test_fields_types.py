# pylint: disable=C0114,C0115,C0116,C0301,R0201
import datetime
from pytest import mark, raises

import api


class TestCharField:
    @mark.parametrize("value", ['Accio', '1\rAlohomora)\n', '12345'])
    def test_valid(self, value):
        assert api.CharField().validate(value) is None

    @mark.parametrize("value",
                      [None,
                       12345,
                       {'Avada': 'Kedavra'},
                       {'Brackium', 'Emendo'},
                       ['Bubble', 'Head', 'Charm']
                       ])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.CharField().validate(value)


class TestArgumentsField:

    @mark.parametrize("value", [{}, {'Avada': 'Kedavra'}])
    def test_valid(self, value):
        assert api.ArgumentsField().validate(value) is None

    @mark.parametrize("value",
                      [None,
                       12345,
                       'Aguamenti',
                       {'Brackium', 'Emendo'},
                       ['Bubble', 'Head', 'Charm']
                       ])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.ArgumentsField().validate(value)


class TestEmailField:

    @mark.parametrize("value", ['_@_', 'email@example.com'])
    def test_valid(self, value):
        assert api.EmailField().validate(value) is None

    @mark.parametrize("value", ['', None, 12345, {'email@example.com'}])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.EmailField().validate(value)


class TestPhoneField:

    @mark.parametrize("value", ['79091234993', 79035151234, 71234567890, ''])
    def test_valid(self, value):
        assert api.PhoneField().validate(value) is None

    @mark.parametrize("value", ['+79991237733', [79991237733, ], 83469431234, 9999])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.PhoneField().validate(value)


class TestDateField:

    def test_empty(self):
        assert api.DateField().validate('') is None

    def test_valid(self):
        assert api.DateField().validate('01.01.2000') == datetime.date(day=1, month=1, year=2000)
        assert api.DateField().validate('12.10.2020') == datetime.date(day=12, month=10, year=2020)
        assert api.DateField().validate('19.01.2022') == datetime.date(day=19, month=1, year=2022)

    @mark.parametrize("value", ['1999.11.11', '01.01.2001 10:20:30', datetime.date.today()])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.DateField().validate(value)


class TestBirthdayField:

    def test_empty(self):
        assert api.BirthDayField().validate('') is None

    @mark.parametrize("value", ['2.7.2022', '01.01.2000', '12.04.2021'])
    def test_valid(self, value):
        assert api.BirthDayField().validate(value) is None

    @mark.parametrize("value", ['2000.11.03', '01.01.1890', '11.01.1111'])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.BirthDayField().validate(value)


class TestGenderField:

    @mark.parametrize("value", list(api.GENDERS.keys()))
    def test_valid(self, value):
        assert api.GenderField().validate(value) is None

    @mark.parametrize("value", [10, '', 3.333, -99])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.GenderField().validate(value)


class TestClientIDsField:

    @mark.parametrize("value", [[1, 2, 3, 4, 5], [-1, -2, -3], [0], []])
    def test_valid(self, value):
        assert api.ClientIDsField().validate(value) is None

    @mark.parametrize("value", ['+79991237733', [3.14, 2.71], 83469431234])
    def test_invalid(self, value):
        with raises(api.ValidationError):
            api.ClientIDsField().validate(value)
