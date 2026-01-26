# MASH Backend - Complete API Documentation

> **Mushroom Automation Smart Harvesting (MASH) Backend API**  
> Version: 1.0.0

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [User Management](#user-management)
3. [Products](#products)
4. [Categories](#categories)
5. [Cart](#cart)
6. [Orders](#orders)
7. [IoT Devices](#iot-devices)
8. [Sensors](#sensors)
9. [Notifications](#notifications)
10. [Lalamove Delivery](#lalamove-delivery)
11. [Admin & Super Admin](#admin--super-admin)
12. [Health & Monitoring](#health--monitoring)
13. [Rate Limiting](#rate-limiting)
14. [Import/Export](#importexport)

---

## Authentication & Authorization

### Register New User
- **POST** `/auth/register`
- **Description:** Create new user account with email verification
- **Rate Limit:** 3 requests/minute
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecureP@ssw0rd!",
    "firstName": "John",
    "lastName": "Doe",
    "username": "johndoe" // optional
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "success": true,
    "message": "Registration successful. Please check your email to verify your account.",
    "data": {
      "userId": "clxxx123456789",
      "email": "user@example.com",
      "emailVerificationSent": true
    }
  }
  ```

### Check Username Availability
- **GET** `/auth/check-username?username=johndoe`
- **Description:** Check if username is available
- **Rate Limit:** 20 requests/minute
- **Auth:** None (Public)
- **Response:** `200 OK`
  ```json
  {
    "available": true,
    "username": "johndoe"
  }
  ```

### Verify Email
- **POST** `/auth/verify-email`
- **Description:** Verify email with token sent via email
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "token": "64-character-verification-token"
  }
  ```

### Login
- **POST** `/auth/login`
- **Description:** Authenticate user and receive JWT tokens
- **Rate Limit:** 5 requests/minute
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecureP@ssw0rd!"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "success": true,
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "refresh_token_here",
    "user": {
      "id": "clxxx123456789",
      "email": "user@example.com",
      "role": "USER"
    }
  }
  ```

### Refresh Token
- **POST** `/auth/refresh`
- **Description:** Get new access token using refresh token
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "refreshToken": "refresh_token_here"
  }
  ```

### Logout
- **POST** `/auth/logout`
- **Description:** Invalidate current session
- **Auth:** Bearer JWT

### Forgot Password
- **POST** `/auth/forgot-password`
- **Description:** Request password reset code via email
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "email": "user@example.com"
  }
  ```

### Reset Password
- **POST** `/auth/reset-password`
- **Description:** Reset password with verification code
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "email": "user@example.com",
    "code": "6-digit-code",
    "newPassword": "NewSecureP@ssw0rd!"
  }
  ```

### Google OAuth Login
- **POST** `/auth/google/login`
- **Description:** Authenticate with Google OAuth
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "idToken": "google_id_token_here"
  }
  ```

### Facebook OAuth Login
- **POST** `/auth/facebook/login`
- **Description:** Authenticate with Facebook OAuth
- **Auth:** None (Public)

---

## User Management

### Get Current User Profile
- **GET** `/users/me`
- **Description:** Get authenticated user's profile
- **Auth:** Bearer JWT
- **Response:** `200 OK`
  ```json
  {
    "id": "clxxx123456789",
    "email": "user@example.com",
    "username": "johndoe",
    "firstName": "John",
    "lastName": "Doe",
    "role": "USER",
    "isActive": true,
    "createdAt": "2026-01-01T00:00:00Z"
  }
  ```

### List All Users (Admin)
- **GET** `/users`
- **Description:** Get paginated list of users with filters
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `page` (number, default: 1)
  - `limit` (number, default: 10)
  - `role` (enum: USER, ADMIN, GROWER, BUYER, SUPER_ADMIN)
  - `isActive` (boolean)
  - `search` (string) - Search by email, username, or name

### Create User (Admin)
- **POST** `/users`
- **Description:** Create new user account
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "email": "newuser@example.com",
    "password": "SecureP@ssw0rd!",
    "firstName": "Jane",
    "lastName": "Smith",
    "role": "USER"
  }
  ```

### Update User
- **PUT** `/users/:id`
- **Description:** Update user information
- **Auth:** Bearer JWT
- **Path Parameters:** `id` (user ID)

### Delete User (Admin)
- **DELETE** `/users/:id`
- **Description:** Soft delete user account
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Upload Avatar
- **POST** `/users/avatar`
- **Description:** Upload user profile picture
- **Auth:** Bearer JWT
- **Content-Type:** `multipart/form-data`
- **Body:** Form data with `file` field

### Update User Preferences
- **PUT** `/users/preferences`
- **Description:** Update notification and display preferences
- **Auth:** Bearer JWT

---

## Profile Management

### Get Profile
- **GET** `/profile`
- **Description:** Get current user's detailed profile
- **Auth:** Bearer JWT

### Update Profile
- **PATCH** `/profile`
- **Description:** Update current user's profile information
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "firstName": "John",
    "lastName": "Doe",
    "phoneNumber": "+639123456789",
    "username": "johndoe"
  }
  ```

### Get User Preferences
- **GET** `/profile/preferences`
- **Description:** Get user notification and display preferences
- **Auth:** Bearer JWT

### Update User Preferences  
- **PATCH** `/profile/preferences`
- **Description:** Update notification and display preferences
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "notifications": {
      "email": true,
      "push": true,
      "sms": false
    },
    "theme": "dark",
    "language": "en"
  }
  ```

### Upload Avatar
- **POST** `/profile/avatar`
- **Description:** Upload profile picture (max 5MB, formats: JPEG, PNG, GIF, WebP, BMP, ICO)
- **Auth:** Bearer JWT
- **Rate Limit:** 10 uploads/hour
- **Content-Type:** `multipart/form-data`
- **Body:** Form data with `avatar` field

### Delete Avatar
- **DELETE** `/profile/avatar`
- **Description:** Delete user's profile picture
- **Auth:** Bearer JWT

### Get Active Sessions
- **GET** `/profile/sessions`
- **Description:** Get all active login sessions for current user
- **Auth:** Bearer JWT

### Get Current Session
- **GET** `/profile/sessions/current`
- **Description:** Get details of current active session
- **Auth:** Bearer JWT

### Revoke Session
- **DELETE** `/profile/sessions/:sessionId`
- **Description:** Revoke a specific session
- **Auth:** Bearer JWT

### Revoke All Other Sessions
- **DELETE** `/profile/sessions`
- **Description:** Revoke all sessions except current
- **Auth:** Bearer JWT

### Get API Keys
- **GET** `/profile/api-keys`
- **Description:** Get all API keys for current user
- **Auth:** Bearer JWT

### Create API Key
- **POST** `/profile/api-keys`
- **Description:** Generate new API key for programmatic access
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "name": "Production API Key",
    "scopes": ["products:read", "orders:write"],
    "expiresAt": "2027-01-01T00:00:00Z"
  }
  ```

### Revoke API Key
- **DELETE** `/profile/api-keys/:keyId`
- **Description:** Revoke an API key
- **Auth:** Bearer JWT

### Get Security Logs
- **GET** `/profile/security-logs`
- **Description:** Get security event logs (login attempts, password changes, etc.)
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `severity` (string: INFO, WARNING, CRITICAL)
  - `startDate`, `endDate` (date range)

### Enable Two-Factor Authentication
- **POST** `/profile/2fa/enable`
- **Description:** Enable TOTP-based two-factor authentication
- **Auth:** Bearer JWT

### Verify 2FA Setup
- **POST** `/profile/2fa/verify`
- **Description:** Verify and activate 2FA with TOTP code
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "code": "123456"
  }
  ```

### Disable Two-Factor Authentication
- **POST** `/profile/2fa/disable`
- **Description:** Disable two-factor authentication
- **Auth:** Bearer JWT

### Regenerate 2FA Backup Codes
- **POST** `/profile/2fa/backup-codes`
- **Description:** Generate new backup codes for 2FA
- **Auth:** Bearer JWT

---

## Products

### List All Products
- **GET** `/products`
- **Description:** Get paginated product list with filters
- **Auth:** None (Public)
- **Query Parameters:**
  - `page` (number, default: 1)
  - `limit` (number, default: 10)
  - `search` (string) - Search by name or description
  - `categoryId` (string) - Filter by category
  - `minPrice` (number)
  - `maxPrice` (number)
  - `isActive` (boolean, default: true)
  - `isFeatured` (boolean)
  - `sortBy` (string: price, name, createdAt)
  - `order` (string: asc, desc)
- **Response:** `200 OK`
  ```json
  {
    "data": [
      {
        "id": "clprod123",
        "name": "Organic Oyster Mushrooms",
        "slug": "organic-oyster-mushrooms",
        "price": 29.99,
        "stock": 100,
        "images": ["https://cdn.example.com/mushroom.jpg"],
        "isActive": true,
        "isFeatured": true
      }
    ],
    "meta": {
      "total": 50,
      "page": 1,
      "limit": 10,
      "totalPages": 5
    }
  }
  ```

### Get Product by ID
- **GET** `/products/:id`
- **Description:** Get detailed product information
- **Auth:** None (Public)
- **Path Parameters:** `id` (product ID)

### Get Product by Slug
- **GET** `/products/slug/:slug`
- **Description:** Get product by URL-friendly slug
- **Auth:** None (Public)

### Create Product (Admin)
- **POST** `/products`
- **Description:** Create new product
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "name": "Fresh Shiitake Mushrooms",
    "slug": "fresh-shiitake-mushrooms",
    "description": "Premium quality shiitake mushrooms",
    "price": 39.99,
    "comparePrice": 49.99,
    "stock": 50,
    "minStock": 10,
    "sku": "SHII-001",
    "images": ["image-url-1", "image-url-2"],
    "categories": ["mushrooms", "organic"],
    "tags": ["fresh", "organic"],
    "isActive": true,
    "isFeatured": false
  }
  ```

### Update Product (Admin)
- **PUT** `/products/:id`
- **Description:** Update product information
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Delete Product (Admin)
- **DELETE** `/products/:id`
- **Description:** Soft delete product
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Featured Products
- **GET** `/products/featured`
- **Description:** Get list of featured products
- **Auth:** None (Public)

### Get Products by Category
- **GET** `/products/category/:categoryId`
- **Description:** Get all products in specific category
- **Auth:** None (Public)

### Search Products
- **GET** `/products/search/:term`
- **Description:** Full-text search for products
- **Auth:** None (Public)

### Update Product Stock (Admin)
- **PUT** `/products/:id/stock`
- **Description:** Update product inventory
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "stock": 75,
    "minStock": 10
  }
  ```

### Update Product Price (Admin)
- **PUT** `/products/:id/price`
- **Description:** Update product pricing
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "price": 34.99,
    "comparePrice": 44.99
  }
  ```

### Toggle Product Active Status (Admin)
- **POST** `/products/:id/activate`
- **Description:** Activate or deactivate product
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Related Products
- **GET** `/products/:id/related`
- **Description:** Get products in same category
- **Auth:** None (Public)

### Get Low Stock Products (Admin)
- **GET** `/products/inventory/low-stock`
- **Description:** Get products below minimum stock level
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Product Reviews
- **GET** `/products/:id/reviews`
- **Description:** Get product reviews and ratings
- **Auth:** None (Public)

### Get Best Sellers (Admin)
- **GET** `/products/analytics/best-sellers`
- **Description:** Get analytics for top-selling products
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

---

## Categories

### List All Categories
- **GET** `/categories`
- **Description:** Get all product categories
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `parentId` (filter by parent category)
  - `isActive` (boolean)

### Get Category Tree
- **GET** `/categories/tree`
- **Description:** Get hierarchical category structure
- **Auth:** Bearer JWT

### Get Category by ID
- **GET** `/categories/:id`
- **Description:** Get category details
- **Auth:** Bearer JWT

### Create Category (Admin)
- **POST** `/categories`
- **Description:** Create new category
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "name": "Edible Mushrooms",
    "slug": "edible-mushrooms",
    "description": "All edible mushroom varieties",
    "parentId": null,
    "imageUrl": "category-image-url",
    "isActive": true,
    "sortOrder": 1
  }
  ```

### Update Category (Admin)
- **PUT** `/categories/:id`
- **Description:** Update category information
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Delete Category (Admin)
- **DELETE** `/categories/:id`
- **Description:** Soft delete category
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Child Categories
- **GET** `/categories/:id/children`
- **Description:** Get sub-categories of a category
- **Auth:** Bearer JWT

### Get Category Products
- **GET** `/categories/:id/products`
- **Description:** Get all products in category
- **Auth:** Bearer JWT

---

## Cart

### Get Current Cart
- **GET** `/api/v1/cart`
- **Description:** Get active cart for user or guest session
- **Auth:** None (Public) - Supports both authenticated and guest users
- **Headers:** `X-Session-Id` (for guest carts)
- **Cookies:** `cart_session_id` (for guest carts)
- **Response:** `200 OK`
  ```json
  {
    "id": "clcart123",
    "userId": "cluser123",
    "status": "ACTIVE",
    "subtotal": 59.98,
    "tax": 7.20,
    "shipping": 150.00,
    "discount": 0,
    "total": 217.18,
    "currency": "PHP",
    "itemCount": 2,
    "items": [
      {
        "id": "clitem123",
        "productId": "clprod123",
        "quantity": 2,
        "price": 29.99,
        "subtotal": 59.98,
        "product": {
          "name": "Organic Oyster Mushrooms",
          "images": ["image-url"],
          "stock": 98
        }
      }
    ],
    "lastActivityAt": "2026-01-26T10:00:00Z"
  }
  ```

### Get Cart Summary
- **GET** `/api/v1/cart/summary`
- **Description:** Get lightweight cart summary
- **Auth:** None (Public)

### Add Item to Cart
- **POST** `/api/v1/cart/items`
- **Description:** Add product to cart
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "productId": "clprod123",
    "quantity": 2
  }
  ```
- **Response:** `201 Created`

### Update Cart Item
- **PUT** `/api/v1/cart/items/:itemId`
- **Description:** Update item quantity
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "quantity": 3
  }
  ```

### Remove Cart Item
- **DELETE** `/api/v1/cart/items/:itemId`
- **Description:** Remove item from cart
- **Auth:** None (Public)

### Clear Cart
- **DELETE** `/api/v1/cart`
- **Description:** Remove all items from cart
- **Auth:** None (Public)

### Estimate Shipping
- **POST** `/api/v1/cart/estimate-shipping`
- **Description:** Calculate shipping cost
- **Auth:** None (Public)
- **Body Parameters:**
  ```json
  {
    "shippingAddress": {
      "city": "Manila",
      "state": "Metro Manila",
      "postalCode": "1000",
      "country": "Philippines"
    }
  }
  ```

### Create Order from Cart
- **POST** `/api/v1/cart/checkout`
- **Description:** Convert cart to order
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "shippingAddress": {
      "firstName": "John",
      "lastName": "Doe",
      "street1": "123 Main St",
      "city": "Manila",
      "state": "Metro Manila",
      "postalCode": "1000",
      "country": "Philippines",
      "phoneNumber": "+639171234567"
    },
    "paymentMethod": "GCASH"
  }
  ```

---

## Orders

### List All Orders (Admin)
- **GET** `/orders`
- **Description:** Get paginated order list
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit`
  - `status` (PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED)
  - `userId`
  - `startDate`, `endDate`

### Create Order
- **POST** `/orders`
- **Description:** Place new order
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "items": [
      {
        "productId": "clprod123",
        "quantity": 2,
        "price": 29.99
      }
    ],
    "shippingAddress": { /* address object */ },
    "billingAddress": { /* address object */ },
    "paymentMethod": "GCASH",
    "notes": "Please deliver in the morning"
  }
  ```

### Get User's Orders
- **GET** `/orders/user/:userId`
- **Description:** Get order history for specific user
- **Auth:** Bearer JWT

### Get Order by ID
- **GET** `/orders/:id`
- **Description:** Get detailed order information
- **Auth:** Bearer JWT

### Update Order (Admin)
- **PUT** `/orders/:id`
- **Description:** Update order details
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Update Order Status (Admin/Grower)
- **PUT** `/orders/:id/status`
- **Description:** Change order status
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN, GROWER)
- **Body Parameters:**
  ```json
  {
    "status": "SHIPPED",
    "trackingNumber": "TRACK123456"
  }
  ```

### Cancel Order
- **POST** `/orders/:id/cancel`
- **Description:** Cancel order
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "reason": "Changed my mind"
  }
  ```

### Delete Order (Admin)
- **DELETE** `/orders/:id`
- **Description:** Delete order
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

---

## IoT Devices

### List All Devices
- **GET** `/devices`
- **Description:** Get paginated device list
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `page`, `limit`
  - `type` (MUSHROOM_CHAMBER, ENVIRONMENTAL_SENSOR, IRRIGATION_SYSTEM, etc.)
  - `status` (ONLINE, OFFLINE, MAINTENANCE, ERROR)
  - `userId`
  - `isActive` (boolean)

### Register Device
- **POST** `/devices`
- **Description:** Register new IoT device
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN, GROWER)
- **Body Parameters:**
  ```json
  {
    "name": "Chamber A - Sensor 1",
    "type": "ENVIRONMENTAL_SENSOR",
    "serialNumber": "SN-123456789",
    "location": "Greenhouse A",
    "description": "Temperature and humidity sensor",
    "firmware": "v1.2.3",
    "configuration": {
      "sampleInterval": 300,
      "alertThresholds": {
        "temperature": { "min": 18, "max": 25 },
        "humidity": { "min": 65, "max": 85 }
      }
    }
  }
  ```

### Get Device by ID
- **GET** `/devices/:id`
- **Description:** Get device details
- **Auth:** Bearer JWT

### Update Device
- **PUT** `/devices/:id`
- **Description:** Update device information
- **Auth:** Bearer JWT

### Delete Device (Admin)
- **DELETE** `/devices/:id`
- **Description:** Soft delete device
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Toggle Device Activation
- **POST** `/devices/:id/activate`
- **Description:** Activate or deactivate device
- **Auth:** Bearer JWT

### Check Device Status
- **POST** `/devices/status/check`
- **Description:** Trigger on-demand device status check
- **Auth:** Bearer JWT
- **Description:** Checks all devices and marks inactive ones as offline

### Send Command to Device
- **POST** `/devices/:id/command`
- **Description:** Send MQTT command to device
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "command": "RESTART",
    "parameters": {
      "force": true
    }
  }
  ```

### Get Device Command History
- **GET** `/devices/:id/commands`
- **Description:** Get command history for device
- **Auth:** Bearer JWT

### Get Device Health Status
- **GET** `/devices/:id/health`
- **Description:** Get device health metrics
- **Auth:** Bearer JWT

### Update Device Firmware
- **POST** `/devices/:id/firmware`
- **Description:** Trigger firmware update
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

---

## Sensors

### List All Sensors
- **GET** `/sensors`
- **Description:** Get paginated sensor list
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `page`, `limit`
  - `deviceId`
  - `type` (temperature, humidity, pH, etc.)
  - `isActive` (boolean)

### Create Sensor
- **POST** `/sensors`
- **Description:** Register new sensor
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN, GROWER)
- **Body Parameters:**
  ```json
  {
    "deviceId": "cldev123",
    "type": "temperature",
    "name": "Temperature Sensor 1",
    "unit": "°C",
    "minValue": 0,
    "maxValue": 50,
    "calibration": {
      "offset": 0,
      "scale": 1
    }
  }
  ```

### Get Sensor by ID
- **GET** `/sensors/:id`
- **Description:** Get sensor details
- **Auth:** Bearer JWT

### Update Sensor
- **PUT** `/sensors/:id`
- **Description:** Update sensor configuration
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN, GROWER)

### Delete Sensor
- **DELETE** `/sensors/:id`
- **Description:** Soft delete sensor
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN, GROWER)

### Ingest Sensor Data
- **POST** `/sensors/:id/data`
- **Description:** Record single sensor reading
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "value": 24.5,
    "quality": "good",
    "timestamp": "2026-01-26T10:00:00Z"
  }
  ```

