import datetime as dt
import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules, assertEqual


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate modules
        activate_modules(['stock_valued_delivery_cost', 'stock_origin_sale'])

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create customer
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.sale_shipment_cost_method = 'order'
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_revenue = revenue
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        ProductTemplate = Model.get('product.template')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        template = ProductTemplate()
        template.name = 'Product'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.lead_time = dt.timedelta(0)
        template.list_price = Decimal('20')
        template.account_category = account_category
        template.save()
        product, = template.products

        # Create carrier product
        carrier_template = ProductTemplate()
        carrier_template.name = 'Carrier Product'
        carrier_template.default_uom = unit
        carrier_template.type = 'service'
        carrier_template.salable = True
        carrier_template.lead_time = dt.timedelta(0)
        carrier_template.list_price = Decimal('3')
        carrier_template.account_category = account_category
        carrier_template.save()
        carrier_product, = carrier_template.products
        carrier_product.cost_price = Decimal('2')
        carrier_product.save()

        # Create carrier
        Carrier = Model.get('carrier')
        carrier = Carrier()
        party = Party(name='Carrier')
        party.save()
        carrier.party = party
        carrier.carrier_product = carrier_product
        carrier.save()

        # Use it as the default carrier
        CarrierSelection = Model.get('carrier.selection')
        csc = CarrierSelection(carrier=carrier)
        csc.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Sale products with cost on order
        Sale = Model.get('sale.sale')
        sale = Sale()
        sale.party = customer
        sale.carrier = carrier
        sale.payment_term = payment_term
        sale.invoice_method = 'shipment'
        self.assertEqual(sale.shipment_cost_method, 'order')
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 5.0
        sale.click('quote')
        cost_line = sale.lines[-1]
        assertEqual(cost_line.product, carrier_product)
        self.assertEqual(cost_line.quantity, 1.0)
        self.assertEqual(cost_line.amount, Decimal('3.00'))
        self.assertEqual(cost_line.invoice_progress, 1.0)
        sale.click('confirm')
        sale.click('process')
        self.assertEqual(sale.state, 'processing')
        self.assertEqual(sale.untaxed_amount, Decimal('103.00'))
        self.assertEqual(sale.tax_amount, Decimal('10.30'))
        self.assertEqual(sale.total_amount, Decimal('113.30'))

        # check shipment amounts
        shipment, = sale.shipments
        self.assertEqual(shipment.cost_method, 'order')
        assertEqual(shipment.carrier, carrier)
        self.assertEqual(shipment.untaxed_amount, Decimal('103.00'))
        self.assertEqual(shipment.tax_amount, Decimal('10.30'))
        self.assertEqual(shipment.total_amount, Decimal('113.30'))
        self.assertEqual(shipment.state, 'waiting')
        shipment.click('assign_force')
        self.assertEqual(shipment.state, 'assigned')
        shipment.click('pick')
        self.assertEqual(shipment.state, 'picked')
        shipment.click('pack')
        self.assertEqual(shipment.state, 'packed')
        shipment.click('do')
        self.assertEqual(shipment.state, 'done')
        self.assertEqual(shipment.untaxed_amount, Decimal('103.00'))
        self.assertEqual(shipment.tax_amount, Decimal('10.30'))
        self.assertEqual(shipment.total_amount, Decimal('113.30'))

        # Sale products without shipment cost
        Sale = Model.get('sale.sale')
        sale = Sale()
        sale.party = customer
        sale.carrier = carrier
        sale.payment_term = payment_term
        sale.invoice_method = 'shipment'
        sale.shipment_cost_method = None
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 5.0
        sale.click('quote')
        self.assertEqual(len(sale.lines), 1)
        sale.click('confirm')
        sale.click('process')
        self.assertEqual(sale.state, 'processing')
        self.assertEqual(sale.untaxed_amount, Decimal('100.00'))
        self.assertEqual(sale.tax_amount, Decimal('10.00'))
        self.assertEqual(sale.total_amount, Decimal('110.00'))

        # check shipment amounts
        shipment, = sale.shipments
        self.assertEqual(shipment.cost_method, None)
        assertEqual(shipment.carrier, carrier)
        self.assertEqual(shipment.untaxed_amount, Decimal('100.00'))
        self.assertEqual(shipment.tax_amount, Decimal('10.00'))
        self.assertEqual(shipment.total_amount, Decimal('110.00'))
        self.assertEqual(shipment.state, 'waiting')
        shipment.click('assign_force')
        self.assertEqual(shipment.state, 'assigned')
        shipment.click('pick')
        self.assertEqual(shipment.state, 'picked')
        shipment.click('pack')
        self.assertEqual(shipment.state, 'packed')
        shipment.click('do')
        self.assertEqual(shipment.state, 'done')
        self.assertEqual(shipment.untaxed_amount, Decimal('100.00'))
        self.assertEqual(shipment.tax_amount, Decimal('10.00'))
        self.assertEqual(shipment.total_amount, Decimal('110.00'))
