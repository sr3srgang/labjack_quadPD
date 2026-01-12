class Device:
    def __init__(self, device_type):
        self._device_type = device_type


d = Device("Laser")
print(d._device_type)  # prints "Laser"
