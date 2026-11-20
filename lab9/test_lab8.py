import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import smart_auditor as app


def show_product_details(product: app.Product) -> None:
    product.display_information()
    print(product.get_fulfilment_info())


class Relationships(unittest.TestCase):
    def setUp(self) -> None:
        self.supplier = app.Supplier("S1", "Campus Books", "books@example.org")
        self.book = app.PhysicalProduct("P1", "Book", 12.50, 8, 0.4, supplier=self.supplier)
        self.ebook = app.DigitalProduct("D1", "E-book", 5.00, 20, 50, supplier=self.supplier)

    def test_supplier_reference_survives_deletion(self) -> None:
        supplier = self.supplier
        del self.supplier
        del supplier
        self.assertIs(self.book.supplier, self.ebook.supplier)
        for product in (self.book, self.ebook):
            output = io.StringIO()
            with redirect_stdout(output):
                product.supplier.display_information()
            self.assertIn("books@example.org", output.getvalue())

    def test_supplier_round_trip(self) -> None:
        registry = {}
        first = app.product_from_dict(self.book.to_dict(), registry)
        second = app.product_from_dict(self.ebook.to_dict(), registry)
        self.assertIs(first.supplier, second.supplier)
        self.assertEqual(first.supplier, self.supplier)

    def test_transfer_preserves_identity(self) -> None:
        first, second = app.Inventory(), app.Inventory()
        first.add_product(self.book)
        self.assertIs(first.remove_product("P1"), self.book)
        self.assertIsNone(first.find_product("P1"))
        self.book.update_stock(5)
        second.add_product(self.book)
        self.assertIs(second.find_product("P1"), self.book)
        self.assertEqual(self.book.history, [8, -3])

    def test_order_owns_distinct_lines(self) -> None:
        first, second = app.Order("A"), app.Order("B")
        first.add_order_line(self.book, 2)
        first.add_order_line(self.ebook, 3)
        second.add_order_line(self.book, 1)
        self.assertEqual(first.calculate_total(), 40)
        self.assertIsNot(first.order_lines[0], second.order_lines[0])
        self.assertIs(first.order_lines[0].product, second.order_lines[0].product)
        first.remove_order_line(0)
        self.assertEqual(first.calculate_total(), 15)
        self.assertEqual(second.calculate_total(), 12.5)
        self.assertEqual(self.book.stock, 8)
        with self.assertRaises(ValueError):
            first.add_order_line(self.book, 0)

    def test_polymorphism_and_stock_contract(self) -> None:
        inventory = app.Inventory()
        inventory.add_product(self.book)
        inventory.add_product(self.ebook)
        for product, expected in zip(inventory.get_products(),
                ("Requires physical shipping.", "Delivered digitally by download.")):
            output = io.StringIO()
            with redirect_stdout(output):
                show_product_details(product)
            self.assertEqual(output.getvalue().splitlines()[-1], expected)
            stock = product.stock
            product.update_stock(stock + 2)
            self.assertEqual(product.history[-1], 2)
            self.assertEqual(product.stock, stock + 2)
            self.assertIs(inventory.find_product(product.product_id), product)

    def test_console_create_order(self) -> None:
        inventory = app.Inventory()
        inventory.add_product(self.book)
        order = app.Order("A")
        with patch("builtins.input", side_effect=["P1", "2", ""]), redirect_stdout(io.StringIO()):
            app.enter_order(inventory, order)
        self.assertEqual(order.calculate_total(), 25)
