# Assignment 3: System Testing - Part D

This project tests wishlist and product comparison functions on the [OpenCart practice store](https://opencart.abstracta.us/).

| Test case | Function | Scenarios |
| --- | --- | --- |
| T010 | Add a product to the wishlist | Add one item, add it twice, and try guest access |
| T011 | Remove a wishlist item | Remove the only item, keep another item, and remove the middle item |
| T012 | Compare products | Compare details, prevent duplicates, and remove one product |

## Setup

Use Python 3.12 and run these commands inside the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Run

```sh
python -m pytest --collect-only -q
python -m pytest tests/test_10_wishlist_add.py tests/test_11_wishlist_remove.py --operator "Haoming Chen"
python -m pytest tests/test_12_compare.py --slowmo 1000 --operator "Haoming Chen"
```

Use the actual runner's name for `--operator`. Each live scenario uses a fresh browser session and creates a timestamped folder under `evidence/`. Some scenarios create a test account using an `example.net` address.

In the 24 October test run, eight scenarios passed and T011-S01 failed: after the last wishlist item was removed, the website displayed a shopping-cart empty message. The test keeps the expected wishlist message so this result can be checked again.
