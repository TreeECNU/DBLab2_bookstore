#!/bin/sh
export PYTHONPATH=`pwd`
# coverage run --timid --branch --source fe,be --concurrency=thread -m pytest -v --ignore=fe/data
coverage run --timid --branch --source fe,be --concurrency=thread -m pytest -v fe/test/test_confirm_receipt.py
coverage combine
coverage report --omit="be/app.py"
coverage html
