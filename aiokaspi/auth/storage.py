import json, os

class Storage:
    @staticmethod
    def get_session(path: str = "session.json") -> tuple[str, str, str]:
        with open(path, "r") as f:
            data = json.load(f)
        x509 = data["x509"]
        token_sn = data["token_sn"]
        user_id_hash = data["user_id_hash"]
        return x509, token_sn, user_id_hash

    @staticmethod
    def check_session(path: str = "session.json") -> bool:
        if not os.path.exists(path):
            return False
        with open(path, "r") as f:
            data = json.load(f)
            if "x509" not in data or "token_sn" not in data or "user_id_hash" not in data:
                return False
        return True

    @staticmethod
    def save_session(x509: str, token_sn: str, user_id_hash: str, path: str = "session.json") -> None:
        with open(path, "w") as f:
            json.dump({"x509": x509, "token_sn": token_sn, "user_id_hash": user_id_hash}, f, indent=4)

    @staticmethod
    def get_keys(path: str = "keys.json") -> tuple[str, str]:
        with open(path, "r") as f:
            data = json.load(f)
        return data["private_key"], data["public_key"]

    @staticmethod
    def check_keys(path: str = "keys.json") -> bool:
        if not os.path.exists(path):
            return False
        with open(path, "r") as f:
            data = json.load(f)
            if "private_key" not in data or "public_key" not in data:
                return False
        return True

    @staticmethod
    def save_keys(private_key: str, public_key: str, path: str = "keys.json") -> None:
        with open(path, "w") as f:
            json.dump({"private_key": private_key, "public_key": public_key}, f, indent=4)

    @staticmethod
    def get_device(path: str = "device.json") -> tuple[str, str, str]:
        with open(path, "r") as f:
            data = json.load(f)
        device_id = data["device_id"]
        install_id = data["install_id"]
        pin_hash = data.get("pin_hash", "")
        return device_id, install_id, pin_hash

    @staticmethod
    def check_device(path: str = "device.json") -> bool:
        if not os.path.exists(path):
            return False
        with open(path, "r") as f:
            data = json.load(f)
            if "device_id" not in data or "install_id" not in data or "pin_hash" not in data:
                return False
        return True

    @staticmethod
    def save_device(device_id: str, install_id: str, pin_hash: str, path: str = "device.json") -> None:
        with open(path, "w") as f:
            json.dump({"device_id": device_id, "install_id": install_id, "pin_hash": pin_hash}, f, indent=4)