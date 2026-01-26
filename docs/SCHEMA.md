# MASH Backend - Complete Database Schema Documentation

> **Mushroom Automation Smart Harvesting (MASH) - PostgreSQL Database Schema**  
> ORM: Prisma 6 | Database: PostgreSQL 15+ (Neon Serverless)

---

## Table of Contents

1. [Core Entities](#core-entities)
2. [E-commerce](#e-commerce)
3. [IoT & Sensors](#iot--sensors)
4. [Alerts & Notifications](#alerts--notifications)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Management](#api-management)
7. [Analytics & Reporting](#analytics--reporting)
8. [System](#system)
9. [Enumerations](#enumerations)

---

## Core Entities

### User
**Table:** `users`  
**Description:** Core user account model supporting multiple authentication methods

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK, @cuid() | Unique user identifier |
| `clerkId` | String? | Unique | Clerk authentication ID |
| `email` | String | Unique, Required | User email address |
| `username` | String? | Unique | Optional username |
| `firstName` | String? | - | User's first name |
| `lastName` | String? | - | User's last name |
| `imageUrl` | String? | - | Profile picture URL |
| `phoneNumber` | String? | - | Contact phone number |
| `password` | String? | - | Hashed password (bcrypt) |
| `role` | UserRole | Default: USER | User role (USER, ADMIN, SUPER_ADMIN, GROWER, BUYER) |
| `isActive` | Boolean | Default: true | Account active status |
| `emailVerified` | Boolean | Default: false | Email verification status |
| `emailVerificationToken` | String? | - | Email verification token (24h expiry) |
| `emailVerificationCode` | String? | - | 6-digit verification code |
| `emailVerificationCodeExpiry` | DateTime? | - | Code expiration time |
| `passwordResetCode` | String? | - | Password reset code |
| `passwordResetCodeExpiry` | DateTime? | - | Reset code expiration |
| `twoFactorEnabled` | Boolean | Default: false | 2FA enabled status |
| `twoFactorSecret` | String? | - | TOTP secret key |
| `twoFactorBackupCodes` | String[] | - | Emergency backup codes |
| `googleId` | String? | Unique | Google OAuth ID |
| `facebookId` | String? | Unique | Facebook OAuth ID |
| `oauthProvider` | String[] | - | Connected OAuth providers |
| `oauthAccessToken` | String? | - | OAuth access token |
| `oauthRefreshToken` | String? | - | OAuth refresh token |
| `oauthTokenExpiry` | DateTime? | - | Token expiration |
| `preferences` | Json? | - | User preferences (notifications, theme, etc.) |
| `lastLoginAt` | DateTime? | - | Last login timestamp |
| `createdAt` | DateTime | @default(now()) | Account creation date |
| `updatedAt` | DateTime | @updatedAt | Last update timestamp |

**Relations:**
- `addresses`: Address[] (one-to-many)
- `carts`: Cart[] (one-to-many)
- `orders`: Order[] (one-to-many)
- `devices`: Device[] (one-to-many)
- `sessions`: Session[] (one-to-many)
- `apiKeys`: ApiKey[] (one-to-many)
- `userRoleAssignments`: UserRoleAssignment[] (one-to-many)

**Indexes:**
- `[email, isActive]`
- `[emailVerificationToken]`
- `[passwordResetCode, passwordResetCodeExpiry]`
- `[googleId]`, `[facebookId]`
- `[createdAt]`, `[lastLoginAt]`

---

### Address
**Table:** `addresses`  
**Description:** Shipping and billing addresses for users

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Address ID |
| `userId` | String | FK → User | Owner user ID |
| `type` | String | - | Address type (shipping, billing) |
| `firstName` | String | Required | Recipient first name |
| `lastName` | String | Required | Recipient last name |
| `company` | String? | - | Company name |
| `street1` | String | Required | Street address line 1 |
| `street2` | String? | - | Street address line 2 |
| `city` | String | Required | City |
| `state` | String | Required | State/Province |
| `postalCode` | String | Required | ZIP/Postal code |
| `country` | String | Default: "Philippines" | Country |
| `phoneNumber` | String? | - | Contact phone |
| `isDefault` | Boolean | Default: false | Default address flag |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

---

## E-commerce

### Product
**Table:** `products`  
**Description:** Product catalog with inventory tracking

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Product ID |
| `name` | String | Required | Product name |
| `description` | String? | - | Product description |
| `slug` | String | Unique | URL-friendly identifier |
| `sku` | String? | Unique | Stock keeping unit |
| `price` | Decimal | Required | Current price (10,2) |
| `comparePrice` | Decimal? | - | Original/compare-at price |
| `costPrice` | Decimal? | - | Cost price for margin calculation |
| `stock` | Int | Default: 0 | Available inventory |
| `minStock` | Int | Default: 0 | Minimum stock level (alert threshold) |
| `maxCartQty` | Int? | Default: 100 | Maximum quantity per cart |
| `weight` | Float? | - | Product weight (kg) |
| `dimensions` | Json? | - | Dimensions (length, width, height) |
| `images` | Json[] | - | Product image URLs array |
| `categories` | Json[] | - | Category IDs array |
| `tags` | Json[] | - | Product tags for filtering |
| `attributes` | Json? | - | Custom attributes (color, size, etc.) |
| `isActive` | Boolean | Default: true | Product active status |
| `isFeatured` | Boolean | Default: false | Featured product flag |
| `seoTitle` | String? | - | SEO meta title |
| `seoDescription` | String? | - | SEO meta description |
| `isDeleted` | Boolean | Default: false | Soft delete flag |
| `deletedAt` | DateTime? | - | Deletion timestamp |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `cartItems`: CartItem[] (one-to-many)
- `orderItems`: OrderItem[] (one-to-many)

**Indexes:**
- `[slug, isActive]`
- `[isActive, isFeatured, createdAt(desc)]`
- `[stock, minStock]`
- `[isDeleted, isActive]`

---

### Category
**Table:** `categories`  
**Description:** Hierarchical product categories

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Category ID |
| `name` | String | Required | Category name |
| `description` | String? | - | Category description |
| `slug` | String | Unique | URL-friendly identifier |
| `parentId` | String? | FK → Category | Parent category (for hierarchy) |
| `imageUrl` | String? | - | Category image |
| `isActive` | Boolean | Default: true | Active status |
| `sortOrder` | Int | Default: 0 | Display order |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `parent`: Category? (self-referential)
- `children`: Category[] (self-referential)

**Indexes:**
- `[isActive, sortOrder]`
- `[parentId, isActive]`

---

### Cart
**Table:** `carts`  
**Description:** Shopping cart for users and guest sessions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Cart ID |
| `userId` | String? | FK → User | Owner user (null for guest carts) |
| `sessionId` | String? | - | Guest session identifier |
| `status` | CartStatus | Default: ACTIVE | Cart status (ACTIVE, COMPLETED, ABANDONED, EXPIRED, MERGED) |
| `subtotal` | Decimal | Default: 0 | Items total before tax/shipping |
| `tax` | Decimal | Default: 0 | Tax amount |
| `shipping` | Decimal | Default: 0 | Shipping cost |
| `discount` | Decimal | Default: 0 | Discount amount |
| `total` | Decimal | Default: 0 | Grand total |
| `metadata` | Json? | - | Additional cart data |
| `lastActivityAt` | DateTime | @default(now()) | Last modification time |
| `expiresAt` | DateTime? | - | Cart expiration time |
| `abandonedAt` | DateTime? | - | Abandonment timestamp |
| `convertedAt` | DateTime? | - | Order conversion timestamp |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `user`: User? (many-to-one)
- `items`: CartItem[] (one-to-many)

**Indexes:**
- `[userId, status]`
- `[sessionId, status]`
- `[status, lastActivityAt]`

---

### CartItem
**Table:** `cart_items`  
**Description:** Individual items in cart

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Cart item ID |
| `cartId` | String | FK → Cart | Parent cart |
| `productId` | String | FK → Product | Product reference |
| `quantity` | Int | Required | Item quantity |
| `price` | Decimal | Required | Unit price at add time |
| `originalPrice` | Decimal | Required | Original price before discount |
| `subtotal` | Decimal | Required | quantity × price |
| `discount` | Decimal | Default: 0 | Item-level discount |
| `total` | Decimal | Required | Final item total |
| `isAvailable` | Boolean | Default: true | Product availability status |
| `unavailableReason` | String? | - | Reason if unavailable |
| `productSnapshot` | Json? | - | Product data snapshot |
| `customization` | Json? | - | Custom options (size, color, etc.) |
| `createdAt` | DateTime | @default(now()) | Added date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Unique Constraints:**
- `[cartId, productId]` (one product per cart)

---

### Order
**Table:** `orders`  
**Description:** Customer orders

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Order ID |
| `orderNumber` | String | Unique | Human-readable order number |
| `userId` | String | FK → User | Customer |
| `status` | OrderStatus | Default: PENDING | Order status (PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED) |
| `subtotal` | Decimal | Required | Items total |
| `tax` | Decimal | Default: 0 | Tax amount |
| `shipping` | Decimal | Default: 0 | Shipping cost |
| `discount` | Decimal | Default: 0 | Discount amount |
| `total` | Decimal | Required | Grand total |
| `currency` | String | Default: "PHP" | Currency code |
| `notes` | String? | - | Customer notes |
| `shippingAddress` | Json | Required | Shipping address object |
| `billingAddress` | Json | Required | Billing address object |
| `trackingNumber` | String? | - | Shipment tracking number |
| `shippedAt` | DateTime? | - | Shipment date |
| `deliveredAt` | DateTime? | - | Delivery date |
| `cancelledAt` | DateTime? | - | Cancellation date |
| `createdAt` | DateTime | @default(now()) | Order date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `user`: User (many-to-one)
- `orderItems`: OrderItem[] (one-to-many)
- `payments`: Payment[] (one-to-many)

**Indexes:**
- `[userId, status, createdAt(desc)]`
- `[status, createdAt(desc)]`
- `[orderNumber]`
- `[deliveredAt]`

---

### OrderItem
**Table:** `order_items`  
**Description:** Line items in orders

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Order item ID |
| `orderId` | String | FK → Order | Parent order |
| `productId` | String | FK → Product | Product reference |
| `quantity` | Int | Required | Quantity ordered |
| `price` | Decimal | Required | Unit price at order time |
| `total` | Decimal | Required | Line total |

**Indexes:**
- `[orderId]`, `[productId]`
- `[productId, orderId]`

---

### Payment
**Table:** `payments`  
**Description:** Payment transactions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Payment ID |
| `orderId` | String? | FK → Order | Associated order |
| `userId` | String | FK → User | Payer |
| `amount` | Decimal | Required | Payment amount |
| `currency` | String | Default: "PHP" | Currency code |
| `status` | PaymentStatus | Default: PENDING | Payment status (PENDING, PAID, FAILED, REFUNDED) |
| `method` | PaymentMethod | Required | Payment method (CREDIT_CARD, GCASH, MAYA, etc.) |
| `transactionId` | String? | Unique | Gateway transaction ID |
| `gatewayResponse` | Json? | - | Payment gateway response |
| `processedAt` | DateTime? | - | Processing timestamp |
| `failedAt` | DateTime? | - | Failure timestamp |
| `refundedAt` | DateTime? | - | Refund timestamp |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[userId, status, createdAt(desc)]`
- `[transactionId]`

---

## IoT & Sensors

### Device
**Table:** `devices`  
**Description:** IoT devices for mushroom cultivation monitoring

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Device ID |
| `name` | String | Required | Device name |
| `type` | DeviceType | Required | Device type (MUSHROOM_CHAMBER, ENVIRONMENTAL_SENSOR, etc.) |
| `serialNumber` | String | Unique | Hardware serial number |
| `status` | DeviceStatus | Default: OFFLINE | Device status (ONLINE, OFFLINE, MAINTENANCE, ERROR) |
| `userId` | String? | FK → User | Device owner |
| `location` | String? | - | Physical location |
| `description` | String? | - | Device description |
| `firmware` | String? | - | Firmware version |
| `ipAddress` | String? | - | Network IP address |
| `macAddress` | String? | - | MAC address |
| `lastSeen` | DateTime? | - | Last communication timestamp |
| `isActive` | Boolean | Default: true | Active status |
| `createdAt` | DateTime | @default(now()) | Registration date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `user`: User? (many-to-one)
- `sensors`: Sensor[] (one-to-many)
- `sensorData`: SensorData[] (one-to-many)
- `deviceCommands`: DeviceCommand[] (one-to-many)
- `healthRecords`: DeviceHealth[] (one-to-many)
- `alerts`: SensorAlert[] (one-to-many)

**Indexes:**
- `[userId, status, isActive]`
- `[status, lastSeen(desc)]`
- `[serialNumber]`

---

### Sensor
**Table:** `sensors`  
**Description:** Individual sensors attached to devices

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Sensor ID |
| `deviceId` | String | FK → Device | Parent device |
| `type` | String | Required | Sensor type (temperature, humidity, pH, etc.) |
| `name` | String | Required | Sensor name |
| `unit` | String | Required | Measurement unit (°C, %, etc.) |
| `minValue` | Float? | - | Minimum valid value |
| `maxValue` | Float? | - | Maximum valid value |
| `calibration` | Json? | - | Calibration parameters |
| `isActive` | Boolean | Default: true | Active status |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `device`: Device (many-to-one)
- `sensorData`: SensorData[] (one-to-many)
- `alerts`: SensorAlert[] (one-to-many)

---

### SensorData
**Table:** `sensor_data`  
**Description:** Time-series sensor readings

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Reading ID |
| `deviceId` | String | FK → Device | Source device |
| `sensorId` | String? | FK → Sensor | Source sensor |
| `userId` | String | FK → User | User who recorded |
| `type` | String | Required | Data type |
| `value` | Float | Required | Sensor reading value |
| `unit` | String | Required | Measurement unit |
| `quality` | String? | - | Data quality indicator |
| `timestamp` | DateTime | @default(now()) | Reading timestamp |

**Indexes:**
- `[deviceId, timestamp]`
- `[type, timestamp]`

---

### DeviceCommand
**Table:** `device_commands`  
**Description:** Commands sent to IoT devices via MQTT

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Command ID |
| `deviceId` | String | FK → Device | Target device |
| `command` | String | Required | Command name (RESTART, UPDATE_CONFIG, etc.) |
| `parameters` | Json? | - | Command parameters |
| `status` | String | Default: "pending" | Command status |
| `response` | Json? | - | Device response |
| `sentAt` | DateTime | @default(now()) | Sent timestamp |
| `acknowledgedAt` | DateTime? | - | Acknowledgment timestamp |

---

### DeviceHealth
**Table:** `device_health`  
**Description:** Device health metrics and diagnostics

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Health record ID |
| `deviceId` | String | FK → Device | Device reference |
| `timestamp` | DateTime | @default(now()) | Measurement time |
| `status` | DeviceHealthStatus | Required | Health status (HEALTHY, WARNING, CRITICAL, OFFLINE, MAINTENANCE) |
| `cpuUsage` | Float? | - | CPU usage percentage |
| `memoryUsage` | Float? | - | Memory usage percentage |
| `diskUsage` | Float? | - | Disk usage percentage |
| `temperature` | Float? | - | Device temperature (°C) |
| `batteryLevel` | Float? | - | Battery level percentage |
| `networkLatency` | Int? | - | Network latency (ms) |
| `uptime` | Int? | - | Uptime (seconds) |
| `errorCount` | Int | Default: 0 | Error count |
| `metadata` | Json? | - | Additional metrics |
| `createdAt` | DateTime | @default(now()) | Created date |

**Indexes:**
- `[deviceId, timestamp(desc)]`
- `[status]`

---

### SensorAlert
**Table:** `sensor_alerts`  
**Description:** Sensor threshold alerts

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Alert ID |
| `deviceId` | String? | FK → Device | Related device |
| `sensorId` | String? | FK → Sensor | Related sensor |
| `type` | String | Required | Alert type |
| `severity` | String | Required | Severity level |
| `title` | String | Required | Alert title |
| `message` | String | Required | Alert message |
| `threshold` | Json? | - | Threshold configuration |
| `isActive` | Boolean | Default: true | Active status |
| `isResolved` | Boolean | Default: false | Resolution status |
| `resolvedAt` | DateTime? | - | Resolution timestamp |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

---

## Alerts & Notifications

### Alert
**Table:** `alerts`  
**Description:** System-wide alerts and notifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK, @uuid() | Alert ID |
| `ruleId` | String | FK → AlertRule | Alert rule reference |
| `title` | String | Required | Alert title |
| `message` | String | Required | Alert message |
| `category` | AlertCategory | Required | Alert category (SYSTEM, SECURITY, BUSINESS, USER, SENSOR, ORDER, PAYMENT) |
| `priority` | AlertPriority | Required | Priority (CRITICAL, HIGH, MEDIUM, LOW) |
| `status` | AlertStatus | Default: PENDING | Status (PENDING, SENT, ACKNOWLEDGED, RESOLVED, etc.) |
| `eventType` | String | Required | Event type that triggered alert |
| `eventId` | String? | - | Related event ID |
| `eventData` | Json? | - | Event payload |
| `fingerprint` | String | Required | Alert deduplication key |
| `groupKey` | String? | - | Alert grouping key |
| `severity` | Int | Default: 5 | Numeric severity (1-10) |
| `tags` | String[] | - | Alert tags |
| `metadata` | Json? | - | Additional data |
| `occurrenceCount` | Int | Default: 1 | Number of occurrences |
| `firstOccurrence` | DateTime | @default(now()) | First occurrence time |
| `lastOccurrence` | DateTime | @default(now()) | Last occurrence time |
| `triggeredAt` | DateTime | @default(now()) | Trigger time |
| `acknowledgedAt` | DateTime? | - | Acknowledgment time |
| `resolvedAt` | DateTime? | - | Resolution time |
| `escalatedAt` | DateTime? | - | Escalation time |
| `snoozedUntil` | DateTime? | - | Snooze until time |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `rule`: AlertRule (many-to-one)
- `acknowledgments`: AlertAcknowledgment[] (one-to-many)
- `notifications`: Notification[] (one-to-many)

**Indexes:**
- `[ruleId]`, `[status]`, `[priority]`, `[fingerprint]`
- `[eventType, eventId]`
- `[triggeredAt]`

---

### AlertRule
**Table:** `alert_rules`  
**Description:** Alert rule definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK, @uuid() | Rule ID |
| `name` | String | Required | Rule name |
| `description` | String? | - | Rule description |
| `category` | AlertCategory | Required | Alert category |
| `priority` | AlertPriority | Required | Alert priority |
| `eventType` | String | Required | Event type to monitor |
| `condition` | Json | Required | Trigger condition logic |
| `activeHours` | Json? | - | Active time windows |
| `cooldownMinutes` | Int | Default: 15 | Cooldown period |
| `isActive` | Boolean | Default: true | Rule active status |
| `isDeleted` | Boolean | Default: false | Soft delete flag |
| `createdBy` | String | FK → User | Creator user ID |
| `updatedBy` | String? | FK → User | Last updater user ID |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `creator`: User (many-to-one)
- `updater`: User? (many-to-one)
- `recipients`: AlertRuleRecipient[] (one-to-many)
- `alerts`: Alert[] (one-to-many)

---

### Notification
**Table:** `notifications`  
**Description:** Notification delivery tracking

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK, @uuid() | Notification ID |
| `userId` | String? | FK → User | Recipient user |
| `alertId` | String? | FK → Alert | Related alert |
| `templateId` | String? | FK → NotificationTemplate | Template used |
| `channel` | NotificationChannel | Required | Delivery channel (EMAIL, SMS, PUSH, IN_APP, WEBHOOK) |
| `status` | NotificationStatus | Default: PENDING | Delivery status |
| `priority` | Int | Default: 5 | Priority (1-10) |
| `recipientId` | String? | - | Recipient identifier |
| `recipientEmail` | String? | - | Email address |
| `recipientPhone` | String? | - | Phone number |
| `subject` | String? | - | Email subject |
| `body` | String | Required | Message body |
| `provider` | String? | - | Service provider used |
| `providerMessageId` | String? | - | Provider message ID |
| `providerResponse` | Json? | - | Provider response |
| `metadata` | Json? | - | Additional data |
| `retryCount` | Int | Default: 0 | Retry attempts |
| `maxRetries` | Int | Default: 3 | Max retry attempts |
| `nextRetryAt` | DateTime? | - | Next retry time |
| `queuedAt` | DateTime? | - | Queue time |
| `sentAt` | DateTime? | - | Send time |
| `deliveredAt` | DateTime? | - | Delivery time |
| `failedAt` | DateTime? | - | Failure time |
| `errorMessage` | String? | - | Error details |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[userId, status, createdAt(desc)]`
- `[status, priority, queuedAt]`
- `[status, nextRetryAt]`

---

## Authentication & Authorization

### Session
**Table:** `sessions`  
**Description:** User authentication sessions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Session ID |
| `userId` | String | FK → User | Session owner |
| `clerkSessionId` | String? | Unique | Clerk session ID |
| `token` | String | Unique | JWT token |
| `status` | SessionStatus | Default: ACTIVE | Session status (ACTIVE, EXPIRED, REVOKED) |
| `deviceInfo` | Json? | - | Device information |
| `ipAddress` | String? | - | IP address |
| `userAgent` | String? | - | User agent string |
| `lastActivity` | DateTime | @default(now()) | Last activity time |
| `expiresAt` | DateTime | Required | Expiration time |
| `revokedAt` | DateTime? | - | Revocation time |
| `revokedReason` | String? | - | Revocation reason |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[userId]`, `[status]`, `[expiresAt]`, `[clerkSessionId]`

---

### Role
**Table:** `roles`  
**Description:** User roles for RBAC

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Role ID |
| `name` | String | Unique | Role name |
| `description` | String? | - | Role description |
| `isSystem` | Boolean | Default: false | System role flag |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Relations:**
- `rolePermissions`: RolePermission[] (one-to-many)
- `userRoleAssignments`: UserRoleAssignment[] (one-to-many)

---

### Permission
**Table:** `permissions`  
**Description:** Granular permissions for RBAC

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Permission ID |
| `resource` | String | Required | Resource name |
| `action` | String | Required | Action name (create, read, update, delete) |
| `description` | String? | - | Permission description |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Unique Constraints:**
- `[resource, action]`

---

### ApiKey
**Table:** `api_keys`  
**Description:** API access keys for programmatic access

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | API key ID |
| `userId` | String | FK → User | Key owner |
| `name` | String | Required | Key name/description |
| `keyHash` | String | Unique | Hashed key value |
| `keyPrefix` | String | Required | Key prefix (for identification) |
| `scopes` | Json | Required | Access scopes |
| `lastUsedAt` | DateTime? | - | Last use timestamp |
| `expiresAt` | DateTime? | - | Expiration time |
| `revokedAt` | DateTime? | - | Revocation time |
| `revokedReason` | String? | - | Revocation reason |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[userId]`, `[keyPrefix]`, `[expiresAt]`

---

## API Management

### RateLimitLog
**Table:** `rate_limit_logs`  
**Description:** Rate limiting tracking and analytics

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Log ID |
| `identifier` | String | Required | User/IP identifier |
| `endpoint` | String | Required | API endpoint |
| `count` | Int | Default: 1 | Request count |
| `windowStart` | DateTime | Required | Time window start |
| `windowEnd` | DateTime | Required | Time window end |
| `blocked` | Boolean | Default: false | Blocked flag |
| `createdAt` | DateTime | @default(now()) | Created date |

**Unique Constraints:**
- `[identifier, endpoint, windowStart]`

**Indexes:**
- `[identifier, blocked, windowStart]`
- `[identifier, windowStart, windowEnd]`
- `[endpoint, blocked, windowStart]`

---

### ApiUsageLog
**Table:** `api_usage_logs`  
**Description:** API usage analytics and monitoring

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Log ID |
| `userId` | String? | FK → User | User making request |
| `apiKey` | String? | - | API key used |
| `endpoint` | String | Required | API endpoint |
| `method` | String | Required | HTTP method |
| `version` | String | Required | API version |
| `statusCode` | Int | Required | HTTP status code |
| `responseTime` | Int | Required | Response time (ms) |
| `requestSize` | Int? | - | Request size (bytes) |
| `responseSize` | Int? | - | Response size (bytes) |
| `ipAddress` | String | Required | Client IP |
| `userAgent` | String? | - | User agent |
| `referer` | String? | - | Referer header |
| `rateLimitHit` | Boolean | Default: false | Rate limit hit flag |
| `throttled` | Boolean | Default: false | Throttled flag |
| `queueTime` | Int? | - | Queue time (ms) |
| `metadata` | Json? | - | Additional data |
| `timestamp` | DateTime | @default(now()) | Request time |

**Indexes:**
- `[userId, timestamp]`, `[endpoint, timestamp]`
- `[apiKey]`, `[timestamp]`

---

## Analytics & Reporting

### Report
**Table:** `reports`  
**Description:** Report definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK, @uuid() | Report ID |
| `name` | String | Required | Report name |
| `description` | String? | - | Report description |
| `type` | ReportType | Required | Report type (SALES, REVENUE, USERS, PRODUCTS, etc.) |
| `configuration` | Json | Required | Report configuration |
| `schedule` | Json? | - | Schedule configuration |
| `isActive` | Boolean | Default: true | Active status |
| `createdBy` | String | Required | Creator user ID |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[type]`, `[createdBy]`, `[isActive, type]`

---

### SearchLog
**Table:** `search_logs`  
**Description:** Search analytics

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Log ID |
| `query` | String | Required | Search query |
| `index` | String | Required | Search index |
| `resultsCount` | Int | Required | Number of results |
| `took` | Int | Required | Query time (ms) |
| `filters` | Json? | - | Applied filters |
| `sort` | Json? | - | Sort criteria |
| `userId` | String? | - | User ID |
| `ipAddress` | String? | - | IP address |
| `userAgent` | String? | - | User agent |
| `clickedResult` | String? | - | Clicked result ID |
| `isSlowQuery` | Boolean | Default: false | Slow query flag (>1000ms) |
| `createdAt` | DateTime | @default(now()) | Query time |

**Indexes:**
- `[query]`, `[createdAt]`, `[isSlowQuery, took]`
- `[userId, createdAt]`, `[index, createdAt]`

---

## System

### SystemConfig
**Table:** `system_config`  
**Description:** System-wide configuration settings

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Config ID |
| `key` | String | Unique | Configuration key |
| `value` | Json | Required | Configuration value |
| `description` | String? | - | Config description |
| `category` | String? | - | Config category |
| `isPublic` | Boolean | Default: false | Public access flag |
| `createdAt` | DateTime | @default(now()) | Created date |
| `updatedAt` | DateTime | @updatedAt | Updated date |

**Indexes:**
- `[key, isPublic]`, `[category, isPublic]`

---

### AuditLog
**Table:** `audit_logs`  
**Description:** Audit trail for sensitive operations

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Log ID |
| `userId` | String? | - | User performing action |
| `action` | String | Required | Action performed |
| `entity` | String | Required | Entity type |
| `entityId` | String? | - | Entity ID |
| `oldValues` | Json? | - | Previous values |
| `newValues` | Json? | - | New values |
| `ipAddress` | String? | - | IP address |
| `userAgent` | String? | - | User agent |
| `timestamp` | DateTime | @default(now()) | Action time |

**Indexes:**
- `[userId, timestamp]`, `[entity, entityId]`

---

### SecurityLog
**Table:** `security_logs`  
**Description:** Security event logging

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | PK | Log ID |
| `userId` | String? | - | Related user |
| `event` | String | Required | Event type |
| `severity` | String | Required | Severity level |
| `ipAddress` | String? | - | IP address |
| `userAgent` | String? | - | User agent |
| `metadata` | Json? | - | Event data |
| `timestamp` | DateTime | @default(now()) | Event time |

**Indexes:**
- `[userId, timestamp]`, `[event]`, `[severity]`, `[timestamp]`

---

## Reports & Analytics

### Report
Report definitions for scheduled and on-demand analytics.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(uuid()) | Report ID |
| `name` | String | Required | Report name |
| `description` | String? | - | Report description |
| `type` | ReportType | Required | SALES, REVENUE, USERS, PRODUCTS, ORDERS, DEVICES, CUSTOM |
| `configuration` | Json | Required | Report parameters & filters |
| `schedule` | Json? | - | Cron schedule (if scheduled) |
| `isActive` | Boolean | @default(true) | Active status |
| `createdBy` | String | Required | Creator user ID |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Relations:**
- `executions` → ReportExecution[] (One-to-many)
- `subscriptions` → ReportSubscription[] (One-to-many)

**Indexes:**
- `[type]`, `[createdBy]`, `[isActive, type]`

---

### ReportExecution
Report execution history and results.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(uuid()) | Execution ID |
| `reportId` | String | Required | Report ID (FK) |
| `status` | ExecutionStatus | @default(PENDING) | PENDING, RUNNING, COMPLETED, FAILED, CANCELLED |
| `startedAt` | DateTime | @default(now()) | Execution start time |
| `completedAt` | DateTime? | - | Completion time |
| `duration` | Int? | - | Duration in milliseconds |
| `resultData` | Json? | - | Report data (if small) |
| `resultUrl` | String? | - | S3 URL (if large) |
| `errorMessage` | String? | - | Error message if failed |
| `executedBy` | String? | - | User ID who triggered |

**Relations:**
- `report` → Report (Many-to-one, cascade delete)

**Indexes:**
- `[reportId]`, `[status]`, `[startedAt]`, `[reportId, status]`

---

### ReportSubscription
Report subscriptions for scheduled delivery.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(uuid()) | Subscription ID |
| `reportId` | String | Required | Report ID (FK) |
| `userId` | String | Required | Subscriber user ID |
| `channel` | NotificationChannel | Required | EMAIL, SMS, PUSH, IN_APP |
| `frequency` | SubscriptionFrequency | Required | DAILY, WEEKLY, MONTHLY, REAL_TIME |
| `isActive` | Boolean | @default(true) | Active status |
| `lastSentAt` | DateTime? | - | Last sent time |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Relations:**
- `report` → Report (Many-to-one, cascade delete)

**Unique Constraints:**
- `[reportId, userId, channel]`

**Indexes:**
- `[reportId]`, `[userId]`, `[isActive, frequency]`

---

## Import/Export System

### ImportExportJob
Tracks bulk data import/export operations with progress and error logging.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(cuid()) | Job ID |
| `type` | JobType | Required | IMPORT, EXPORT |
| `entityType` | EntityType | Required | PRODUCT, ORDER, USER, CATEGORY, SELLER, BUYER, TRANSACTION, INVENTORY |
| `status` | JobStatus | Required | QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED |
| `priority` | JobPriority | Required | URGENT, NORMAL, LOW |
| `fileName` | String | Required | Original file name |
| `fileFormat` | FileFormat | Required | CSV, EXCEL, JSON, XML |
| `fileSize` | Int | Required | File size in bytes |
| `fileUrl` | String? | - | S3 upload URL |
| `resultFileUrl` | String? | - | Result file URL (errors/warnings) |
| `totalRecords` | Int | @default(0) | Total rows/records |
| `processedRecords` | Int | @default(0) | Processed count |
| `successCount` | Int | @default(0) | Successful operations |
| `failureCount` | Int | @default(0) | Failed operations |
| `warningCount` | Int | @default(0) | Warnings |
| `progressPercent` | Float | @default(0) | Progress percentage (0-100) |
| `startedAt` | DateTime? | - | Processing start time |
| `completedAt` | DateTime? | - | Completion time |
| `estimatedTimeMs` | Int? | - | Estimated time remaining |
| `options` | Json? | - | Import/export options |
| `filters` | Json? | - | Export filters |
| `createdBy` | String | Required | Creator user ID |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Relations:**
- `errors` → ImportExportError[] (One-to-many)
- `createdByUser` → User (Many-to-one)

**Indexes:**
- `[status, createdAt]`, `[entityType, type]`, `[createdBy]`

---

### ImportExportError
Detailed error logging for import/export operations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(cuid()) | Error ID |
| `jobId` | String | Required | Job ID (FK) |
| `rowNumber` | Int? | - | Row number in file |
| `columnName` | String? | - | Column name |
| `fieldPath` | String? | - | JSON field path |
| `errorType` | ErrorType | Required | VALIDATION, CONSTRAINT, FORMAT, BUSINESS_RULE |
| `severity` | ErrorSeverity | Required | ERROR, WARNING |
| `errorCode` | String | Required | Error code |
| `message` | String | Required | Error message |
| `suggestion` | String? | - | How to fix |
| `originalValue` | String? | - | Original invalid value |
| `expectedFormat` | String? | - | Expected format |
| `createdAt` | DateTime | @default(now()) | Error time |

**Relations:**
- `job` → ImportExportJob (Many-to-one, cascade delete)

**Indexes:**
- `[jobId, severity]`

---

### ImportExportTemplate
Reusable templates for import/export operations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(cuid()) | Template ID |
| `name` | String | Required | Template name |
| `description` | String? | - | Template description |
| `entityType` | EntityType | Required | Entity type |
| `fileFormat` | FileFormat | Required | File format |
| `headers` | Json | Required | Column headers mapping |
| `sampleData` | Json | Required | Sample rows |
| `validation` | Json | Required | Validation rules |
| `isActive` | Boolean | @default(true) | Active status |
| `createdBy` | String | Required | Creator user ID |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Indexes:**
- `[entityType, fileFormat]`

---

## Delivery Integration

### LalamoveQuotation
Delivery quotations from Lalamove API (Philippines market).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(cuid()) | Internal ID |
| `quotationId` | String | @unique | Lalamove quotation ID |
| `serviceType` | String | Required | MOTORCYCLE, SEDAN, VAN, etc. |
| `totalPrice` | Float | Required | Total delivery price |
| `currency` | String | @default("PHP") | Currency code |
| `distance` | Float | Required | Distance in km |
| `distanceUnit` | String | @default("km") | Distance unit |
| `stops` | Json | Required | Pickup/dropoff locations |
| `isScheduled` | Boolean | @default(false) | Scheduled delivery |
| `scheduleAt` | DateTime? | - | Scheduled delivery time |
| `expiresAt` | DateTime | Required | Quotation expiry (5min) |
| `status` | String | @default("ACTIVE") | ACTIVE, EXPIRED, USED |
| `userId` | String? | - | User ID |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Indexes:**
- `[quotationId]`, `[status]`, `[userId]`, `[createdAt]`

---

### LalamoveOrder
Active delivery orders with tracking and POD.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(cuid()) | Internal ID |
| `orderId` | String | @unique | Lalamove order ID |
| `quotationId` | String | Required | Original quotation ID |
| `status` | String | Required | ASSIGNING, PICKED_UP, COMPLETED, CANCELLED |
| `driverId` | String? | - | Assigned driver ID |
| `shareLink` | String | Required | Public tracking URL |
| `totalPrice` | Float | Required | Total price |
| `currency` | String | @default("PHP") | Currency code |
| `distance` | Float | Required | Distance in km |
| `distanceUnit` | String | @default("km") | Distance unit |
| `stops` | Json | Required | Delivery stops with status |
| `isPODEnabled` | Boolean | @default(true) | Proof of delivery |
| `podStatus` | String? | - | POD status |
| `podImage` | String? | - | POD photo URL |
| `podSignature` | String? | - | POD signature URL |
| `orderReference` | String? | - | MASH order reference |
| `userId` | String? | - | User ID |
| `createdAt` | DateTime | @default(now()) | Creation time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Indexes:**
- `[orderId]`, `[quotationId]`, `[status]`, `[userId]`, `[driverId]`, `[createdAt]`

---

## Push Notifications

### PushSubscription
Web push notification subscriptions for browsers and PWA.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String | @id @default(uuid()) | Subscription ID |
| `userId` | String | Required | User ID (FK) |
| `deviceId` | String? | - | IoT device ID (FK) |
| `endpoint` | String | @unique | Push service endpoint URL |
| `keys` | Json | Required | P256dh and auth keys |
| `userAgent` | String? | - | Browser user agent |
| `isActive` | Boolean | @default(true) | Active status |
| `createdAt` | DateTime | @default(now()) | Subscription time |
| `updatedAt` | DateTime | @updatedAt | Last update time |

**Relations:**
- `user` → User (Many-to-one, cascade delete)
- `device` → Device? (Many-to-one, cascade delete)

**Indexes:**
- `[userId]`, `[deviceId]`, `[isActive]`

---

## Enumerations

### UserRole
```prisma
enum UserRole {
  USER           // Regular customer
  ADMIN          // System administrator
  SUPER_ADMIN    // Super administrator
  GROWER         // Mushroom grower/producer
  BUYER          // Business buyer
}
```

### OrderStatus
```prisma
enum OrderStatus {
  PENDING        // Order placed, awaiting confirmation
  CONFIRMED      // Order confirmed
  PROCESSING     // Order being prepared
  SHIPPED        // Order shipped
  DELIVERED      // Order delivered
  CANCELLED      // Order cancelled
  REFUNDED       // Order refunded
}
```

### PaymentStatus
```prisma
enum PaymentStatus {
  PENDING        // Payment pending
  PAID           // Payment successful
  FAILED         // Payment failed
  REFUNDED       // Payment refunded
}
```

### PaymentMethod
```prisma
enum PaymentMethod {
  CREDIT_CARD    // Credit card
  DEBIT_CARD     // Debit card
  PAYPAL         // PayPal
  GCASH          // GCash
  MAYA           // Maya
  BANK_TRANSFER  // Bank transfer
  COD            // Cash on delivery
}
```

### DeviceType
```prisma
enum DeviceType {
  MUSHROOM_CHAMBER       // Mushroom growing chamber
  ENVIRONMENTAL_SENSOR   // Environmental sensor
  IRRIGATION_SYSTEM      // Irrigation system
  HVAC_CONTROLLER        // HVAC controller
  CAMERA                 // Camera
  pH_SENSOR              // pH sensor
  HUMIDITY_CONTROLLER    // Humidity controller
}
```

### DeviceStatus
```prisma
enum DeviceStatus {
  ONLINE         // Device online and responding
  OFFLINE        // Device offline
  MAINTENANCE    // Under maintenance
  ERROR          // Device error
}
```

### CartStatus
```prisma
enum CartStatus {
  ACTIVE         // Active shopping cart
  COMPLETED      // Converted to order
  ABANDONED      // Cart abandoned
  EXPIRED        // Cart expired
  MERGED         // Merged with another cart
}
```

### AlertCategory
```prisma
enum AlertCategory {
  SYSTEM         // System alerts
  SECURITY       // Security alerts
  BUSINESS       // Business alerts
  USER           // User-related alerts
  SENSOR         // Sensor alerts
  ORDER          // Order alerts
  PAYMENT        // Payment alerts
}
```

### AlertPriority
```prisma
enum AlertPriority {
  CRITICAL       // Critical priority
  HIGH           // High priority
  MEDIUM         // Medium priority
  LOW            // Low priority
}
```

### NotificationChannel
```prisma
enum NotificationChannel {
  EMAIL          // Email notification
  SMS            // SMS notification
  PUSH           // Push notification
  IN_APP         // In-app notification
  WEBHOOK        // Webhook notification
}
```

### NotificationStatus
```prisma
enum NotificationStatus {
  PENDING        // Queued for delivery
  QUEUED         // In delivery queue
  SENDING        // Currently sending
  SENT           // Successfully sent
  DELIVERED      // Delivered to recipient
  FAILED         // Delivery failed
  BOUNCED        // Email bounced
  RETRYING       // Retrying delivery
  CANCELLED      // Delivery cancelled
}
```

---

## Database Indexes Strategy

### Performance Optimizations
1. **Composite Indexes:** Used for common query patterns (e.g., `[userId, status, createdAt]`)
2. **Partial Indexes:** Filtered indexes for active/non-deleted records
3. **Covering Indexes:** Include frequently selected columns
4. **Time-series Optimization:** Descending timestamp indexes for recent data queries

### Index Naming Convention
- `idx_tablename_columns` for custom indexes
- Auto-generated indexes for foreign keys and unique constraints

---

**For complete schema definition, see:** [prisma/schema.prisma](prisma/schema.prisma)
