# Assistant Code Style

Python:

- use explicit names over terse names
- prefer small pure functions for generation logic where practical
- add docstrings to public interfaces
- keep module imports grouped and stable
- avoid magical constants; promote them to named constants or config values

Documentation:

- write in concise technical English
- document assumptions, not just mechanics
- keep README content high signal

Testing:

- test deterministic behavior using fixed random seeds
- cover schema shape, date coverage, and write path behavior
- avoid tests that depend on network access