### Batch Ingest Sensor Data
- **POST** `/sensors/:id/data/batch`
- **Description:** Record multiple sensor readings
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "readings": [
      { "value": 24.5, "timestamp": "2026-01-26T10:00:00Z" },
      { "value": 24.7, "timestamp": "2026-01-26T10:05:00Z" }
    ]
  }
  ```

### Get Sensor Data
- **GET** `/sensors/:id/data`
- **Description:** Query sensor readings with date range
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `startDate`, `endDate`
  - `interval` (raw, hourly, daily)
  - `page`, `limit`

### Get Sensor Analytics
- **GET** `/sensors/:id/analytics`
- **Description:** Get aggregated sensor statistics
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `startDate`, `endDate`
  - `aggregation` (avg, min, max, sum)

---

## Notifications

### List Notifications
- **GET** `/notifications`
- **Description:** Get user's notifications
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `page`, `limit`
  - `type` (ALERT, INFO, WARNING, SUCCESS, etc.)
  - `isRead` (boolean)

### Create Notification (Admin)
- **POST** `/notifications`
- **Description:** Create new notification
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Unread Count
- **GET** `/notifications/unread-count`
- **Description:** Get count of unread notifications
- **Auth:** Bearer JWT

### Get Notification Preferences
- **GET** `/notifications/preferences`
- **Description:** Get user's notification settings
- **Auth:** Bearer JWT

### Update Notification Preferences
- **PUT** `/notifications/preferences`
- **Description:** Update notification settings
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "emailNotifications": true,
    "pushNotifications": true,
    "smsNotifications": false,
    "alertTypes": ["ORDER_UPDATE", "DEVICE_STATUS"]
  }
  ```

