import ast
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import smart_auditor as app
from discount_strategy import DiscountStrategy
from no_discount import NoDiscount
from percentage_discount import PercentageDiscount
from bulk_discount import BulkDiscount
from student_discount import StudentDiscount
from order import Order
from order_line import OrderLine
from inventory import Inventory
from supplier import UNKNOWN_SUPPLIER
from product_factory import ProductFactory
from input_helpers import get_positive_float, get_integer, get_nonnegative_float
from csv_loader import load_products

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = os.environ.get("TEST_TMP_ROOT")


class Lab9Tests(unittest.TestCase):
    def product(self, kind="physical", price=125.0, stock=4):
        return ProductFactory.create(kind, "P1", "Book", price, stock, weight=0.5, download_size=20)

    def test_strategy_is_abstract(self):
        with self.assertRaises(TypeError):
            DiscountStrategy()

    def test_default_and_interchangeable_discounts(self):
        order = Order("A")
        order.add_order_line(self.product(), 2)
        self.assertEqual(order.calculate_total(), 250)
        order.set_discount(BulkDiscount(200, 20))
        self.assertEqual(order.calculate_total(), 230)
        order.set_discount(PercentageDiscount(10))
        self.assertEqual(order.calculate_total(), 225)
        order.set_discount(StudentDiscount())
        self.assertEqual(order.calculate_total(), 237.5)

    def test_strategy_can_be_shared_between_orders(self):
        discount = PercentageDiscount(10)
        first, second = Order("A", discount), Order("B", discount)
        first.add_order_line(self.product(), 2)
        second.add_order_line(self.product(), 1)
        self.assertEqual(first.calculate_total(), 225)
        self.assertEqual(second.calculate_total(), 112.5)

    def test_order_delegates_without_discount_branches(self):
        class FixedTotal(DiscountStrategy):
            def apply(self, total: float) -> float:
                return 17.0
        order = Order("A", FixedTotal())
        order.add_order_line(self.product(), 2)
        self.assertEqual(order.calculate_total(), 17)
        tree = ast.parse((ROOT / "order.py").read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "calculate_total")
        self.assertFalse(any(isinstance(n, (ast.If, ast.IfExp)) for n in ast.walk(method)))

    def test_discount_boundaries(self):
        self.assertEqual(BulkDiscount(200, 20).apply(199), 199)
        self.assertEqual(BulkDiscount(200, 20).apply(200), 180)
        self.assertEqual(BulkDiscount(0, 20).apply(5), 0)
        self.assertEqual(PercentageDiscount(0).apply(250), 250)
        self.assertEqual(PercentageDiscount(100).apply(250), 0)
        self.assertEqual(NoDiscount().apply(0), 0)

    def test_invalid_discounts(self):
        for value in [-1, 101, float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                PercentageDiscount(value)
        with self.assertRaises(ValueError):
            BulkDiscount(-1, 20)
        with self.assertRaises(ValueError):
            BulkDiscount(200, -1)

    def test_factory_unknown_type(self):
        with self.assertRaisesRegex(ValueError, "Unknown product type: service"):
            self.product("service")

    def test_prices_are_positive_and_finite(self):
        for kind in ["physical", "digital"]:
            for price in [0, -1, float("nan"), float("inf")]:
                with self.subTest(kind=kind, price=price), self.assertRaises(ValueError):
                    self.product(kind, price=price)

    def test_invalid_stock_cannot_change_existing_state(self):
        for kind in ["physical", "digital"]:
            for value in [-1, 1.5, True]:
                with self.subTest(kind=kind, stock=value):
                    with self.assertRaises(ValueError):
                        self.product(kind, stock=value)
                    product = self.product(kind)
                    with self.assertRaises(ValueError):
                        product.update_stock(value)
                    self.assertEqual((product.stock, product.history), (4, [4]))

    def test_order_line_protects_its_own_quantity(self):
        for value in [0, -1, 1.5, True]:
            with self.subTest(quantity=value), self.assertRaises(ValueError):
                OrderLine(self.product(), value)
        self.assertEqual(OrderLine(self.product(), 2).calculate_subtotal(), 250)

    def test_price_retry_messages(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["abc", "-5", "12.50"]), contextlib.redirect_stdout(output):
            value = get_positive_float("Price: ")
        self.assertEqual(value, 12.5)
        self.assertEqual(output.getvalue().splitlines(), [
            "Please enter a valid number, e.g. 12.50",
            "Please enter a number greater than zero.",
        ])

    def test_numeric_helpers_reject_nonfinite_and_invalid_values(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with patch("builtins.input", side_effect=["nan", "inf", "0", "1"]):
                self.assertEqual(get_positive_float(""), 1)
            with patch("builtins.input", side_effect=["a", "-1", "0"]):
                self.assertEqual(get_integer(""), 0)
            with patch("builtins.input", side_effect=["a", "nan", "-1", "0.5"]):
                self.assertEqual(get_nonnegative_float(""), 0.5)

    def test_csv_sample_loads_three_and_always_finishes(self):
        inventory = Inventory()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(ProductFactory, "create", wraps=ProductFactory.create) as factory:
            load_products(str(ROOT / "products.csv"), inventory, UNKNOWN_SUPPLIER)
        self.assertEqual([p.product_id for p in inventory.get_products()], ["P001", "D001", "P003"])
        self.assertEqual(factory.call_count, 4)
        lines = output.getvalue().splitlines()
        self.assertIn("Row 4 skipped: Unknown product type: service", lines[0])
        self.assertIn("Row 5 skipped:", lines[1])
        self.assertEqual(lines[-2:], ["3 products loaded.", "Load attempt finished."])

    def test_missing_csv_finishes(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            path = str(Path(folder) / "missing.csv")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                load_products(path, Inventory(), UNKNOWN_SUPPLIER)
            self.assertEqual(output.getvalue().splitlines(), [
                f"Products file not found: {path}", "Load attempt finished."
            ])

    def test_csv_repeat_does_not_duplicate_products(self):
        inventory = Inventory()
        with contextlib.redirect_stdout(io.StringIO()):
            load_products(str(ROOT / "products.csv"), inventory, UNKNOWN_SUPPLIER)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            load_products(str(ROOT / "products.csv"), inventory, UNKNOWN_SUPPLIER)
        self.assertEqual(len(inventory.get_products()), 3)
        self.assertIn("0 products loaded.", output.getvalue())

    def test_bad_csv_rows_do_not_stop_later_rows(self):
        header = "product_type,product_id,name,price,stock_quantity\n"
        rows = "physical,P0,Zero,0,1\ndigital,D0,Stock,4,-1\nbad,row\nphysical,P9,Good,10,3\n"
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            path = Path(folder) / "data.csv"
            path.write_text(header + rows)
            inventory = Inventory()
            with contextlib.redirect_stdout(io.StringIO()):
                load_products(str(path), inventory, UNKNOWN_SUPPLIER)
            self.assertEqual([p.product_id for p in inventory.get_products()], ["P9"])

    def test_corrupt_inventory_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            path = Path(folder) / "inventory.json"
            path.write_text("{broken")
            result = subprocess.run([sys.executable, str(ROOT / "smart_auditor.py")],
                input="6\n", text=True, capture_output=True, cwd=folder, timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Could not load inventory:", result.stdout)
            self.assertEqual(path.read_text(), "{broken")

    def test_failed_save_preserves_previous_file(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                Path("inventory.json").write_text("[]")
                with patch("smart_auditor.os.replace", side_effect=PermissionError("locked")):
                    with self.assertRaises(PermissionError):
                        app.save_inventory(Inventory())
                self.assertEqual(Path("inventory.json").read_text(), "[]")
                self.assertEqual(list(Path(".").glob("*.tmp")), [])
            finally:
                os.chdir(previous)

    def test_menu_import_order_discount_and_exit(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as folder:
            csv_path = str(ROOT / "products.csv")
            answers = ["10", csv_path, "9", "O1", "P001", "10", "", "11", "O1", "3", "200", "20", "11", "O1", "2", "10", "6"]
            result = subprocess.run([sys.executable, str(ROOT / "smart_auditor.py")],
                input="\n".join(answers)+"\n", text=True, capture_output=True, cwd=folder, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            for total in ("250.00", "230.00", "225.00"):
                self.assertIn("Total: $" + total, result.stdout)
            data = json.loads((Path(folder) / "inventory.json").read_text())
            self.assertEqual(len(data), 3)
