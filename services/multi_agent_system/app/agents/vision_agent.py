from typing import Any


def extract_from_image(
    image_base64: str | None,
    image_url: str | None,
) -> dict[str, Any]:
    """
    Vision Agent placeholder.

    Later this can use OCR or a vision-capable model.
    """

    has_image = bool(image_base64 or image_url)

    if not has_image:
        return {
            "status": "no_image",
            "needs_user_clarification": True,
            "question": "Please upload an image or type the amount, category, and date.",
            "extracted_data": {},
        }

    return {
        "status": "not_implemented_yet",
        "needs_user_clarification": True,
        "question": "Image extraction is planned. For now, please type the amount, category, and date.",
        "extracted_data": {},
    }