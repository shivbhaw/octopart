# Python Client for Octopart API v3

[![Build Status](https://travis-ci.com/tempoautomation/octopart.svg?token=Cp2eqGgyd7Y9dCG3JbgE&branch=develop)](https://travis-ci.com/tempoautomation/octopart)

[![Coverage Status](https://coveralls.io/repos/github/tempoautomation/octopart/badge.svg?t=s1mBG7)](https://coveralls.io/github/tempoautomation/octopart)


# Quickstart

Install

```sh
python setup.py install
export OCTOPART_API_KEY="secret"
```

Use

```
import octopart

mpns = ['CGA3E1X7R1E105K080AC']
res = octopart.match(mpns)
print(res[0].parts[0].manufacturer)
```
