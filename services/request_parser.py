import json


def parse_request_json(raw_request):
    payload = json.loads(raw_request)

    return {
        "itemId": payload.get("itemId"),
        "mcId": int(payload["mcId"]),
        "mcTitle": payload["mcTitle"],
        "description": payload["description"],
    }