### Get Notification by ID
- **GET** `/notifications/:id`
- **Description:** Get notification details
- **Auth:** Bearer JWT

### Mark as Read
- **PUT** `/notifications/:id/read`
- **Description:** Mark notification as read
- **Auth:** Bearer JWT

### Delete Notification
- **DELETE** `/notifications/:id`
- **Description:** Delete notification
- **Auth:** Bearer JWT

---

## Search & Elasticsearch

### Health Check
- **GET** `/search/health`
- **Description:** Test Elasticsearch connection
- **Auth:** None (Public)
- **Response:** `200 OK`

### Advanced Product Search
- **GET** `/search/products`
- **Description:** Full-text search with filters, sorting, and facets
- **Auth:** None (Public)
- **Query Parameters:**
  - `query` (string) - Search query
  - `page` (number, default: 1)
  - `limit` (number, max: 100)
  - `minPrice`, `maxPrice` (number) - Price range
  - `categories` (string[]) - Category filters
  - `minRating` (number) - Minimum rating filter
  - `inStock` (boolean) - Only in-stock products
  - `tags` (string[]) - Tag filters
  - `sortBy` (string: relevance, price, rating, createdAt, name)
  - `sortOrder` (string: asc, desc)
  - `includeFacets` (boolean) - Include facets in response
