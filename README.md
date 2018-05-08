Python Client for Octopart API v3
=================================

[![CircleCI](https://circleci.com/gh/tempoautomation/octopart.svg?style=svg&circle-token=aee3e352a57741869fc0d3a62a18d64b8f4f23f9)](https://circleci.com/gh/tempoautomation/octopart)


# Quickstart

## Install

```sh
pip install octopart
python setup.py install
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

`octopart` requests data from [Octopart API](https://octopart.com/api/docs/v3/rest-api) endpoints,
and returns response data as Python objects. Not all endpoints have been implemented.

## Top-level API

* `octopart.api.match()`
* `octopart.api.search()`
* `octopart.api.get_brand()`
* `octopart.api.search_brand()`
* `octopart.api.get_category()`
* `octopart.api.search_category()`
* `octopart.api.get_seller()`
* `octopart.api.search_seller()`

## Data models

* `octopart.models.PartsMatchResult`
* `octopart.models.PartsSearchResult`
* `octopart.models.Part`
* `octopart.models.PartOffer`
* `octopart.models.Brand`
* `octopart.models.Category`
* `octopart.models.Seller`
