# Cat Breed Recognition System Tests

This folder contains unit tests for the Cat Breed Recognition System, used to verify that each functional module works correctly.

## Test Structure

The test code is divided into the following main parts:

- `test_model.py`: Tests model loading and image-processing functionality  
- `test_auth.py`: Tests user authentication-related functionality  
- `test_recognition.py`: Tests the core cat breed recognition functionality  
- `test_database.py`: Tests database operations  
- `test_file_handling.py`: Tests file upload and handling  
- `conftest.py`: Defines test fixtures and configuration  

## Environment Setup

1. Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

2. Ensure the project includes a `model` directory containing at least one `.h5` model file.

## Running the Tests

### Run All Tests

```bash
pytest -v tests/
```

### Run Specific Test Files

```bash
pytest -v tests/test_model.py
pytest -v tests/test_auth.py
```

### Run Tests with Coverage Report

```bash
pytest --cov=app tests/
```

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

## Test Details

1. Tests use various mocking techniques to avoid dependencies on the real database and file system.  
2. Most tests use `monkeypatch` to mock external dependencies (e.g., database connections, file operations, and deep-learning models).  
3. `conftest.py` defines several fixtures that can be shared across different tests.  

## Interpreting Test Results

- **PASSED (.)**: Test passed  
- **FAILED (F)**: Test failed  
- **SKIPPED (s)**: Test skipped  
- **ERROR (E)**: An error occurred during test execution  

## Troubleshooting

1. If you encounter import errors, ensure the project root is on the Python path and that each test file imports the modules under test correctly.  
2. If file-path–related tests fail, it may be due to differences in OS path separators—please check your path-building logic.  
3. For model-related tests, ensure TensorFlow is installed correctly and the model files are accessible. 