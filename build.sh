git update-index --chmod=+x build.sh

#!/usr/bin/env bash
# Build commands for Render
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate