import random
import string

def generate_promocode(length=8):
    """Generate a single random promocode"""
    # Use only uppercase letters and digits
    characters = string.ascii_uppercase + string.digits
    # Ensure the promocode doesn't start with a digit
    first_char = random.choice(string.ascii_uppercase)
    # Generate the rest of the promocode
    rest_of_code = ''.join(random.choice(characters) for _ in range(length - 1))
    return first_char + rest_of_code

def generate_promocodes(count, length=8):
    """Generate multiple unique promocodes"""
    promocodes = set()
    while len(promocodes) < count:
        promocodes.add(generate_promocode(length))
    return list(promocodes)