import re
import bcrypt

# ----------------------------------------
# 1) PASSWORD VALIDATION (NO LOOPS, NO I/O)
# ----------------------------------------

def validate_password(password: str) -> tuple[bool, list]:
    """
    Validates a password against a set of common security rules.
    
    Paramaters:
    - password (str): The password string to validate.
    
    returns:
    - tuple[bool, list]: 
        - First element: True if password passes all rules, False otherwise.
        - Second element: A list of error messages for rules that failed.

    Rules checked:
    1. Minimum length of 8 characters
    2. At least one uppercase letter
    3. At least one lowercase letter
    4. At least one numeric digit
    5. At least one special character
    """

    # Initialize an empty list to collect any rule violations
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit.")

    if not re.search(r"[=_`/\\+!@#$%^&*(),.?\"':;{}|<>-]", password):
        errors.append("Password must contain at least one special character.")

    return (len(errors) == 0, errors)



# ----------------------------------------
# 2) PASSWORD STRENGTH validation
# ----------------------------------------

def validate_password_strength(password: str) -> str:
    """
    Returns basic human-readable strength evaluation.
    """

    score = 0

    # Length contribution
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1

    # Character variety
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[=_/\\+!@#$%^&*(),.?\":{}|<>-]", password): score += 1

    if score >= 5:
        return "Strong"
    elif score >= 3:
        return "Moderate"
    else:
        return "Weak"



# ----------------------------------------
# 3) HASHING
# ----------------------------------------

def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt.
    Returns UTF-8 string safe for PostgreSQL.
    """
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")



# ----------------------------------------
# 4) VERIFY HASH
# ----------------------------------------

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password using a bcrypt hash.
    Accepts hashed password stored as text.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8")
        )
    except Exception as e:
        print("Password verification error:", e)
        return False

# ----------------------------------------
# 5) student ID validation
# ----------------------------------------
def validate_student_id(student_id: str):
    """
    Validate student ID.
    Returns:
        None if valid,
        or an error message string.
    """
    if not student_id:
        return "Student ID is required."
    if " " in student_id:
        return "Student ID cannot contain spaces."
    if not student_id.isdigit():
        return "Student ID must contain numbers only."
    if len(student_id) <= 5:
        return "Student ID must be more than 5 digits."
    return None

# ----------------------------------------
# 6) email validation
# ----------------------------------------
def validate_email(email: str):
    """
    Validate email format strictly, while allowing uncommon domains.
    
    Returns:
        None if valid,
        or an error message string.
    """
    email = email.strip()
    
    # --- 1. Basic checks ---
    if not email:
        return "Email is required."
    if " " in email:
        return "Email cannot contain spaces."
    
    # --- 2. Regex check for proper email characters and structure ---
    # Local part: letters, numbers, dot, underscore, percent, plus, hyphen
    # Domain: letters, numbers, hyphen, dot, at least one dot in domain, TLD >=2 letters
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.fullmatch(pattern, email):
        return "Invalid email format."
    
    # --- 3. Optional: reject common typos for popular providers ---
    wrong_domains = {
        "gamil.com", "gmial.com", "gmai.com", "gmal.com",
        "gmaiil.com", "gmail.co", "gmail.con", "gnail.com",
        "gmail.comm", "gmai.con",
        "hotmil.com", "hotmal.com", "hotmial.com", "hotmai.com",
        "hotnail.com", "homtail.com",
        "outlok.com", "outllok.com", "ootlook.com", "outloook.com", "outloo.com"
    }
    domain = email.split("@")[1].lower()
    if domain in wrong_domains:
        return "Invalid email format."
    
    # --- 4. Passed all checks ---
    return None

# ----------------------------------------
# 7) full name validation
# ----------------------------------------
def validate_full_name(full_name: str):
    """
    Validate a full name (First Middle Last).
    Returns:
        (parts, None) if valid, where parts is [first, middle, last]
        (None, error_message) if invalid.
    """
    cleaned = " ".join(full_name.split())
    lowered = cleaned.lower()

    if not lowered.replace(" ", "").isalpha():
        return None, "Name must contain alphabetic characters only."

    parts = lowered.title().split()

    if len(parts) != 3:
        return None, "Please enter your full name (first, middle, last)."

    if any(len(p) < 3 for p in parts):
        return None, "Each name must be at least 3 characters long."

    return parts, None
