# Free API Test

This directory contains tests and examples for the Free API functionality.

## Overview

This test suite is designed to verify the functionality of the Free API, which provides access to AI models through OpenRouter.

## Requirements

- Python 3.7+
- requests library
- Valid OpenRouter API key

## Installation

1. Install required dependencies:
```bash
pip install requests
```

2. Configure your API key in the `.env` file:
```properties
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

### Running Tests

Execute the test script:
```bash
python test_free_api.py
```

### Example Usage

See `example_free_api.py` for a simple example of how to use the Free API.

## API Endpoints

- Base URL: `https://openrouter.ai/api/v1/chat/completions`
- Model: `openrouter/free`

## Notes

- The Free API has rate limits and usage quotas
- Monitor your usage through the OpenRouter dashboard
- For production use, consider upgrading to a paid plan
