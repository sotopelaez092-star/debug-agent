# ImportError Test Cases

This directory contains 5 comprehensive ImportError test cases designed to challenge debugging agents with realistic, hard-to-diagnose import issues.

## Test Case Overview

### Case 01: Nested Package Structure
**Directory:** `case_01_nested_package/`
**Files:** 11 Python files + 1 metadata.json
**Error Type:** Incorrect import path in deeply nested package structure

**Structure:**
```
app/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── authentication.py
│   ├── database.py
│   └── data/
│       ├── __init__.py
│       ├── validators.py
│       ├── transformers.py
│       └── processors/
│           ├── __init__.py
│           ├── text_processor.py
│           └── json_processor.py
└── main.py
```

**Error:** `ModuleNotFoundError: No module named 'app.services.processors'`
**Root Cause:** Import statement uses `app.services.processors.json_processor` but actual path is `app.services.data.processors.json_processor` (missing 'data' level)
**Difficulty:** Requires navigating 4 levels of package nesting to identify the correct path

---

### Case 02: Conditional Import
**Directory:** `case_02_conditional_import/`
**Files:** 8 Python files + 1 metadata.json
**Error Type:** Conditional import with wrong module name

**Structure:**
```
config/
├── __init__.py (contains conditional imports)
├── base_config.py
├── dev_config.py
├── production_config.py
├── staging_config.py
└── testing_config.py
app.py
main.py
```

**Error:** `ModuleNotFoundError: No module named 'config.test_config'`
**Root Cause:** When `APP_ENV='testing'`, the code tries to import `from .test_config import TestConfig` but the file is named `testing_config.py`
**Difficulty:** Error only occurs with specific environment variable setting; requires understanding environment-based configuration

---

### Case 03: Dynamic Import
**Directory:** `case_03_dynamic_import/`
**Files:** 8 Python files + 1 metadata.json
**Error Type:** Wrong module path in plugin registry used by dynamic import system

**Structure:**
```
plugins/
├── __init__.py
├── base_plugin.py
├── data_processor_plugin.py
├── validation_plugin.py
├── analytics_plugin.py
└── data_transformer_plugin.py
plugin_manager.py
main.py
```

**Error:** `No module named 'plugins.transformer_plugin'`
**Root Cause:** Plugin registry dictionary maps 'transformer' to `plugins.transformer_plugin.DataTransformerPlugin` but actual file is `data_transformer_plugin.py`
**Difficulty:** Error occurs at runtime through importlib; requires inspecting plugin_registry dictionary and understanding dynamic loading mechanism

---

### Case 04: Relative Import
**Directory:** `case_04_relative_import/`
**Files:** 12 Python files + 1 metadata.json
**Error Type:** Invalid relative import across sibling packages

**Structure:**
```
package_a/
├── __init__.py
├── constants.py
├── utilities.py
└── submodule_x/
    ├── __init__.py
    ├── processor.py
    └── analyzer.py
package_b/
├── __init__.py
├── helpers.py
├── coordinator.py
└── submodule_y/
    ├── __init__.py
    └── report_generator.py
main.py
```

**Error:** `ImportError: attempted relative import beyond top-level package`
**Root Cause:** `report_generator.py` in `package_b/submodule_y/` tries to use `from ...package_a.utilities import serialize_data`, but package_a and package_b are siblings, not parent-child
**Difficulty:** Requires understanding Python's relative import rules and package relationships; needs to change to absolute imports

---

### Case 05: Shadowed Module
**Directory:** `case_05_shadowed_module/`
**Files:** 8 Python files + 1 metadata.json
**Error Type:** Local module shadows Python standard library

**Structure:**
```
utils/
├── __init__.py
├── file_operations.py
└── text_processing.py
random.py (shadows stdlib!)
game.py
data_processor.py
simulator.py
main.py
```

**Error:** `AttributeError: module 'random' has no attribute 'shuffle'`
**Root Cause:** Local `random.py` file shadows Python's standard library `random` module. Local version only implements `randint()` and `choice()`, but code tries to use `shuffle()`, `sample()`, and `seed()`
**Difficulty:** Error is AttributeError, not ImportError; requires recognizing module shadowing pattern; affects multiple files; solution requires renaming local module

---

## Common Characteristics

All test cases share these properties:
- **difficulty:** "hard"
- **requires_exploration:** true
- **5+ Python files** with realistic, working code
- **Detailed metadata.json** with error info, fix description, and complexity factors
- **Multiple complexity factors** that make the issue non-trivial to diagnose
- **Realistic code patterns** found in actual Python projects

## Running the Tests

Each case can be run independently:
```bash
cd case_XX_<name>
python main.py
```

All cases will produce the expected error when run.
