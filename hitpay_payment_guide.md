# HitPay Payment Integration Guide

This document explains the technical flow for integrating HitPay payments into the Meditation Program registration process.

## 1. Environment Configuration
Ensure your `.env` file contains the following credentials from your HitPay Dashboard (Developers section):

```bash
HITPAY_API_KEY=your_api_key_here
HITPAY_SALT=your_salt_here
HITPAY_IS_TEST=true # Set to false for production
```

---

## 2. The Payment Flow

### Step A: User Registration
When a user registers for a program, the frontend sends the registration data along with a `pay_full` boolean.

- **Endpoint**: `POST /api/programs/{program_id}/register`
- **Payload Example**:
  ```json
  {
    "pay_full": false, // If true, pays full price. If false, pays deposit.
    "nric_last_4": "1234",
    ... (other registration fields)
  }
  ```

### Step B: Payment Initiation (Backend)
1. The backend calculates the `amount_to_pay` based on the program's `price` and `minimum_deposit`.
2. The backend calls the `HitPayService` to create a payment request.
3. A record is created in the `payments` table with status `pending`.

### Step C: Redirect User (Frontend)
The API response includes a `payment_url`. The frontend must redirect the user to this URL.

- **Response Example**:
  ```json
  {
    "id": "registration-uuid",
    "payment_url": "https://securecheckout.sandbox.hit-pay.com/...",
    "payment_request_id": "a1a77a07-fd0f-4a4a-8536-55aa3be12cec",
    "payment_signature": "43cf059f17a41c894b132f041f560aaba217aeffd03b62aff2164adc5c0bde3c",
    "payment_status": "Pending",
    "balance_amount": 50.0
  }
  ```

### Step D: Webhook Notification (HitPay -> Backend)
Once the user completes the payment on HitPay's site:
1. HitPay sends a `POST` request to `/api/payments/webhook`.
2. **Security**: The backend verifies the `Hitpay-Signature` header using HMAC-SHA256 and your `HITPAY_SALT`.
3. If valid, the backend updates:
   - The `Payment` record status to `completed`.
   - The `ProgramRegistration` record: increases `amount_paid` and decreases `balance_amount`.
   - Sets `payment_status` to `PARTIAL` or `COMPLETED`.

---

## 3. Testing Locally
For local development, your frontend can run on `http://localhost:3000`. However, HitPay webhooks need to reach your local backend, so you must use a public tunnel for the **APP_URL**:

1. Run a tunnel (ngrok or cloudflare): `ngrok http 8000`
2. Copy the public URL (e.g., `https://xyz.ngrok-free.app`).
3. Update your `.env`:
   - `APP_URL=https://xyz.ngrok-free.app`
   - `FRONTEND_URL=http://localhost:3000`
4. Update your HitPay Dashboard Webhook URL to: `https://xyz.ngrok-free.app/api/payments/webhook`.

### Step E: Paying Balance Amount
If the user made a partial payment, they can complete the payment later using the `pay-balance` route.

1. **Endpoint**: `POST /api/payments/pay-balance/{registration_id}`
2. **Logic**: The backend calculates the remaining balance and generates a new HitPay link.
3. **Flow**: Frontend redirects the user to the returned `payment_url`.
4. **Completion**: Once paid, the webhook updates the registration to `COMPLETED`.

---

## 4. Payment Statuses
- **Pending**: Registration created, but no payment received yet.
- **Partial**: Deposit paid, balance remaining.
- **Completed**: Full price paid.
- **Failed**: The transaction was rejected or timed out.

## 5. Security Note
Never share your `HITPAY_SALT` or `HITPAY_API_KEY`. The signature verification logic in `app/services/hitpay.py` ensures that only legitimate notifications from HitPay are processed.
