# Syncflow Identity & Access API Documentation

## Overview
This document provides the API specifications for Syncflow's platform foundations: Identity & Access (Milestone 1) and Workspace, Personal Space, Brand Identity & Multi-Tenant Authorization (Milestone 2).

All endpoints return JSON responses and standard HTTP status codes.

---

## Base Path
- Authentication routes: `/api/auth/`
- Workspace routes: `/api/workspaces/`
- Invitation routes: `/api/invitations/`
- Brand & Knowledge routes: `/api/social/`
- Personal Space route: `/api/me/personal-space/`

---

## Workspace & Multi-Tenant Endpoints (Milestone 2)

### 13. List & Create Workspaces
- **URL**: `/api/workspaces/`
- **Method**: `GET`, `POST`
- **Authentication Required**: Yes (`Bearer <access_token>`)
- **Authorization**: Returns only workspaces where the authenticated user has an `ACTIVE` membership. Creating a workspace automatically assigns the creator as `OWNER`.
- **POST Body**:
```json
{
  "name": "Acme Marketing Workspace",
  "description": "Workspace for Acme brand assets"
}
```

### 14. Workspace Detail, Update & Delete
- **URL**: `/api/workspaces/{id}/`
- **Method**: `GET`, `PATCH`, `DELETE`
- **Authentication Required**: Yes (`Bearer <access_token>`)
- **Authorization**: Members can `GET`. `OWNER` & `ADMIN` can `PATCH`. Only `OWNER` can `DELETE`.

### 15. Workspace Members Management
- **URL**: `/api/workspaces/{id}/members/`
- **Method**: `GET`, `POST`
- **URL (Member detail)**: `/api/workspaces/{id}/members/{member_id}/`
- **Method**: `PATCH`, `DELETE`
- **Authorization**: `OWNER` & `ADMIN` can manage members. `ADMIN` cannot grant `OWNER` role or remove `OWNER`. Sole `OWNER` cannot be removed.

### 16. Workspace Invitations
- **URL**: `/api/workspaces/{id}/invite/` (POST)
- **URL**: `/api/invitations/` (GET)
- **URL**: `/api/invitations/accept/` (POST)
- **Authorization**: Only `OWNER` and `ADMIN` can create or list workspace invitations. Single-use invitation tokens accepted securely.

### 17. Brands API
- **URL**: `/api/social/brands/`
- **Method**: `GET`, `POST`, `PATCH`, `DELETE`
- **Authorization**: Workspace member required. Brands belong to workspaces (`workspace_id`).

### 18. Brand Profile & Knowledge APIs
- **URL**: `/api/social/brands/{id}/profile/` (`GET`, `PATCH`)
- **URL**: `/api/social/brands/{id}/knowledge/` (`GET`, `POST`)
- **Authorization**: Scoped to workspace members. `OWNER`, `ADMIN`, `MANAGER` can update profile & knowledge items.

### 19. Personal Space API
- **URL**: `/api/me/personal-space/`
- **Method**: `GET`
- **Authorization**: Authenticated user context. Strictly user-isolated.


---

## Endpoints