- **Response:** `200 OK`
  ```json
  {
    "hits": [
      {
        "id": "prod123",
        "name": "Fresh Oyster Mushrooms",
        "price": 150,
        "_score": 9.5
      }
    ],
    "total": 42,
    "took": 28,
    "facets": {
      "categories": {"Mushrooms": 35, "Dried": 7},
      "priceRanges": {"0-100": 10, "100-200": 20}
    }
  }
  ```

### Autocomplete
- **GET** `/search/autocomplete`
- **Description:** Fast prefix-based product name suggestions (target <100ms)
- **Auth:** None (Public)
- **Query Parameters:**
  - `q` (string, min 2 chars) - Query string
  - `limit` (number, default: 10) - Max suggestions
- **Response:** `200 OK`
  ```json
  {
    "query": "oys",
    "suggestions": ["Oyster Mushrooms", "Oyster Sauce"],
    "took": 45
  }
  ```

### Find Similar Products
- **GET** `/search/products/:id/similar`
- **Description:** Get products similar to specified product using More Like This
- **Auth:** None (Public)
- **Path Parameters:** `id` (product ID)
- **Query Parameters:**
  - `limit` (number, default: 5) - Max results

### Reindex All Products (Admin)
- **POST** `/search/reindex/products`
- **Description:** Trigger full reindex of all products from database to Elasticsearch
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Response:** `200 OK`
  ```json
  {
    "message": "Product reindexing completed successfully",
    "timestamp": "2026-01-26T10:00:00Z"
  }
  ```

