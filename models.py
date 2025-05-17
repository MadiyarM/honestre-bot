from dataclasses import dataclass

@dataclass
class Review:
    phone: str
    city: str
    complex_name: str
    status: str
    heating: int
    electricity: int
    gas: int
    water: int
    noise: int
    mgmt: int
    rent_price: str
    likes: str
    annoy: str
    recommend: str
    # можно добавить timestamp