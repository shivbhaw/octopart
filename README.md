Python Client for Octopart API v3
=================================

[![CircleCI](https://circleci.com/gh/tempoautomation/octopart.svg?style=svg&circle-token=aee3e352a57741869fc0d3a62a18d64b8f4f23f9)](https://circleci.com/gh/tempoautomation/octopart)


# Quickstart

## Install

```sh
pip install octopart

export OCTOPART_API_KEY="secret"
```

## Use

```python
import octopart

mpns = ['6ET1']
results = octopart.match(mpns)
print(results[0].parts[0])
# <Part mpn=6ET1>

print(results[0].parts[0].manufacturer)
# 'TE Connectivity / Corcom'

print(results[0].parts[0].offers[0])
# <Offer sku=CCM1604-ND seller=Digi-Key in_stock_quantity=220>
```

## Test

```sh
python -m pytest --cov=octopart --doctest-modules --ignore=setup.py
python -m mypy octopart --ignore-missing-imports
```

# What does it do

`octopart` is an [Octopart API](https://octopart.com/api/docs/v3/rest-api) client for Python 3.6+. API response data is returned as Python objects that attempt to make it easy to get the data you want. Not all endpoints have been implemented.

## Top-level API

* `octopart.match()`
* `octopart.search()`
* `octopart.get_seller()`
* `octopart.search_seller()`
* `octopart.get_category()`
* `octopart.search_category()`
* `octopart.get_brand()`
* `octopart.search_brand()`

## Data models

* `octopart.models.PartsMatchResult`
* `octopart.models.PartsSearchResult`
* `octopart.models.Part`
* `octopart.models.PartOffer`
* `octopart.models.Seller`
* `octopart.models.Category`
* `octopart.models.Brand`
