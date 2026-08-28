# Frontend Integration: Program Registration & HitPay Payment

This guide explains the 2-step process to handle program registrations with integrated HitPay payments.

---

## Step 1: Program Registration (The Data Step)

When the user clicks "Register" in your UI, you must send their details to the backend.

### Request
- **Endpoint**: `POST /api/programs/{program_id}/register`
- **Headers**: `Authorization: Bearer <token>`
- **Payload**:
  ```json
  {
    "pay_full": true, // or false if allowing deposit
    "nric_last_4": "1234",
    "preferred_language": "Tamil",
    "meal_preference": "Vegetarian",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+60123456789",
    "emergency_contact_relation": "Spouse",
    "discovery_source": "Facebook"
  }
  ```

### Handling the Response
The backend will return a `payment_url` if the program has a cost.

```javascript
const handleRegistration = async (formData) => {
  try {
    const response = await api.post(`/programs/${programId}/register`, formData);
    
    if (response.data.payment_url) {
      // PROCEED TO STEP 2
      initiatePayment(response.data.payment_url);
    } else {
      // If price was 0, registration is done!
      alert("Registration Successful!");
    }
  } catch (error) {
    console.error("Registration failed", error);
  }
};
```

---

## Step 2: HitPay Payment (The Checkout Step)

Once you have the `payment_url`, you need to show it to the user.

### Option A: Direct Redirect (Recommended)
This is the simplest and most reliable method.
```javascript
const initiatePayment = (url) => {
  // Redirect the current window to HitPay
  window.location.href = url;
};
```

### Option B: New Tab / Popup
If you want to keep your app open in the background.
```javascript
const initiatePayment = (url) => {
  // Open HitPay in a new tab
  window.open(url, '_blank');
};
```

### Option C: HitPay Payment Element (Premium JS SDK)
If you want to keep the user on your site and use HitPay's embedded checkout.

```javascript
const handleRegistration = async (formData) => {
  const response = await api.post(`/programs/${programId}/register`, formData);
  const { payment_request_id, payment_signature } = response.data;

  if (payment_request_id) {
    // Initialize HitPay JS SDK (Ensure SDK is loaded)
    window.HitPay.initialize({
      payment_request_id: payment_request_id,
      signature: payment_signature,
      is_test: true // Set based on your environment
    });
    
    // Show the payment element
    window.HitPay.toggle();
  }
};
```

---

## Step 3: The Return (Success Handling)

After the user pays on HitPay, they will be redirected back to your `FRONTEND_URL` (configured in the backend `.env`).

### The Success URL
The user will land on:
`http://localhost:3000/payment/success?reg_id=xxxxx`

### What to do on the Success Page:
1. **Show a Thank You message**: "We have received your registration."
2. **Poll for Status (Optional)**: Since the payment is processed via webhook in the background, the status might stay "Pending" for a few seconds. You can call your "My Registrations" API to check when it changes to "Completed".

---

## Troubleshooting Checklist for Frontend
- **Missing payment_url?**: Check if the Program actually has a `price` set in the Admin Panel.
- **CORS Error?**: Ensure your frontend URL is added to the `CORS_ORIGINS` in the backend `.env`.
- **HitPay Error?**: If the backend returns a 500 error during registration, check the backend logs. It usually means HitPay keys are missing or invalid.
