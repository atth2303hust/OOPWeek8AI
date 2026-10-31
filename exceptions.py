# /****************/
# Mã sinh viên: 202419007
# Họ tên: Phạm Anh Tú
# /****************/
"""Ngoai le du lieu do thiet bi khong hop le."""


class InvalidDeviceReadingException(ValueError):
    def __init__(self, device_id: str, invalid_value: int):
        self.device_id = device_id
        self.invalid_value = invalid_value
        super().__init__(
            f"Thiết bị {device_id}: giá trị {invalid_value} nằm ngoài khoảng 0..100"
        )
