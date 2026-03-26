from PIL import Image, ImageEnhance, ImageOps

class ImageProcessor:
    def __init__(self):
        # We can store future state here if needed
        pass

    def apply_filters(self, image: Image.Image, brightness: float = 1.0, dark_mode: bool = False) -> Image.Image:
        """
        Takes a raw image and applies the selected visual filters.
        - brightness: 1.0 is normal, 0.5 is half brightness, 1.5 is 50% brighter.
        - dark_mode: True inverts the colors.
        """
        if not image:
            return None

        # 1. Standardize the image format
        # PDFs can sometimes have transparent backgrounds (RGBA). 
        # Inverting colors works best on standard RGB.
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 2. Apply Dark Mode (Invert)
        if dark_mode:
            image = ImageOps.invert(image)

        # 3. Apply Brightness
        # We do this after dark mode so the user can dim the dark mode if it's too intense
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)

        return image
    def stitch_images(self, img1: Image.Image, img2: Image.Image) -> Image.Image:
        """Glues two images side-by-side for a two-page spread."""
        if not img1: return img2
        if not img2: return img1
        
        # Calculate the size of the new combined image
        total_width = img1.width + img2.width
        max_height = max(img1.height, img2.height)
        
        # Create a blank white canvas
        new_img = Image.new('RGB', (total_width, max_height), (255, 255, 255))
        
        # Paste the left page, then paste the right page next to it
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (img1.width, 0))
        
        return new_img