---

## Inventory Management

### Create Inventory Item
- **POST** `/inventory`
- **Description:** Create new inventory record
- **Auth:** Bearer JWT (ADMIN, GROWER)
- **Body Parameters:**
  ```json
  {
    "productId": "prod123",
    "quantity": 100,
    "location": "Warehouse A",
    "notes": "Fresh stock"
  }
  ```

### List All Inventory
- **GET** `/inventory`
- **Description:** Get all inventory items
- **Auth:** Bearer JWT

### Search Inventory
- **GET** `/inventory/search`
- **Description:** Search inventory by product name or SKU
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `q` (string) - Search query

### Get Inventory Item
- **GET** `/inventory/:id`
- **Description:** Get specific inventory item details
- **Auth:** Bearer JWT
- **Path Parameters:** `id` (inventory item ID)

### Update Inventory Item
- **PATCH** `/inventory/:id`
- **Description:** Update inventory information
- **Auth:** Bearer JWT (ADMIN, GROWER)

### Restore Inventory Item
- **PATCH** `/inventory/:id/restore`
- **Description:** Restore soft-deleted inventory item
- **Auth:** Bearer JWT (ADMIN)

### Delete Inventory Item
- **DELETE** `/inventory/:id`
- **Description:** Soft delete inventory item
- **Auth:** Bearer JWT (ADMIN)

