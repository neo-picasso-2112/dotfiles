# How to Validate Data and Manage Settings with Pydantic

This guide describes how to use the Pydantic library in Python to effectively validate data structures and manage application settings.

## Goal

To implement robust data validation for Python objects and function arguments, and to manage application configuration using Pydantic's core features.

## Prerequisites

*   Python installed (version 3.7+ recommended for features like `Annotated`).
*   `pip` package installer available.
*   Basic understanding of Python syntax, object-oriented programming (classes), and type hints.
*   A terminal or command prompt.

## Steps

Follow these steps to install Pydantic and utilize its features for data validation and settings management.

### 1. Install Pydantic

Install the core Pydantic library using pip. It's recommended to do this within a virtual environment.

```bash
# Activate your virtual environment first
python -m pip install pydantic
```

For specific validation types (like email) or settings management, install optional dependencies:

```bash
# For email validation
python -m pip install "pydantic[email]"

# For settings management
python -m pip install pydantic-settings
```

### 2. Define Data Schemas with `BaseModel`

Use `BaseModel` to define the structure and types of your data. Pydantic automatically validates data upon model instantiation.

```python
from datetime import date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, EmailStr

class Department(Enum):
    HR = "HR"
    SALES = "SALES"
    IT = "IT"
    ENGINEERING = "ENGINEERING"

class Employee(BaseModel):
    employee_id: UUID = uuid4()
    name: str
    email: EmailStr
    date_of_birth: date
    salary: float
    department: Department
    elected_benefits: bool

# Example instantiation (Pydantic validates and coerces types)
try:
    employee = Employee(
        name="Chris DeTuma",
        email="cdetuma@example.com",
        date_of_birth="1998-04-02", # String is parsed to date
        salary=123_000.00,
        department="IT",           # String is matched to Enum
        elected_benefits=True,
    )
    print(employee)
except ValidationError as e:
    print(e)

# Validate from dictionary or JSON
employee_dict = { ... }
employee_json = """{ ... }"""
employee_from_dict = Employee.model_validate(employee_dict)
employee_from_json = Employee.model_validate_json(employee_json)

# Serialize to dictionary or JSON
dict_output = employee.model_dump()
json_output = employee.model_dump_json()

# Generate JSON Schema
schema = Employee.model_json_schema()
print(schema)
```

### 3. Customize Field Validation with `Field`

Use `Field` to add metadata and constraints beyond basic type checking to your model fields.

```python
from pydantic import Field, HttpUrl

class Employee(BaseModel):
    employee_id: UUID = Field(default_factory=uuid4, frozen=True)
    name: str = Field(min_length=1, frozen=True)
    email: EmailStr = Field(pattern=r".+@example\.com$") # Regex pattern
    date_of_birth: date = Field(alias="birth_date", repr=False, frozen=True) # Alias, hide in repr
    salary: float = Field(alias="compensation", gt=0, repr=False) # Greater than 0
    department: Department
    elected_benefits: bool

# Instantiation using aliases
employee_data = {
    "name": "Clyde Harwell",
    "email": "charwell@example.com",
    "birth_date": "2000-06-12",     # Using alias
    "compensation": 100_000,        # Using alias
    "department": "ENGINEERING",
    "elected_benefits": True,
}
employee = Employee.model_validate(employee_data)

# Attempting to modify a frozen field will raise an error
# employee.name = "New Name" # Raises ValidationError
```

### 4. Implement Custom Validation Logic with Validators

Use `@field_validator` for custom logic on a single field and `@model_validator` for validation involving multiple fields or the entire model.

```python
from pydantic import field_validator, model_validator
from typing import Self # Use typing_extensions for Python < 3.11

class Employee(BaseModel):
    # ... (fields as defined before) ...

    @field_validator("date_of_birth")
    @classmethod
    def check_valid_age(cls, date_of_birth: date) -> date:
        today = date.today()
        eighteen_years_ago = date(today.year - 18, today.month, today.day)
        if date_of_birth > eighteen_years_ago:
            raise ValueError("Employees must be at least 18 years old.")
        return date_of_birth

    @model_validator(mode="after")
    def check_it_benefits(self) -> Self:
        if self.department == Department.IT and self.elected_benefits:
            raise ValueError(
                "IT employees are contractors and don't qualify for benefits"
            )
        return self
```

### 5. Validate Function Arguments with `@validate_call`

Apply Pydantic validation rules directly to function arguments using the `@validate_call` decorator. Use `Annotated` for applying `Field` constraints.

```python
from typing import Annotated
from pydantic import PositiveFloat, Field, EmailStr, validate_call

@validate_call
def send_invoice(
    client_name: Annotated[str, Field(min_length=1)],
    client_email: EmailStr,
    items_purchased: list[str],
    amount_owed: PositiveFloat,
) -> str:
    # Function logic here...
    email_str = f"Invoice details for {client_name}..."
    print(f"Sending email to {client_email}...")
    return email_str

# Calling with invalid arguments will raise ValidationError
try:
    send_invoice(client_name="", client_email="invalid-email", items_purchased=[], amount_owed=-10)
except ValidationError as e:
    print(e)
```

### 6. Manage Application Settings with `BaseSettings`

Use `BaseSettings` from `pydantic-settings` to load configuration from environment variables or `.env` files, applying Pydantic validation rules.

```python
# settings_management.py
from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    # Configure settings source and behavior
    model_config = SettingsConfigDict(
        env_file=".env",              # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,         # Match env vars case-insensitively (default)
        extra="ignore"                # Ignore extra fields in env (default)
        # Use extra="forbid" to raise error on extra fields
        # Use case_sensitive=True for strict matching
    )

    database_host: HttpUrl
    database_user: str = Field(min_length=5)
    database_password: str = Field(min_length=10)
    api_key: str = Field(min_length=20)

# Example .env file:
# DATABASE_HOST=http://db.example.com
# DATABASE_USER=myuser
# DATABASE_PASSWORD=mypassword123
# API_KEY=abcdefghijklmnopqrstuvwxyz

# In your application code:
try:
    config = AppConfig()
    print(f"Connecting to DB: {config.database_host} as {config.database_user}")
    # Use config.api_key, etc.
except ValidationError as e:
    print("Configuration error:", e)

```

## Conclusion

You have learned how to use Pydantic to:
*   Define clear data schemas using `BaseModel`.
*   Apply built-in and custom validation rules using `Field`, `@field_validator`, and `@model_validator`.
*   Validate function arguments automatically with `@validate_call`.
*   Manage application settings robustly using `BaseSettings` and environment variables or `.env` files.

Integrating Pydantic enhances code reliability, readability, and maintainability by ensuring data conforms to expected structures and constraints.

## Further Reading

*   [Pydantic Official Documentation](https://docs.pydantic.dev/)
*   [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
*   [Real Python Pydantic Article](https://realpython.com/python-pydantic/) (Original source for this guide)
```
