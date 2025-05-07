# This file is part stock_valued_delivery_cost module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool, PoolMeta
from trytond.model import fields


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

    @classmethod
    def get_amounts(cls, shipments, names):
        pool = Pool()
        Tax = pool.get('account.tax')
        Date = pool.get('ir.date')

        result = super().get_amounts(shipments, names)

        for shipment in shipments:
            # in case has cache, not sum delivery cost
            if shipment.untaxed_amount_cache is not None:
                continue

            # add delivery cost in stock valued
            if shipment.sale_delivery_cost:
                date = shipment.effective_date or shipment.planned_date or Date.today()
                untaxed_amount = shipment.sale_delivery_cost.amount
                tax_list = Tax.compute(shipment.sale_delivery_cost.taxes,
                    shipment.sale_delivery_cost.unit_price or Decimal(0),
                    shipment.sale_delivery_cost.quantity or 0.0, date)
                tax_amount = sum([shipment.company.currency.round(t['amount'])
                        for t in tax_list], Decimal(0))
                if 'untaxed_amount' in names:
                    result['untaxed_amount'][shipment.id] += untaxed_amount
                if 'tax_amount' in names:
                    result['tax_amount'][shipment.id] += tax_amount
                if 'total_amount' in names:
                    result['total_amount'][shipment.id] += (untaxed_amount + tax_amount)

        return result