---

## Alerts Management

### Trigger Alert Evaluation
- **POST** `/alerts/trigger`
- **Description:** Manually trigger an alert evaluation
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "eventType": "sensor.temperature.high",
    "data": {
      "deviceId": "device123",
      "value": 35.5,
      "threshold": 30
    }
  }
  ```

### Get Alert History
- **GET** `/alerts/history`
- **Description:** Get paginated alert history
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `category` (AlertCategory)
  - `priority` (AlertPriority)
  - `status` (AlertStatus)
  - `startDate`, `endDate` (date range)

### Get Active Alerts
- **GET** `/alerts/active`
- **Description:** Get currently active alerts
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Acknowledge Alert
- **POST** `/alerts/:id/acknowledge`
- **Description:** Acknowledge an alert
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Path Parameters:** `id` (alert ID)

### Resolve Alert
- **POST** `/alerts/:id/resolve`
- **Description:** Mark alert as resolved
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Alert Statistics
- **GET** `/alerts/statistics`
- **Description:** Get alert statistics and trends
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `days` (number, default: 7) - Number of days for statistics

---

## Super Admin

### Get Dashboard Overview
- **GET** `/super-admin/dashboard/overview`
- **Description:** Get comprehensive dashboard overview
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Response:** `200 OK`
  ```json
  {
    "users": {"total": 1500, "active": 1200},
    "orders": {"total": 5000, "pending": 45},
    "revenue": {"today": 15000, "month": 450000},
    "devices": {"online": 32, "offline": 8}
  }
  ```

### Get Daily Sales
- **GET** `/super-admin/dashboard/sales`
- **Description:** Get daily sales data for last N days
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `days` (number, default: 7) - Number of days

### Get Chamber Registry
- **GET** `/super-admin/dashboard/chambers`
- **Description:** Get mushroom chamber device registry
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit` (pagination)

### Get User Statistics
- **GET** `/super-admin/dashboard/users-stats`
- **Description:** Get user counts by role
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Cards Summary
- **GET** `/super-admin/dashboard/cards`
- **Description:** Get dashboard card statistics
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Pending Seller Applications
- **GET** `/super-admin/seller-applications/pending`
- **Description:** Get all pending seller role applications
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `page` (number, default: 1)
  - `limit` (number, default: 20)

### Get All Seller Applications
- **GET** `/super-admin/seller-applications/all`
- **Description:** Get all seller applications with filters
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `status` (string: pending, approved, rejected)
  - `userId` (string) - Filter by user

### Get Application Statistics
- **GET** `/super-admin/seller-applications/stats`
- **Description:** Get seller application statistics
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Application Details
- **GET** `/super-admin/seller-applications/:requestId`
- **Description:** Get detailed information about specific application
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Approve Seller Application
- **PUT** `/super-admin/seller-applications/:requestId/approve`
- **Description:** Approve seller role request
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Reject Seller Application
- **PUT** `/super-admin/seller-applications/:requestId/reject`
- **Description:** Reject seller role request
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "reason": "Incomplete documentation"
  }
  ```

### Bulk Process Applications
- **POST** `/super-admin/seller-applications/bulk`
- **Description:** Approve or reject multiple applications at once
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "requestIds": ["req1", "req2"],
    "action": "approve"
  }
  ```

---

## Lalamove Delivery

### Get City Information
- **GET** `/api/v1/lalamove/city-info`
- **Description:** Get available cities, service types, and special requests for Philippines market
- **Auth:** Bearer JWT

