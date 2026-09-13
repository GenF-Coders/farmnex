def ok(data=None, message="Success", **extra):
    payload = {"success": True, "message": message, "data": data}
    payload.update(extra)
    return payload
