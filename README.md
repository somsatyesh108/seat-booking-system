# Concurrent Seat Booking System

A movie/bus/event seat booking system that prevents double-booking under heavy concurrency.

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (Docker)
- **Seat holds:** Redis with 5-minute auto-expiry (`SET NX EX`)
- **Frontend:** React

## Run the databases locally
~~~bash
cp .env.example .env      # then edit .env
docker compose up -d
docker compose ps         # both should show (healthy)
~~~

_Work in progress. Full documentation and screenshots coming soon._