### Create Quotation
- **POST** `/api/v1/lalamove/quotations`
- **Description:** Create delivery quotation (expires in 5 minutes)
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "serviceType": "MOTORCYCLE",
    "stops": [
      {
        "location": {"lat": "14.5995", "lng": "120.9842"},
        "address": "Pickup Address, Manila",
        "stopType": "PICK_UP",
        "contactName": "John Doe",
        "contactPhone": "+639123456789"
      },
      {
        "location": {"lat": "14.6091", "lng": "121.0223"},
        "address": "Delivery Address, Quezon City",
        "stopType": "DROP_OFF",
        "contactName": "Jane Smith",
        "contactPhone": "+639987654321"
      }
    ],
    "isScheduled": false,
    "specialRequests": ["COD"]
  }
  ```

### Get Quotation Details
- **GET** `/api/v1/lalamove/quotations/:quotationId`
- **Description:** Get detailed quotation information
- **Auth:** Bearer JWT

### Create Delivery Order
- **POST** `/api/v1/lalamove/orders`
- **Description:** Create delivery order from valid quotation
- **Auth:** Bearer JWT
- **Body Parameters:**
  ```json
  {
    "quotationId": "PHLM123456",
    "sender": {
      "name": "MASH Store",
      "phone": "+639123456789"
    },
    "isPODEnabled": true
  }
  ```

### Get Order Details
- **GET** `/api/v1/lalamove/orders/:orderId`
- **Description:** Get detailed order information and tracking
- **Auth:** Bearer JWT

### Cancel Order
- **DELETE** `/api/v1/lalamove/orders/:orderId`
- **Description:** Cancel delivery order (only before driver pickup)
- **Auth:** Bearer JWT

### Add Driver Tip
- **POST** `/api/v1/lalamove/orders/:orderId/tip`
- **Description:** Add tip for driver
- **Auth:** Bearer JWT

### Get Available Drivers
- **GET** `/api/v1/lalamove/drivers`
- **Description:** Get list of available drivers near pickup location
- **Auth:** Bearer JWT

---

## Search & Elasticsearch

### Health Check
- **GET** `/search/health`
- **Description:** Test Elasticsearch connection
- **Auth:** None (Public)

### Advanced Product Search
- **GET** `/search/products`
- **Description:** Full-text search with filters, sorting, and facets
- **Auth:** None (Public)
- **Query Parameters:**
  - `query` (string) - Search query
  - `page`, `limit` (pagination, max 100 per page)
  - `minPrice`, `maxPrice` (number) - Price range
  - `categories` (string[]) - Category filters
  - `minRating` (number) - Minimum rating filter
  - `inStock` (boolean) - Only in-stock products
  - `tags` (string[]) - Tag filters
  - `sortBy` (enum: relevance, price, rating, createdAt, name)
  - `sortOrder` (enum: asc, desc)
  - `includeFacets` (boolean) - Include facets

### Autocomplete
- **GET** `/search/autocomplete`
- **Description:** Fast prefix-based product name suggestions (target <100ms)
- **Auth:** None (Public)
- **Query Parameters:**
  - `q` (string, min 2 chars) - Query string
  - `limit` (number, default: 10) - Max suggestions

### Find Similar Products
- **GET** `/search/products/:id/similar`
- **Description:** Get products similar to specified product
- **Auth:** None (Public)
- **Query Parameters:**
  - `limit` (number, default: 5) - Max results

### Reindex All Products (Admin)
- **POST** `/search/reindex/products`
- **Description:** Trigger full reindex from database to Elasticsearch
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

---

## Inventory Management

### Create Inventory Item
- **POST** `/inventory`
- **Description:** Create new inventory record
- **Auth:** Bearer JWT (ADMIN, GROWER)

### List All Inventory
- **GET** `/inventory`
- **Description:** Get all inventory items
- **Auth:** Bearer JWT

### Search Inventory
- **GET** `/inventory/search`
- **Description:** Search inventory by product name or SKU
- **Auth:** Bearer JWT
- **Query Parameters:**
  - `q` (string) - Search query

### Get Inventory Item
- **GET** `/inventory/:id`
- **Description:** Get specific inventory item details
- **Auth:** Bearer JWT

### Update Inventory Item
- **PATCH** `/inventory/:id`
- **Description:** Update inventory information
- **Auth:** Bearer JWT (ADMIN, GROWER)

### Restore Inventory Item
- **PATCH** `/inventory/:id/restore`
- **Description:** Restore soft-deleted inventory item
- **Auth:** Bearer JWT (ADMIN)

### Delete Inventory Item
- **DELETE** `/inventory/:id`
- **Description:** Soft delete inventory item
- **Auth:** Bearer JWT (ADMIN)

---

## Alerts Management

### Trigger Alert Evaluation
- **POST** `/alerts/trigger`
- **Description:** Manually trigger an alert evaluation
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "eventType": "sensor.temperature.high",
    "data": {
      "deviceId": "device123",
      "value": 35.5,
      "threshold": 30
    }
  }
  ```

### Get Alert History
- **GET** `/alerts/history`
- **Description:** Get paginated alert history
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `category`, `priority`, `status` (filters)
  - `startDate`, `endDate` (date range)

### Get Active Alerts
- **GET** `/alerts/active`
- **Description:** Get currently active alerts
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Acknowledge Alert
- **POST** `/alerts/:id/acknowledge`
- **Description:** Acknowledge an alert
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Resolve Alert
- **POST** `/alerts/:id/resolve`
- **Description:** Mark alert as resolved
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Get Alert Statistics
- **GET** `/alerts/statistics`
- **Description:** Get alert statistics and trends
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `days` (number, default: 7) - Number of days for statistics

---

## Super Admin

### Get Dashboard Overview
- **GET** `/super-admin/dashboard/overview`
- **Description:** Get comprehensive dashboard overview
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Daily Sales
- **GET** `/super-admin/dashboard/sales`
- **Description:** Get daily sales data for last N days
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `days` (number, default: 7) - Number of days

