#!/bin/bash
pytest --cov=. --cov-config=tool_coverage.ini --cache-clear -n 3 ./tests/
