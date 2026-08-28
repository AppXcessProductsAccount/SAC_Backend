# Authentication & RBAC User Guide

This guide provides the API documentation for the Authentication, OTP, and Role-Based Access Control (RBAC) system.

## 1. Authentication Concept
The system uses **OTP (One-Time Password)** for standard users and **Password-based login** for Admins. Both flows return a **JWT Access Token** (short-lived) and a **JWT Refresh Token** (long-lived).

- **User Flow**: Send OTP -> Verify OTP -> Receive Tokens.
- **Admin Flow**: Login with Email/Password -> Receive Tokens.

---

## 2. Authentication Routes

### A. Send OTP (Signup/Login)
Trigger an email containing a 6-digit verification code.
- **URL**: `/api/auth/send-otp`
- **Method**: `POST`

**Payload:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "OTP sent successfully"
}
```

---

### B. Verify OTP
Verify the code and receive your session tokens.
- **URL**: `/api/auth/verify-otp`
- **Method**: `POST`

**Payload:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-v4-string",
    "name": "user",
    "email": "user@example.com",
    "role": "USER",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-04-28T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "refresh_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
}
```

---

### C. Admin Login
Standard password login for accounts with `ADMIN` or `SUPER_ADMIN` roles.
- **URL**: `/api/auth/login`
- **Method**: `POST`

**Payload:**
```json
{
  "email": "admin@example.com",
  "password": "your-secure-password"
}
```

**Response (200 OK):**
Same structure as **Verify OTP**.

---

## 3. Profile Management

> [!IMPORTANT]
> These routes require the `Authorization: Bearer <access_token>` header.

### A. Get My Profile
Retrieve details for the currently logged-in user.
- **URL**: `/api/user/me`
- **Method**: `GET`

---

### B. Update My Profile
Update your profile details and/or upload a new profile picture.
- **URL**: `/api/user/me`
- **Method**: `PUT`
- **Body**: `multipart/form-data`

**Fields (all optional):**
- `full_name`: User's complete name
- `nickname`: Preferred calling name
- `email`: Contact email
- `phone_number`: Mobile number
- `gender`: Gender (`Male`, `Female`, `Other`)
- `dob`: Date of Birth (`YYYY-MM-DD`)
- `occupation`: Current profession
- `address`: Residential address
- `avatar`: Profile image file (S3 upload)

> [!NOTE]
> The **Age** is automatically calculated based on the `dob` provided.

## 5. Program Management (Admin)

> [!IMPORTANT]
> These routes require `ADMIN` or `SUPER_ADMIN` roles.

### A. Create a Program
Define a new class location and schedule.
- **URL**: `/api/admin/programs`
- **Method**: `POST`

**Payload:**
```json
{
  "program_name": "SASM IPOH",
  "city": "Kuala Lumpur",
  "address": "1-2, Jalan Alam Sutera 10, Alam Sutera, 57000 Kuala Lumpur",
  "class_id": "C1006",
  "date_range": "20 – 26 April 2026 (Mon – Sun)",
  "is_active": true,
  "order_id": 1,
  "languages": ["English", "Tamil", "Chinese"],
  "discovery_sources": ["TikTok", "Facebook", "Introducer"],
  "price": 250.0,
  "is_refundable": true,
  "refund_percentage": 50.0,
  "allow_partial_payment": true,
  "minimum_deposit": 50.0,
  "balance_due_days": 14,
  "currency": "MYR"
}
```

**Pricing Fields:**
- `price`: Total cost of the program.
- `allow_partial_payment`: If true, users can pay just the `minimum_deposit` to register.
- `balance_due_days`: Days the user has to pay the remaining balance.

---

### B. List Registrants
Get all users who signed up for a specific program.
- **URL**: `/api/admin/programs/{program_id}`
- **Method**: `GET`

---

### C. Update a Program
Update details of an existing program.
- **URL**: `/api/admin/programs/{program_id}`
- **Method**: `PUT`

**Payload (all fields optional):**
```json
{
  "program_name": "New Name",
  "city": "New City",
  "order_id": 5
}
```