### Get Chamber Registry
- **GET** `/super-admin/dashboard/chambers`
- **Description:** Get mushroom chamber device registry
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get User Statistics
- **GET** `/super-admin/dashboard/users-stats`
- **Description:** Get user counts by role
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Cards Summary
- **GET** `/super-admin/dashboard/cards`
- **Description:** Get dashboard card statistics
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Pending Seller Applications
- **GET** `/super-admin/seller-applications/pending`
- **Description:** Get all pending seller role applications
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get All Seller Applications
- **GET** `/super-admin/seller-applications/all`
- **Description:** Get all seller applications with filters
- **Auth:** Bearer JWT (SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit` (pagination)
  - `status` (enum: pending, approved, rejected)
  - `userId` (string) - Filter by user

### Get Application Statistics
- **GET** `/super-admin/seller-applications/stats`
- **Description:** Get seller application statistics
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Get Application Details
- **GET** `/super-admin/seller-applications/:requestId`
- **Description:** Get detailed information about specific application
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Approve Seller Application
- **PUT** `/super-admin/seller-applications/:requestId/approve`
- **Description:** Approve seller role request
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Reject Seller Application
- **PUT** `/super-admin/seller-applications/:requestId/reject`
- **Description:** Reject seller role request
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Bulk Process Applications
- **POST** `/super-admin/seller-applications/bulk`
- **Description:** Approve or reject multiple applications at once
- **Auth:** Bearer JWT (SUPER_ADMIN)

---

## Admin & Super Admin

### Get System Statistics
- **GET** `/super-admin/statistics`
- **Description:** Get system-wide statistics
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Manage Users
- **GET/POST/PUT/DELETE** `/super-admin/users/*`
- **Description:** Full user management
- **Auth:** Bearer JWT (SUPER_ADMIN)

### Seed Database
- **POST** `/super-admin/seed`
- **Description:** Populate database with sample data
- **Auth:** Bearer JWT (SUPER_ADMIN)

---

## Health & Monitoring

### Health Check
- **GET** `/health`
- **Description:** System health status
- **Auth:** None (Public)
- **Response:** `200 OK`
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-01-26T10:00:00Z",
    "uptime": 86400,
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "mqtt": "healthy"
    }
  }
  ```

### Prometheus Metrics
- **GET** `/metrics`
- **Description:** Prometheus-format metrics
- **Auth:** None (Public)

### Metrics JSON
- **GET** `/metrics/json`
- **Description:** JSON-format metrics
- **Auth:** None (Public)

---

## Rate Limiting

### Get Rate Limit Status
- **GET** `/rate-limit/status`
- **Description:** Check rate limit status for user
- **Auth:** Bearer JWT

---

## Import/Export

### Upload Import File
- **POST** `/import/upload`
- **Description:** Upload file for data import (CSV, Excel, JSON, XML)
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  ```json
  {
    "file": "binary",
    "entityType": "PRODUCT | ORDER | USER | CATEGORY | SELLER | BUYER | TRANSACTION | INVENTORY",
    "priority": "URGENT | NORMAL | LOW",
    "skipInvalid": true,
    "batchSize": 1000
  }
  ```

### Get Import Job Details
- **GET** `/import/jobs/:jobId`
- **Description:** Get detailed import job status, progress, and errors
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### List Import Jobs
- **GET** `/import/jobs`
- **Description:** List all import jobs with filters
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `entityType`, `status`, `page`, `limit`

### Cancel Import Job
- **POST** `/import/jobs/:jobId/cancel`
- **Description:** Cancel pending/processing import job
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Retry Failed Import
- **POST** `/import/jobs/:jobId/retry`
- **Description:** Retry failed import records
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Download Import Errors
- **GET** `/import/jobs/:jobId/errors/download`
- **Description:** Download error report (CSV)
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Create Export Job
- **POST** `/export/create`
- **Description:** Create export job to generate downloadable file
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Body Parameters:**
  ```json
  {
    "entityType": "PRODUCT | ORDER | USER | CATEGORY",
    "fileFormat": "CSV | EXCEL | JSON | XML",
    "priority": "NORMAL",
    "filters": {
      "isActive": true,
      "dateRange": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      }
    }
  }
  ```

### Get Export Job Details
- **GET** `/export/jobs/:jobId`
- **Description:** Get export job status with download URL
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### List Export Jobs
- **GET** `/export/jobs`
- **Description:** List all export jobs
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `entityType`, `status`, `page`, `limit`

### Cancel Export Job
- **POST** `/export/jobs/:jobId/cancel`
- **Description:** Cancel queued/processing export
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

### Download Export File
- **GET** `/export/jobs/:jobId/download`
- **Description:** Download generated export file
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)

---

## Cart Analytics (Admin)

### Get Overall Cart Analytics
- **GET** `/api/v1/admin/cart/analytics`
- **Description:** Get comprehensive cart statistics
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `startDate`, `endDate` (ISO 8601 dates, default: last 30 days)

### Get Shipping Revenue Breakdown
- **GET** `/api/v1/admin/cart/shipping-revenue`
- **Description:** Get shipping revenue analytics
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `startDate`, `endDate`

### Get Product Performance
- **GET** `/api/v1/admin/cart/product-performance`
- **Description:** Get top products by cart additions
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `limit` (default: 10)

### Get Abandoned Carts
- **GET** `/api/v1/admin/cart/abandoned`
- **Description:** Get abandoned carts with recovery potential
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `page`, `limit`, `minValue` (minimum cart value)

### Get Daily Cart Trends
- **GET** `/api/v1/admin/cart/trends`
- **Description:** Get daily cart creation trends
- **Auth:** Bearer JWT (ADMIN, SUPER_ADMIN)
- **Query Parameters:**
  - `days` (default: 30)

---

## General Notes

### Authentication
All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Error Responses
Standard error format:
```json
{
  "statusCode": 400,
  "message": "Error description",
  "error": "Bad Request"
}
```

### Pagination
Standard pagination format:
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 10,
    "totalPages": 10
  }
}
```

### Rate Limits
- Authentication endpoints: 3-5 req/min
- Public endpoints: 100 req/min
- Authenticated endpoints: 200 req/min

---

**For interactive API documentation, visit:** `http://localhost:4000/api/docs` (Swagger UI)
