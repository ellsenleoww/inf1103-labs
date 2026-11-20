import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().with_name("smart_auditor.py")
TEST_TMP_ROOT = os.environ.get("TEST_TMP_ROOT")
MIXED_DATA = [
    {"id": "P001", "name": "Laptop", "price": 1200.0, "stock": 15,
     "history": [10, 5], "type": "physical", "weight": 2.5},
    {"id": "D001", "name": "Photo Editor", "price": 49.99, "stock": 100,
     "history": [100], "type": "digital", "download_size": 512.0},
]


@contextlib.contextmanager
def temporary_working_directory():
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as directory:
        try:
            os.chdir(directory)
            yield Path(directory)
        finally:
            os.chdir(previous)


def run_program(answers, initial_data=None):
    with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as directory:
        data_path = Path(directory, "inventory.json")
        if initial_data is not None:
            data_path.write_text(json.dumps(initial_data), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True,
            cwd=directory,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                "Program failed with code {}:\n{}\n{}".format(
                    result.returncode, result.stdout, result.stderr
                )
            )
        if result.stderr:
            raise AssertionError("Unexpected stderr: " + result.stderr)
        if not data_path.exists():
            raise AssertionError("Exiting must save inventory.json.")
        return result.stdout, json.loads(data_path.read_text(encoding="utf-8"))


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("lab7_auditor_under_test", SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            spec.loader.exec_module(cls.module)
        if output.getvalue():
            raise AssertionError("Importing smart_auditor.py must not start the menu.")

    def physical(self, product_id="P001", weight=2.5, history=None):
        return self.module.PhysicalProduct(
            product_id, "Laptop", 1200.0, 15, weight, history=history
        )

    def digital(self, product_id="D001", download_size=512.0, history=None):
        return self.module.DigitalProduct(
            product_id, "Photo Editor", 49.99, 100, download_size, history=history
        )

    def test_product_is_abstract_and_requires_fulfilment(self):
        with self.assertRaises(TypeError):
            self.module.Product("P001", "Laptop", 1200.0, 15)

        class IncompleteProduct(self.module.Product):
            pass

        with self.assertRaises(TypeError):
            IncompleteProduct("P001", "Laptop", 1200.0, 15)

    def test_shipping_interface_cannot_be_instantiated_or_left_unimplemented(self):
        with self.assertRaises(TypeError):
            self.module.CanBeShipped()

        class IncompleteShipment(self.module.CanBeShipped):
            pass

        with self.assertRaises(TypeError):
            IncompleteShipment()

    def test_shipping_interface_is_usable_without_product_inheritance(self):
        class Parcel(self.module.CanBeShipped):
            def calculate_shipping_cost(self):
                return 8.0

        parcel = Parcel()
        self.assertIsInstance(parcel, self.module.CanBeShipped)
        self.assertNotIsInstance(parcel, self.module.Product)
        self.assertEqual(parcel.calculate_shipping_cost(), 8.0)

    def test_subclass_and_interface_relationships(self):
        physical, digital = self.physical(), self.digital()
        self.assertIsInstance(physical, self.module.Product)
        self.assertIsInstance(digital, self.module.Product)
        self.assertIsInstance(physical, self.module.CanBeShipped)
        self.assertNotIsInstance(digital, self.module.CanBeShipped)
        self.assertFalse(hasattr(digital, "calculate_shipping_cost"))

    def test_common_and_type_specific_properties_are_read_only(self):
        physical, digital = self.physical(), self.digital()
        self.assertEqual((physical.product_id, physical.name, physical.price, physical.stock),
                         ("P001", "Laptop", 1200.0, 15))
        self.assertEqual(physical.weight, 2.5)
        self.assertEqual(digital.download_size, 512.0)
        for product in (physical, digital):
            for attribute in ("product_id", "name", "price", "stock", "history"):
                with self.subTest(product=type(product).__name__, attribute=attribute):
                    with self.assertRaises(AttributeError):
                        setattr(product, attribute, None)
        with self.assertRaises(AttributeError):
            physical.weight = 10
        with self.assertRaises(AttributeError):
            digital.download_size = 10

    def test_shipping_cost_uses_each_products_weight(self):
        for weight, expected in [(0, 0), (0.5, 2.5), (2.5, 12.5), (10, 50)]:
            with self.subTest(weight=weight):
                self.assertAlmostEqual(self.physical(weight=weight).calculate_shipping_cost(),
                                       expected)

    def test_specialised_numeric_attributes_reject_negative_or_nonfinite_values(self):
        for value in [-1, float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.physical(weight=value)
                with self.assertRaises(ValueError):
                    self.digital(download_size=value)

    def test_each_subclass_has_appropriate_fulfilment_message(self):
        physical_message = self.physical().get_fulfilment_info()
        digital_message = self.digital().get_fulfilment_info()
        self.assertIsInstance(physical_message, str)
        self.assertIsInstance(digital_message, str)
        self.assertRegex(physical_message.lower(), r"ship")
        self.assertRegex(digital_message.lower(), r"digital|download")
        self.assertNotEqual(physical_message, digital_message)

    def test_display_contains_inherited_and_specialised_information(self):
        for product, name, price, size in [
            (self.physical(), "Laptop", "$1200.00", "2.5"),
            (self.digital(), "Photo Editor", "$49.99", "512"),
        ]:
            with self.subTest(product=type(product).__name__):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    product.display_information()
                text = output.getvalue()
                self.assertIn(product.product_id, text)
                self.assertIn(name, text)
                self.assertIn(price, text)
                self.assertIn(str(product.stock), text)
                self.assertIn(size, text)
                self.assertIn(product.get_fulfilment_info(), text)
                if isinstance(product, self.module.CanBeShipped):
                    self.assertRegex(text.lower(), r"weight.*kg")
                    self.assertIn("12.50", text)
                else:
                    self.assertRegex(text.lower(), r"download.*mb")

    def test_overridden_displays_reuse_parent_display(self):
        for product in (self.physical(), self.digital()):
            with self.subTest(product=type(product).__name__):
                output = io.StringIO()
                with patch.object(self.module.Product, "display_information",
                                  side_effect=lambda: print("PARENT DETAILS")) as parent:
                    with contextlib.redirect_stdout(output):
                        product.display_information()
                parent.assert_called_once_with()
                self.assertIn("PARENT DETAILS", output.getvalue())

    def test_inherited_stock_updates_record_signed_deltas_and_zero(self):
        for product in (self.physical(), self.digital()):
            with self.subTest(product=type(product).__name__):
                opening = product.stock
                product.update_stock(opening + 5)
                product.update_stock(opening - 2)
                product.update_stock(opening - 2)
                self.assertEqual(product.stock, opening - 2)
                self.assertEqual(product.history, [opening, 5, -7, 0])

    def test_history_and_serialized_history_do_not_expose_internal_list(self):
        for factory in (self.physical, self.digital):
            history = [10, 5]
            product = factory(history=history)
            history.append(999)
            product.history.append(888)
            product.to_dict()["history"].append(777)
            self.assertEqual(product.history, [10, 5])

    def test_to_dict_preserves_common_fields_type_and_own_attribute(self):
        self.assertEqual(self.physical(history=[10, 5]).to_dict(), MIXED_DATA[0])
        self.assertEqual(self.digital().to_dict(), MIXED_DATA[1])

    def test_factory_restores_correct_subclass_and_roundtrips_data(self):
        for data, expected_type in zip(
            MIXED_DATA, [self.module.PhysicalProduct, self.module.DigitalProduct]
        ):
            with self.subTest(product_type=data["type"]):
                product = self.module.product_from_dict(data)
                self.assertIsInstance(product, expected_type)
                self.assertEqual(product.to_dict(), data)

    def test_factory_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            self.module.product_from_dict(dict(MIXED_DATA[0], type="unexpected"))

    def test_typed_record_cannot_silently_lose_its_required_attribute(self):
        for record, field in zip(MIXED_DATA, ["weight", "download_size"]):
            malformed = record.copy()
            del malformed[field]
            with self.subTest(product_type=record["type"]):
                with self.assertRaises(KeyError):
                    self.module.product_from_dict(malformed)

    def test_legacy_records_default_to_physical_with_zero_weight(self):
        legacy = {"id": "P001", "name": "Laptop", "price": 1200.0,
                  "stock": 15, "history": [10, 5]}
        product = self.module.product_from_dict(legacy)
        self.assertIsInstance(product, self.module.PhysicalProduct)
        self.assertEqual(product.weight, 0)
        self.assertEqual(product.to_dict(), dict(legacy, type="physical", weight=0))

    def test_legacy_missing_history_is_not_invented(self):
        legacy = {"id": "P001", "name": "Laptop", "price": 1200.0, "stock": 15}
        product = self.module.product_from_dict(legacy)
        self.assertNotIn("history", product.to_dict())
        product.update_stock(12)
        self.assertEqual(product.history, [-3])
        self.assertEqual(product.to_dict()["history"], [-3])

    def test_empty_history_stays_empty_until_first_delta(self):
        for data in MIXED_DATA:
            product = self.module.product_from_dict(dict(data, history=[]))
            self.assertEqual(product.history, [])
            self.assertEqual(product.to_dict()["history"], [])
            product.update_stock(product.stock + 3)
            self.assertEqual(product.history, [3])

    def test_inventory_rejects_duplicate_ids_across_product_types(self):
        inventory = self.module.Inventory()
        physical = self.physical()
        self.assertTrue(inventory.add_product(physical))
        self.assertFalse(inventory.add_product(self.digital(product_id="P001")))
        self.assertIs(inventory.search_product("P001"), physical)
        self.assertIsNone(inventory.search_product("missing"))
        self.assertEqual(inventory.get_products(), (physical,))

    def test_inventory_update_delegates_to_correct_product(self):
        inventory = self.module.Inventory()
        physical, digital = self.physical(), self.digital()
        inventory.add_product(physical)
        inventory.add_product(digital)
        self.assertTrue(inventory.update_stock("D001", 98))
        self.assertEqual(digital.history, [100, -2])
        self.assertEqual(physical.history, [15])
        self.assertFalse(inventory.update_stock("missing", 10))

    def test_inventory_display_dispatches_product_methods(self):
        inventory = self.module.Inventory()
        physical, digital = self.physical(), self.digital()
        inventory.add_product(physical)
        inventory.add_product(digital)
        with patch.object(physical, "display_information") as physical_display:
            with patch.object(digital, "display_information") as digital_display:
                with contextlib.redirect_stdout(io.StringIO()):
                    inventory.display_all()
        physical_display.assert_called_once_with()
        digital_display.assert_called_once_with()

    def test_mixed_save_load_preserves_subclasses_and_all_values(self):
        with temporary_working_directory() as directory:
            path = directory / "inventory.json"
            path.write_text(json.dumps(MIXED_DATA), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                inventory = self.module.load_inventory()
                self.module.save_inventory(inventory)
            self.assertIsInstance(inventory.search_product("P001"), self.module.PhysicalProduct)
            self.assertIsInstance(inventory.search_product("D001"), self.module.DigitalProduct)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), MIXED_DATA)

    def test_loading_duplicate_ids_rejects_file_without_modifying_it(self):
        duplicated = [MIXED_DATA[0], dict(MIXED_DATA[1], id="P001")]
        with temporary_working_directory() as directory:
            path = directory / "inventory.json"
            original = json.dumps(duplicated)
            path.write_text(original, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    self.module.load_inventory()
            self.assertEqual(path.read_text(encoding="utf-8"), original)


class ConsoleTests(unittest.TestCase):
    def test_empty_start_display_and_exit_saves_empty_inventory(self):
        output, data = run_program(["1", "6"])
        self.assertIn("inventory.json not found.", output)
        self.assertIn("Starting with an empty inventory.", output)
        self.assertIn("Inventory is empty.", output)
        self.assertIn("Saving inventory before exit...", output)
        self.assertIn("Program terminated.", output)
        self.assertEqual(data, [])

    def test_all_menu_choices_with_mixed_products_and_restart(self):
        answers = [
            "2", "P002", "1", "Keyboard", "45", "25", "0.8",
            "2", "D002", "2", "Game", "29.99", "50", "2048",
            "1", "3", "P002", "30", "3", "D002", "48",
            "4", "P002", "4", "D002", "5", "6",
        ]
        output, data = run_program(answers)
        expected = [
            {"id": "P002", "name": "Keyboard", "price": 45.0, "stock": 30,
             "history": [25, 5], "type": "physical", "weight": 0.8},
            {"id": "D002", "name": "Game", "price": 29.99, "stock": 48,
             "history": [50, -2], "type": "digital", "download_size": 2048.0},
        ]
        self.assertEqual(data, expected)
        self.assertEqual(output.count("Product added successfully!"), 2)
        self.assertEqual(output.count("Stock updated successfully!"), 2)
        self.assertEqual(output.count("Inventory saved successfully to inventory.json."), 2)
        self.assertIn("0.8", output)
        self.assertIn("2048", output)
        for option in ["1. Display All Products", "2. Add Product", "3. Update Stock",
                       "4. Search Product", "5. Save Inventory", "6. Exit"]:
            self.assertIn(option, output)
        restarted_output, restarted_data = run_program(["1", "4", "D002", "6"], data)
        self.assertIn("Inventory loaded successfully.", restarted_output)
        self.assertIn("Keyboard", restarted_output)
        self.assertIn("Game", restarted_output)
        self.assertIn("2048", restarted_output)
        self.assertEqual(restarted_data, expected)

    def test_duplicate_id_returns_before_asking_for_type_or_other_fields(self):
        output, data = run_program(["2", "P001", "6"], MIXED_DATA)
        self.assertIn("Product ID already exists.", output)
        self.assertNotIn("Product Name:", output)
        self.assertEqual(data, MIXED_DATA)

    def test_invalid_type_returns_to_menu_without_creating_a_product(self):
        output, data = run_program(["2", "P999", "9", "6"], MIXED_DATA)
        self.assertRegex(output.lower(), r"invalid.*type|invalid.*choice|choose.*1.*2")
        self.assertNotIn("Product Name:", output)
        self.assertEqual(data, MIXED_DATA)

    def test_invalid_product_numbers_return_to_menu_without_saving_partial_product(self):
        invalid_attempts = [
            ["2", "P999", "1", "Invalid Price", "abc", "6"],
            ["2", "P999", "1", "Invalid Stock", "10", "abc", "6"],
            ["2", "P999", "1", "Invalid Weight", "10", "5", "-1", "6"],
            ["2", "D999", "2", "Invalid Size", "10", "5", "nan", "6"],
        ]
        for answers in invalid_attempts:
            with self.subTest(name=answers[3]):
                output, data = run_program(answers, MIXED_DATA)
                self.assertIn("Invalid product details:", output)
                self.assertEqual(data, MIXED_DATA)

    def test_invalid_stock_update_does_not_change_stock_or_history(self):
        output, data = run_program(["3", "D001", "1.5", "6"], MIXED_DATA)
        self.assertIn("Stock quantity must be an integer.", output)
        self.assertEqual(data, MIXED_DATA)

    def test_missing_search_update_and_invalid_menu_choice(self):
        output, data = run_program(["4", "missing", "3", "missing", "99", "6"], MIXED_DATA)
        self.assertEqual(output.count("Product not found."), 2)
        self.assertIn("Invalid option. Please choose 1 to 9.", output)
        self.assertEqual(data, MIXED_DATA)

    def test_legacy_migration_preserves_missing_and_empty_history(self):
        legacy = [
            {"id": "P001", "name": "Laptop", "price": 1200.0, "stock": 15},
            {"id": "P002", "name": "Mouse", "price": 25.5, "stock": 40, "history": []},
        ]
        _, migrated = run_program(["5", "6"], legacy)
        self.assertEqual(migrated, [dict(record, type="physical", weight=0) for record in legacy])
        _, updated = run_program(["3", "P001", "12", "3", "P002", "42", "6"], migrated)
        self.assertEqual(updated[0]["history"], [-3])
        self.assertEqual(updated[1]["history"], [2])

    def test_exit_alone_persists_added_product(self):
        _, data = run_program(["2", "D003", "2", "Free Guide", "0", "1", "2.5", "6"])
        self.assertEqual(data, [{"id": "D003", "name": "Free Guide", "price": 0.0,
                                "stock": 1, "history": [1], "type": "digital",
                                "download_size": 2.5}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
