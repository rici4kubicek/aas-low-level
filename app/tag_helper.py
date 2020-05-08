def tag_type_string(storage_size):
    if storage_size == 0x0f:
        return "NTAG213"
    elif storage_size == 0x11:
        return "NTAG215"
    elif storage_size == 0x13:
        return "NTAG216"
    else:
        return "Unknown"


def tag_memory_size(storage_size):
    if storage_size == 0x0f:
        return 144
    elif storage_size == 0x11:
        return 504
    elif storage_size == 0x13:
        return 888
    else:
        return 0


def tag_vendor_to_string(vendor_id):
    if vendor_id == 4:
        return "NXP"
    else:
        return "Unknown"


def tag_user_memory_offset(data):
    return 4


def tag_parse_version(data):
    back_data = {"tag_size": tag_memory_size(data["storage_size"]), "tag_type": tag_type_string(data["storage_size"]),
                 "tag_vendor": tag_vendor_to_string(data["vendor_id"]), "tag_protocol": data["protocol_type"],
                 "user_memory_offset": tag_user_memory_offset(data)}
    return back_data