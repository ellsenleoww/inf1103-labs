from dataclasses import dataclass
from product_record import ProductRecord


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    contact_email: str

    def display_information(self) -> None:
        print("Supplier ID:", self.supplier_id)
        print("Supplier:", self.name)
        print("Contact email:", self.contact_email)


UNKNOWN_SUPPLIER = Supplier("", "Supplier not recorded", "")


def supplier_from_record(data: ProductRecord) -> Supplier:
    record = data.get("supplier")
    return Supplier(**record) if record is not None else UNKNOWN_SUPPLIER
