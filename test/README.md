# DeepInsight Test Suite

This directory contains test scripts and test data for the DeepInsight project.

## Test Scripts

Run all tests from the project root directory using:
```bash
python test/<script_name>.py
```

### Available Test Scripts

- **`test_system.py`** - Basic system integration tests
- **`test_enhanced_direct.py`** - Direct unit tests for enhanced extraction components
- **`test_enhanced_extraction.py`** - End-to-end integration test with test_doc.pdf
- **`test_feature_flags.py`** - Feature flag functionality tests
- **`test_name_normalization.py`** - Entity name normalization and deduplication tests
- **`test_turkish_airlines_fix.py`** - Specific test for the Turkish Airlines case issue fix

### Test Data

The `testdata/` directory contains:
- **`test_doc.pdf`** - Sample document for end-to-end testing
- **`extraction_*_results.json`** - Sample extraction results for analysis
- **`*_ontology.json`** - Sample ontologies for testing

### Running Tests

Examples:
```bash
# Test name normalization functionality
python test/test_name_normalization.py

# Test Turkish Airlines duplication fix
python test/test_turkish_airlines_fix.py

# Full end-to-end test (requires running backend)
python test/test_enhanced_extraction.py
```

### Notes

- Tests require the backend to be running on `localhost:8000` for integration tests
- Unit tests can run independently
- Test data in `testdata/` is gitignored to avoid committing large files