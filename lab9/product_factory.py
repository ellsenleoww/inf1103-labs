from product import Product
from product_record import ProductRecord
from supplier import Supplier, UNKNOWN_SUPPLIER, supplier_from_record
from physical_product import PhysicalProduct
from digital_product import DigitalProduct


class ProductFactory:
    __product_classes: dict[str, type[Product]] = {
        "physical": PhysicalProduct,
        "digital": DigitalProduct,
    }

    @staticmethod
    def create(
        product_type: str,
        product_id: str,
        name: str,
        price: float,
        stock_quantity: int,
        supplier: Supplier = UNKNOWN_SUPPLIER,
        *,
        weight: float = 0.0,
        download_size: float = 0.0,
        history: list[int] | None = None,
    ) -> Product:
        data: ProductRecord = {
            "type": product_type,
            "id": product_id,
            "name": name,
            "price": price,
            "stock": stock_quantity,
            "weight": weight,
            "download_size": download_size,
            "history": [stock_quantity] if history is None else history,
        }
        return ProductFactory.from_record(data, supplier)

    @staticmethod
    def from_record(data: ProductRecord, supplier: Supplier | None = None) -> Product:
        if "type" not in data:
            data = dict(data, type="physical", weight=0.0)
        product_type = data["type"]
        product_class = ProductFactory.__product_classes.get(product_type)
        if product_class is None:
            raise ValueError(f"Unknown product type: {product_type}")
        if supplier is None:
            supplier = supplier_from_record(data)
        return product_class.from_dict(data, supplier)
