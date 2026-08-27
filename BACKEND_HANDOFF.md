# PickleBuddy Backend Handoff

## Current frontend-supported flows

- Player, owner, and admin roles
- Private court booking
- Open Play booking with seat counts
- Whole-gym booking
- Pasalo resale/transfer flow
- Manual payment flow via owner-uploaded QR methods
- Owner-side payment proof review and booking approval
- Admin-side owner monitoring, settlement status, and owner lock/suspension
- Rental gear attached to bookings

## Immediate schema gaps to fix

### 1. Bookings need booking mode fields

The frontend uses:

- `private`
- `open_play`
- `whole_gym`

Add to `bookings`:

- `booking_type`
- `participant_count`
- nullable `court_id` or a separate booking target model

Whole-gym bookings should not depend on a fake court record.

### 2. Open Play capacity is not modeled

The frontend tracks:

- court booking mode
- open play capacity per court
- seats taken per date/slot

Add to `courts`:

- `booking_mode`
- `open_play_capacity`

### 3. Venue-wide booking setup is missing

The frontend supports whole-gym booking configuration per venue:

- enabled flag
- price per hour
- allowed slots
- notes

This should live in a dedicated table such as `venue_booking_settings` and `venue_available_slots`.

### 4. Transactions and booking payments overlap

Right now `transactions` and `booking_payments` both carry payment data.

Recommended split:

- `bookings`: booking lifecycle
- `booking_payments`: customer payment proof and owner review
- `owner_settlements`: what owner owes the platform/admin

Keep `transactions` only if you want a reporting ledger. If so, make it derived/audit-focused, not the primary payment state store.

### 5. Pasalo transfer is incomplete at schema level

You already have `pasalo_offers` and `pasalo_transfers`, but the final ownership transfer rule needs to be explicit:

- seller creates offer
- claimant uploads proof
- owner reviews
- only after approval does booking ownership move to claimant

Do not transfer the booking to the claimant before approval.

### 6. Admin settlement state is not persisted

The frontend already uses:

- paid
- unpaid
- suspended / locked owner access

Add owner settlement fields or tables:

- `owners.system_payment_status`
- `owners.suspension_reason`
- `owner_settlements`
- `owner_settlement_items`

### 7. Rental gear is frontend-only

Add:

- `rental_items`
- `booking_rentals`

This is already part of the booking UX and should be persisted before backend wiring starts.

### 8. File uploads need a real storage contract

Current frontend flows upload:

- venue QR codes
- booking payment receipts
- pasalo transfer receipts
- gym/court images

Decide now:

- local dev storage path
- production object storage target
- DB stores URL/path + original file name + MIME type

## Recommended MySQL tables

- `players`
- `owners`
- `admins`
- `venues`
- `courts`
- `court_slots`
- `venue_booking_settings`
- `venue_payment_methods`
- `rental_items`
- `bookings`
- `booking_slots`
- `booking_payments`
- `booking_rentals`
- `pasalo_offers`
- `pasalo_claims`
- `owner_settlements`
- `notifications`

## Recommended booking rules

### Private booking

- one booking reserves one court for one or more slots
- conflict check must happen server-side in a transaction

### Open Play

- booking type is `open_play`
- multiple players can join same court/date/slot
- enforce `sum(participant_count) <= open_play_capacity`

### Whole gym

- booking type is `whole_gym`
- blocks all courts in that venue for those slots
- conflict check must reject private/open-play bookings on overlapping slots

### Pasalo

- only confirmed private bookings can be offered
- open pasalo should keep the slot blocked
- claimant submits proof
- owner approves/rejects
- on approval, transfer booking ownership and close offer

## Recommended FastAPI modules

- `app/modules/auth`
- `app/modules/players`
- `app/modules/owners`
- `app/modules/admin`
- `app/modules/venues`
- `app/modules/courts`
- `app/modules/bookings`
- `app/modules/payments`
- `app/modules/pasalo`
- `app/modules/reports`
- `app/modules/uploads`
- `app/modules/notifications`

## First API surface to build

- `POST /auth/login`
- `GET /owners/me`
- `GET /players/me`
- `GET /venues`
- `GET /venues/{venue_id}`
- `POST /owners/venues`
- `POST /owners/venues/{venue_id}/payment-methods`
- `POST /owners/venues/{venue_id}/courts`
- `POST /bookings`
- `GET /bookings/me`
- `POST /bookings/{booking_id}/payment-proof`
- `POST /bookings/{booking_id}/approve`
- `POST /bookings/{booking_id}/reject`
- `POST /pasalo/offers`
- `POST /pasalo/offers/{offer_id}/claim`
- `POST /pasalo/claims/{claim_id}/approve`
- `POST /pasalo/claims/{claim_id}/reject`
- `GET /owners/transactions`
- `GET /admin/owners`
- `POST /admin/owners/{owner_id}/lock`
- `POST /admin/owners/{owner_id}/unlock`

## Backend priorities

1. Auth and role enforcement
2. Venue/court/payment-method CRUD
3. Booking creation with hard conflict checks
4. Manual payment proof upload and owner approval
5. Open Play capacity enforcement
6. Whole-gym blocking rules
7. Pasalo approval flow
8. Admin owner settlement/lock flow

## Important implementation notes

- Use UUID/public IDs externally, numeric IDs internally.
- Keep booking status separate from payment status.
- Store slots in normalized rows, not JSON, if you want reliable conflict checks.
- Use DB transactions for booking create/approve/transfer flows.
- Add audit fields for approval actions: actor, timestamp, note.
- Do not trust client-side seat counts, slot availability, or owner lock state.