### 1. Register User
- **URL**: `/api/auth/register/`
- **Method**: `POST`
- **Authentication Required**: No
- **Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "StrongPassword123!",
  "password_confirmation": "StrongPassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Success Response** (`201 Created`):
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
      "full_name": "John Doe",
      "avatar_url": "https://...",
      "email_confirmed": false,
      "provider": "email",
      "created_at": "2026-07-24T03:50:00Z"
    }
  },
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "message": "Registration successful. Verification code sent."
}
```
- **Error Responses**: `400 Bad Request` (duplicate email/username, password mismatch, weak password, missing fields).

---

### 2. Login
- **URL**: `/api/auth/login/`
- **Method**: `POST`
- **Authentication Required**: No
- **Request Body**:
```json
{
  "email": "john@example.com",
  "password": "StrongPassword123!",
  "device_type": "web",
  "device_token": "fcm_or_device_token_optional"
}
```
- **Success Response** (`200 OK`):
```json
{
  "user": { ... },
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>"
}
```
- **Error Responses**: `400 Bad Request` (missing fields), `401 Unauthorized` (invalid credentials or disabled account).

---

### 3. Logout
- **URL**: `/api/auth/logout/`
- **Method**: `POST`
- **Authentication Required**: Optional / Recommended
- **Request Body**:
```json
{
  "refresh": "<jwt_refresh_token>"
}
```
- **Token Behavior**: Blacklists the refresh token in SimpleJWT's token blacklist.
- **Success Response** (`200 OK`):
```json
{
  "message": "Logged out successfully."
}
```
- **Error Responses**: `400 Bad Request` (missing refresh token, invalid, expired, or blacklisted token).

---

### 4. Refresh Token
- **URL**: `/api/auth/refresh/`
- **Method**: `POST`
- **Authentication Required**: No
- **Request Body**:
```json
{
  "refresh": "<jwt_refresh_token>"
}
```
- **Success Response** (`200 OK`):
```json
{
  "access": "<new_jwt_access_token>",
  "refresh": "<new_jwt_refresh_token>"
}
```
- **Error Responses**: `401 Unauthorized` (invalid, expired, or blacklisted token).

---

### 5. Email Verification
- **URL**: `/api/auth/verify-email/`
- **Method**: `POST`
- **Authentication Required**: Optional
- **Request Body**:
```json
{
  "email": "john@example.com",
  "code": "123456"
}
```
- **Success Response** (`200 OK`):
```json
{
  "message": "Email verified successfully."
}
```
- **Error Responses**: `400 Bad Request` (invalid or expired code).

---

### 6. Resend Email Verification
- **URL**: `/api/auth/resend-verification/`
- **Method**: `POST`
- **Authentication Required**: Optional
- **Request Body**:
```json
{
  "email": "john@example.com"
}
```
- **Rate Limit**: Maximum 1 request per 60 seconds per user.
- **Success Response** (`200 OK`):
```json
{
  "message": "Verification code sent if account exists."
}
```
- **Error Responses**: `429 Too Many Requests` (throttled if re-requested under 60s).

---

### 7. Password Reset Request
- **URL**: `/api/auth/password-reset/`
- **Method**: `POST`
- **Authentication Required**: No
- **Request Body**:
```json
{
  "email": "john@example.com"
}
```
- **Security Note**: Password reset tokens are never exposed in production API response payloads.
- **Success Response** (`200 OK`):
```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

---

### 8. Password Reset Confirm
- **URL**: `/api/auth/password-reset-confirm/`
- **Method**: `POST`
- **Authentication Required**: No
- **Request Body**:
```json
{
  "token": "<reset_token_from_email>",
  "new_password": "NewStrongPassword123!",
  "new_password_confirmation": "NewStrongPassword123!"
}
```
- **Success Response** (`200 OK`):
```json
{
  "message": "Password has been reset successfully."
}
```
- **Error Responses**: `400 Bad Request` (invalid, used, or expired token, password mismatch, weak password).

---

### 9. Change Password
- **URL**: `/api/auth/change-password/`
- **Method**: `POST`
- **Authentication Required**: Yes (`Bearer <access_token>`)
- **Request Body**:
```json
{
  "old_password": "StrongPassword123!",
  "new_password": "NewStrongPassword123!",
  "new_password_confirmation": "NewStrongPassword123!"
}
```
- **Success Response** (`200 OK`):
```json
{
  "message": "Password changed successfully."
}
```
- **Error Responses**: `400 Bad Request` (incorrect old password, mismatch, weak password), `401 Unauthorized`.

---

### 10. Google Authentication
- **URL**: `/api/auth/google/`
- **Method**: `POST`
- **Authentication Required**: No
- **Architecture**: Google Identity Credential Flow
- **Request Body**:
```json
{
  "token": "<google_identity_credential_id_token>"
}
```
- **Verification Details**: Google ID token is validated server-side via Google public keys (`google.oauth2.id_token.verify_oauth2_token`). Claims validated: signature, expiration, audience, email, `email_verified == True`.
- **Success Response** (`200 OK`):
```json
{
  "user": { ... },
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "created": false
}
```
- **Error Responses**: `400 Bad Request` (missing/invalid credential, unverified email, or mock token in production mode).

---

### 11. Current User Profile
- **URL**: `/api/auth/me/`
- **Method**: `GET`, `PUT`, `PATCH`
- **Authentication Required**: Yes (`Bearer <access_token>`)
- **Success Response** (`200 OK`):
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "full_name": "John Doe",
    "avatar_url": "https://...",
    "email_confirmed": true,
    "provider": "email",
    "created_at": "2026-07-24T03:50:00Z"
  }
}
```
- **Security Guarantee**: Password hashes, tokens, and OAuth secrets are strictly excluded from all profile responses.

---

### 12. Delete Account
- **URL**: `/api/auth/delete-account/`
- **Method**: `DELETE`
- **Authentication Required**: Yes (`Bearer <access_token>`)
- **Request Body**:
```json
{
  "password": "StrongPassword123!"
}
```
*(For Google provider accounts, `confirm: true` is accepted instead of password).*
- **Success Response** (`200 OK`):
```json
{
  "message": "Account deleted successfully."
}
```
