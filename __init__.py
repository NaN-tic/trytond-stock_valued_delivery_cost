# This file is part stock_valued_delivery_cost module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import stock


def register():
    Pool.register(
        stock.ShipmentOut,
        module='stock_valued_delivery_cost', type_='model')
