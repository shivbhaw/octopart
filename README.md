Python Client for Octopart API v3
=================================

[![CircleCI](https://circleci.com/gh/tempoautomation/octopart.svg?style=svg&circle-token=aee3e352a57741869fc0d3a62a18d64b8f4f23f9)](https://circleci.com/gh/tempoautomation/octopart)


# Quickstart

## Install

```sh
python setup.py install
export OCTOPART_API_KEY="secret"
```

## Use

```python
import octopart

mpns = ['CGA3E1X7R1E105K080AC']
res = octopart.match(mpns)
print(res[0].parts[0].manufacturer)
```

## Test

```sh
py.test --cov=octopart --doctest-modules --ignore=setup.py
python -m mypy octopart --ignore-missing-imports
```