---

### D. Delete a Program
Permanently remove a program and its registrations.
- **URL**: `/api/admin/programs/{program_id}`
- **Method**: `DELETE`

---

## 6. Program Registration (User)

### A. List Available Programs
See all classes currently open for registration.
- **URL**: `/api/programs`
- **Method**: `GET`

---

### B. Register for a Program
Sign up for a specific class with your preferences.
- **URL**: `/api/programs/{program_id}/register`
- **Method**: `POST`

> [!IMPORTANT]
> **Profile Requirement**: You must have a complete profile (Full Name, Nickname, Gender, DOB, Occupation, Address, and Phone) before you can register.

**If your profile is incomplete, you will receive a 400 Error:**
```json
{
  "detail": {
    "message": "Please complete your profile details before registering for a program.",
    "profile_setup": false
  }
}
```

**Payload:**
```json
{
  "nric_last_4": "1234",
  "preferred_language": "Tamil",
  "meal_preference": "Vegetarian",
  "health_issues": "None",
  "referred_by": "John Doe (Ambassador)",
  "emergency_contact_name": "Jane Smith",
  "emergency_contact_phone": "+60123456789",
  "emergency_contact_relation": "Spouse",
  "discovery_source": "Introducer",
  "introducer_name": "Michael Tan",
  "introducer_phone": "+60128889999",
  "pay_full": false
}
```

> [!IMPORTANT]
> **Conditional Validation**: If `discovery_source` is set to `"Introducer"`, you **must** provide `introducer_name` and `introducer_phone`. Otherwise, a 400 error will be returned.

**Response (200 OK):**
```json
{
  "id": "registration-uuid",
  "payment_url": "https://securecheckout.sandbox.hit-pay.com/...",
  "payment_request_id": "a1a77a07-fd0f-4a4a-8536-55aa3be12cec",
  "payment_signature": "43cf059f17a41c894b132f041f560aaba217aeffd03b62aff2164adc5c0bde3c",
  "amount_paid": 0.0,
  "balance_amount": 250.0,
  "payment_status": "Pending",
  "due_date": "2024-05-12T00:00:00"
}
```

---

### C. My Registrations
View all programs you have signed up for.
- **URL**: `/api/programs/my-registrations`
- **Method**: `GET`
---

### D. Pay Remaining Balance
Initiate a payment for the outstanding balance of a partial registration.
- **URL**: `/api/payments/pay-balance/{registration_id}`
- **Method**: `POST`

**Response (200 OK):**
```json
{
  "payment_url": "https://securecheckout.sandbox.hit-pay.com/...",
  "payment_request_id": "a1a77a07-fd0f-4a4a-8536-55aa3be12cec",
  "payment_signature": "43cf059f17a41c894b132f041f560aaba217aeffd03b62aff2164adc5c0bde3c"
}
```

> [!IMPORTANT]
> All administrative routes require the `Authorization: Bearer <access_token>` header.

### A. List Users
Get a list of all registered users.
- **URL**: `/api/admin/users`
- **Method**: `GET`
- **Query Parameter**: `q` (optional) - Search by Name, Email, Phone, or User ID.

**Example**: `/api/admin/users?q=John`
- **Access**: `ADMIN`, `SUPER_ADMIN`

---

### B. Promote User to Admin
Grant admin privileges to a standard user.
- **URL**: `/api/admin/promote-to-admin/{user_id}`
- **Method**: `POST`
- **Access**: `SUPER_ADMIN` only

---

### C. CMS Management
Manage landing page content.
- **URL**: `/api/cms/admin/sections`
- **Method**: `GET`, `POST`, `PUT`, `DELETE`
- **Access**: `SUPER_ADMIN` only

---

## 4. Setup Checklist
1. **Environment Variables**: Ensure `SECRET_KEY`, `AWS_SES_REGION`, and `AWS_SES_SENDER_EMAIL` are set in `.env`.
2. **First Super Admin**: Manually set the `role` to `SUPER_ADMIN` for your first user in the database to unlock full administrative access.
