# This file is part stock_valued_delivery_cost module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class StockValuedDeliveryCostTestCase(ModuleTestCase):
    'Test Stock Valued Delivery Cost module'
    module = 'stock_valued_delivery_cost'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            StockValuedDeliveryCostTestCase))
    return suite
