import base64
import mimetypes
import os

def encode_image_to_base64(image_path):
    """
    Encode an image file to a base64 string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: A base64 encoded string of the image.
    """
    # Determine the mime type of the image
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        raise ValueError(f"Could not determine the mime type for the file: {image_path}")

    # Read the image file and encode it to base64
    with open(image_path, "rb") as image_file:
        base64_encoded_str = base64.b64encode(image_file.read()).decode('utf-8')

    return f"data:{mime_type};base64,{base64_encoded_str}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert an image to a base64 encoded string for embedding in HTML.")
    parser.add_argument("image_path", help="Path to the image file")
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"The file {args.image_path} does not exist.")
        return

    try:
        base64_encoded_image = encode_image_to_base64(args.image_path)
        print("Base64 encoded image string:")
        print(f"<img src=\"{base64_encoded_image}\"")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
