#!/bin/bash
# remove packages that are not part of the requirements
pip freeze | grep -v -f requirements.txt - | xargs pip uninstall -y