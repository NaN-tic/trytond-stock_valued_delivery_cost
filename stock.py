# This file is part stock_valued_delivery_cost module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool, PoolMeta
from trytond.model import fields

__all__ = ['ShipmentOut']


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'
    sale_delivery_cost = fields.Function(fields.Many2One('sale.line',
        'Sale Delivery Cost'), 'get_sale_line')

    @classmethod
    def get_sale_line(cls, shipments, names):
        res = {n: {s.id: None for s in shipments} for n in names}
        for name in names:
            for shipment in shipments:
                if (shipment.origin and shipment.origin.__name__ == 'sale.sale'):
                    for line in shipment.origin.lines:
                        if name == 'sale_delivery_cost' and line.shipment_cost:
                            res[name][shipment.id] = line.id
                            break
        return res

    def calc_amounts(self):
        Tax = Pool().get('account.tax')

        result = super(ShipmentOut, self).calc_amounts()

        # add delivery cost in stock valued
        if self.sale_delivery_cost:
            untaxed_amount = self.sale_delivery_cost.amount
            tax_list = Tax.compute(self.sale_delivery_cost.taxes,
                self.sale_delivery_cost.unit_price or Decimal('0.0'),
                self.sale_delivery_cost.quantity or 0.0)
            tax_amount = sum([self.company.currency.round(t['amount'])
                    for t in tax_list], Decimal('0.0'))
            result['untaxed_amount'] += untaxed_amount
            result['tax_amount'] += tax_amount
            result['total_amount'] += (untaxed_amount + tax_amount)

        return result
