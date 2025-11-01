# Testing Guide

This document describes how to run and extend the project's tests.

## Backend (Python)

- Run unit and integration tests with `pytest`.
- Example property-based test added using `hypothesis` in `backend/tests/test_hypothesis_example.py`.
- To collect coverage: `pytest --cov=./` (requires `pytest-cov`).

## Frontend (TypeScript/React)

- Run unit tests: `npm run test` (Vitest)
- Run e2e tests: `npm run test:e2e` (Playwright)
- Example component tests are in `frontend/src/test/`.
- Use `vitest --coverage` to collect frontend coverage.

## Recommendations

- Add MSW for API mocking in frontend tests.
- Add seed data fixtures for reproducible DB state during backend tests.
- Use Locust for load testing critical API endpoints.

