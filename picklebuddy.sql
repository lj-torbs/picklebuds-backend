/*
PickleBuddy backend-ready prototype database
Updated on Monday, August 24, 2026.

Supported flows:
- Player, owner, and admin accounts
- Private court booking
- Open Play booking with participant counts and seat limits
- Whole-gym booking
- Manual payment review using owner-configured QR/account methods
- Pasalo offers and owner-reviewed transfer claims
- Rental gear attached to bookings
- Admin settlement tracking and owner lock/suspension
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `picklebuddy`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE `picklebuddy`;

DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `owner_settlements`;
DROP TABLE IF EXISTS `pasalo_claims`;
DROP TABLE IF EXISTS `pasalo_offers`;
DROP TABLE IF EXISTS `transactions`;
DROP TABLE IF EXISTS `booking_rentals`;
DROP TABLE IF EXISTS `booking_payments`;
DROP TABLE IF EXISTS `booking_slots`;
DROP TABLE IF EXISTS `bookings`;
DROP TABLE IF EXISTS `rental_items`;
DROP TABLE IF EXISTS `court_available_slots`;
DROP TABLE IF EXISTS `courts`;
DROP TABLE IF EXISTS `venue_available_slots`;
DROP TABLE IF EXISTS `venue_booking_settings`;
DROP TABLE IF EXISTS `venue_payment_methods`;
DROP TABLE IF EXISTS `venues`;
DROP TABLE IF EXISTS `admins`;
DROP TABLE IF EXISTS `owners`;
DROP TABLE IF EXISTS `players`;

CREATE TABLE `players` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(32) NOT NULL,
  `full_name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(160) NOT NULL,
  `password_hash` VARCHAR(255) NULL,
  `phone` VARCHAR(32) NULL,
  `location` VARCHAR(160) NULL,
  `status` ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_players_public_id` (`public_id`),
  UNIQUE KEY `uq_players_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `owners` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(32) NOT NULL,
  `full_name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(160) NOT NULL,
  `password_hash` VARCHAR(255) NULL,
  `phone` VARCHAR(32) NULL,
  `business_name` VARCHAR(160) NULL,
  `status` ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active',
  `system_payment_status` ENUM('paid', 'unpaid') NOT NULL DEFAULT 'unpaid',
  `suspension_reason` ENUM('system_payment_due', 'manual_review') NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_owners_public_id` (`public_id`),
  UNIQUE KEY `uq_owners_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `admins` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(32) NOT NULL,
  `full_name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(160) NOT NULL,
  `password_hash` VARCHAR(255) NULL,
  `status` ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_admins_public_id` (`public_id`),
  UNIQUE KEY `uq_admins_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `venues` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(64) NOT NULL,
  `owner_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(160) NOT NULL,
  `address` VARCHAR(255) NOT NULL,
  `phone` VARCHAR(32) NULL,
  `status` ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  `image_url` LONGTEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_venues_public_id` (`public_id`),
  KEY `idx_venues_owner_id` (`owner_id`),
  CONSTRAINT `fk_venues_owner`
    FOREIGN KEY (`owner_id`) REFERENCES `owners` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `venue_booking_settings` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `whole_gym_enabled` TINYINT(1) NOT NULL DEFAULT 0,
  `whole_gym_price_per_hour` DECIMAL(10,2) NULL,
  `whole_gym_notes` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_venue_booking_settings_venue_id` (`venue_id`),
  CONSTRAINT `fk_venue_booking_settings_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `venue_available_slots` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `slot_label` VARCHAR(32) NOT NULL,
  `sort_order` SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_venue_slot` (`venue_id`, `slot_label`),
  CONSTRAINT `fk_venue_slots_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `venue_payment_methods` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `provider` ENUM('GCash', 'Bank Transfer', 'Maya', 'Other') NOT NULL,
  `display_name` VARCHAR(160) NOT NULL,
  `account_name` VARCHAR(160) NOT NULL,
  `account_number` VARCHAR(120) NOT NULL,
  `instructions` TEXT NULL,
  `qr_code_image_url` LONGTEXT NOT NULL,
  `qr_code_file_name` VARCHAR(255) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_payment_methods_venue_id` (`venue_id`),
  CONSTRAINT `fk_payment_methods_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `courts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(64) NOT NULL,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(120) NOT NULL,
  `surface` VARCHAR(120) NOT NULL,
  `capacity_label` VARCHAR(120) NOT NULL,
  `price_per_hour` DECIMAL(10,2) NOT NULL,
  `status` ENUM('available', 'maintenance') NOT NULL DEFAULT 'available',
  `booking_mode` ENUM('private', 'open_play') NOT NULL DEFAULT 'private',
  `open_play_capacity` INT UNSIGNED NULL,
  `image_url` LONGTEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_courts_public_id` (`public_id`),
  KEY `idx_courts_venue_id` (`venue_id`),
  CONSTRAINT `fk_courts_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `court_available_slots` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `court_id` BIGINT UNSIGNED NOT NULL,
  `slot_label` VARCHAR(32) NOT NULL,
  `sort_order` SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_court_slot` (`court_id`, `slot_label`),
  CONSTRAINT `fk_court_slots_court`
    FOREIGN KEY (`court_id`) REFERENCES `courts` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `rental_items` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(64) NOT NULL,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(120) NOT NULL,
  `category` ENUM('paddle', 'ball', 'shoes', 'net', 'other') NOT NULL,
  `price_per_session` DECIMAL(10,2) NOT NULL,
  `quantity_available` INT UNSIGNED NOT NULL DEFAULT 0,
  `status` ENUM('available', 'unavailable') NOT NULL DEFAULT 'available',
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_rental_items_public_id` (`public_id`),
  KEY `idx_rental_items_venue_id` (`venue_id`),
  CONSTRAINT `fk_rental_items_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `bookings` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(32) NOT NULL,
  `player_id` BIGINT UNSIGNED NOT NULL,
  `original_player_id` BIGINT UNSIGNED NOT NULL,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `court_id` BIGINT UNSIGNED NULL,
  `booking_type` ENUM('private', 'open_play', 'whole_gym') NOT NULL DEFAULT 'private',
  `booking_date` DATE NOT NULL,
  `participant_count` INT UNSIGNED NOT NULL DEFAULT 1,
  `status` ENUM('pending', 'confirmed', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
  `payment_status` ENUM('unpaid', 'paid', 'refunded') NOT NULL DEFAULT 'unpaid',
  `booked_by_name_snapshot` VARCHAR(120) NOT NULL,
  `booked_by_email_snapshot` VARCHAR(160) NOT NULL,
  `owner_name_snapshot` VARCHAR(120) NULL,
  `owner_email_snapshot` VARCHAR(160) NULL,
  `base_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `rental_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_bookings_public_id` (`public_id`),
  KEY `idx_bookings_player_id` (`player_id`),
  KEY `idx_bookings_original_player_id` (`original_player_id`),
  KEY `idx_bookings_venue_id` (`venue_id`),
  KEY `idx_bookings_court_id` (`court_id`),
  KEY `idx_bookings_type_date_status` (`booking_type`, `booking_date`, `status`),
  CONSTRAINT `fk_bookings_player`
    FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_bookings_original_player`
    FOREIGN KEY (`original_player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_bookings_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_bookings_court`
    FOREIGN KEY (`court_id`) REFERENCES `courts` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `booking_slots` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT UNSIGNED NOT NULL,
  `slot_label` VARCHAR(32) NOT NULL,
  `sort_order` SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_booking_slot` (`booking_id`, `slot_label`),
  KEY `idx_booking_slots_booking_id` (`booking_id`),
  CONSTRAINT `fk_booking_slots_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `booking_payments` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT UNSIGNED NOT NULL,
  `venue_payment_method_id` BIGINT UNSIGNED NULL,
  `amount` DECIMAL(10,2) NOT NULL,
  `payment_method_label` VARCHAR(120) NOT NULL,
  `review_status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
  `payment_status` ENUM('unpaid', 'paid', 'refunded') NOT NULL DEFAULT 'unpaid',
  `reference_number` VARCHAR(120) NULL,
  `sender_account_name` VARCHAR(160) NULL,
  `receipt_file_name` VARCHAR(255) NULL,
  `receipt_image_url` LONGTEXT NULL,
  `receipt_uploaded_at` DATETIME NULL,
  `review_note` TEXT NULL,
  `approved_by_owner_id` BIGINT UNSIGNED NULL,
  `approved_at` DATETIME NULL,
  `rejected_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_booking_payments_booking_id` (`booking_id`),
  KEY `idx_booking_payments_method_id` (`venue_payment_method_id`),
  KEY `idx_booking_payments_owner_id` (`approved_by_owner_id`),
  KEY `idx_booking_payments_review_status` (`review_status`),
  CONSTRAINT `fk_booking_payments_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_booking_payments_method`
    FOREIGN KEY (`venue_payment_method_id`) REFERENCES `venue_payment_methods` (`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT `fk_booking_payments_owner`
    FOREIGN KEY (`approved_by_owner_id`) REFERENCES `owners` (`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `booking_rentals` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT UNSIGNED NOT NULL,
  `rental_item_id` BIGINT UNSIGNED NOT NULL,
  `item_name_snapshot` VARCHAR(120) NOT NULL,
  `category_snapshot` ENUM('paddle', 'ball', 'shoes', 'net', 'other') NOT NULL,
  `price_per_session_snapshot` DECIMAL(10,2) NOT NULL,
  `quantity` INT UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_booking_rentals_booking_id` (`booking_id`),
  KEY `idx_booking_rentals_item_id` (`rental_item_id`),
  CONSTRAINT `fk_booking_rentals_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_booking_rentals_item`
    FOREIGN KEY (`rental_item_id`) REFERENCES `rental_items` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `transactions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(32) NOT NULL,
  `booking_id` BIGINT UNSIGNED NOT NULL,
  `player_id` BIGINT UNSIGNED NOT NULL,
  `venue_id` BIGINT UNSIGNED NOT NULL,
  `court_id` BIGINT UNSIGNED NULL,
  `booking_type` ENUM('private', 'open_play', 'whole_gym') NOT NULL,
  `amount` DECIMAL(10,2) NOT NULL,
  `payment_method_label` VARCHAR(120) NOT NULL,
  `payment_status` ENUM('unpaid', 'paid', 'refunded') NOT NULL DEFAULT 'unpaid',
  `status` ENUM('pending', 'confirmed', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transactions_public_id` (`public_id`),
  UNIQUE KEY `uq_transactions_booking_id` (`booking_id`),
  KEY `idx_transactions_player_id` (`player_id`),
  KEY `idx_transactions_venue_id` (`venue_id`),
  KEY `idx_transactions_status` (`status`),
  CONSTRAINT `fk_transactions_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_transactions_player`
    FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_transactions_venue`
    FOREIGN KEY (`venue_id`) REFERENCES `venues` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_transactions_court`
    FOREIGN KEY (`court_id`) REFERENCES `courts` (`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pasalo_offers` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `booking_id` BIGINT UNSIGNED NOT NULL,
  `seller_player_id` BIGINT UNSIGNED NOT NULL,
  `asking_price` DECIMAL(10,2) NOT NULL,
  `note` TEXT NULL,
  `status` ENUM('open', 'pending', 'completed', 'cancelled') NOT NULL DEFAULT 'open',
  `offered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pasalo_offers_booking_id` (`booking_id`),
  KEY `idx_pasalo_seller_id` (`seller_player_id`),
  KEY `idx_pasalo_status` (`status`),
  CONSTRAINT `fk_pasalo_offers_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_pasalo_offers_seller`
    FOREIGN KEY (`seller_player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pasalo_claims` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pasalo_offer_id` BIGINT UNSIGNED NOT NULL,
  `claimant_player_id` BIGINT UNSIGNED NOT NULL,
  `reference_number` VARCHAR(120) NOT NULL,
  `sender_account_name` VARCHAR(160) NOT NULL,
  `receipt_file_name` VARCHAR(255) NOT NULL,
  `receipt_image_url` LONGTEXT NOT NULL,
  `review_note` TEXT NULL,
  `status` ENUM('pending', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
  `claimed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reviewed_by_owner_id` BIGINT UNSIGNED NULL,
  `reviewed_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pasalo_claims_offer_id` (`pasalo_offer_id`),
  KEY `idx_pasalo_claims_claimant_id` (`claimant_player_id`),
  KEY `idx_pasalo_claims_owner_id` (`reviewed_by_owner_id`),
  CONSTRAINT `fk_pasalo_claims_offer`
    FOREIGN KEY (`pasalo_offer_id`) REFERENCES `pasalo_offers` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_pasalo_claims_claimant`
    FOREIGN KEY (`claimant_player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_pasalo_claims_owner`
    FOREIGN KEY (`reviewed_by_owner_id`) REFERENCES `owners` (`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `owner_settlements` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `owner_id` BIGINT UNSIGNED NOT NULL,
  `period_start` DATE NOT NULL,
  `period_end` DATE NOT NULL,
  `gross_revenue` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `system_share` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `owner_total_profit` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `payment_status` ENUM('paid', 'unpaid') NOT NULL DEFAULT 'unpaid',
  `locked_at` DATETIME NULL,
  `paid_at` DATETIME NULL,
  `note` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_owner_settlements_owner_id` (`owner_id`),
  KEY `idx_owner_settlements_payment_status` (`payment_status`),
  CONSTRAINT `fk_owner_settlements_owner`
    FOREIGN KEY (`owner_id`) REFERENCES `owners` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `notifications` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `player_id` BIGINT UNSIGNED NOT NULL,
  `booking_id` BIGINT UNSIGNED NULL,
  `title` VARCHAR(160) NOT NULL,
  `message` TEXT NOT NULL,
  `is_read` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_notifications_player_id` (`player_id`),
  KEY `idx_notifications_booking_id` (`booking_id`),
  CONSTRAINT `fk_notifications_player`
    FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_notifications_booking`
    FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `players` (`id`, `public_id`, `full_name`, `email`, `password_hash`, `phone`, `location`, `status`, `joined_at`)
VALUES
  (1, 'USR-1001', 'Jordan Alcaraz', 'jordan.alcaraz@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(555) 210-4471', 'Tagum City', 'active', '2026-02-14 09:00:00'),
  (2, 'USR-1002', 'Mika Santos', 'mika.santos@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(555) 210-9821', 'Tagum City', 'active', '2026-03-02 11:30:00'),
  (3, 'USR-1003', 'Leo Fontanilla', 'leo.fontanilla@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', NULL, 'Tagum City', 'active', '2026-01-27 08:45:00'),
  (4, 'USR-1004', 'Ava Reyes', 'ava.reyes@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(555) 210-3390', 'Tagum City', 'active', '2026-04-11 14:15:00'),
  (5, 'USR-1005', 'Noah Villareal', 'noah.villareal@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', NULL, 'Tagum City', 'suspended', '2026-03-19 10:00:00'),
  (6, 'USR-1006', 'Sofia Cruz', 'sofia.cruz@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(555) 210-6602', 'Tagum City', 'active', '2026-02-28 16:20:00'),
  (7, 'USR-1007', 'Ethan Bautista', 'ethan.bautista@example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', NULL, 'Tagum City', 'active', '2026-05-06 13:10:00'),
  (8, 'USR-1008', 'Apex Systems Sports Club', 'events@apexsystems.example.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(555) 210-7788', 'Tagum City', 'active', '2026-06-12 13:40:00');

INSERT INTO `owners` (`id`, `public_id`, `full_name`, `email`, `password_hash`, `phone`, `business_name`, `status`, `system_payment_status`, `suspension_reason`, `created_at`)
VALUES
  (1, 'owner-1', 'Priya Nair', 'priya@northsidepb.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(084) 218-2231', 'Northside Pickleball Operations', 'active', 'unpaid', NULL, '2026-01-05 09:00:00'),
  (2, 'owner-2', 'Marcus Diaz', 'marcus@riversidesports.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(084) 218-4471', 'Riverside Sports Group', 'active', 'paid', NULL, '2026-01-05 09:30:00'),
  (3, 'owner-3', 'Mika Santos', 'mika@courtclubpb.com', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', '(084) 218-7782', 'Mankilam Court Club Holdings', 'suspended', 'unpaid', 'system_payment_due', '2026-01-05 10:00:00');

INSERT INTO `admins` (`id`, `public_id`, `full_name`, `email`, `password_hash`, `status`, `created_at`)
VALUES
  (1, 'ADM-1001', 'Platform Admin', 'admin@picklebuddy.local', 'pbkdf2_sha256$600000$c4t4II+Ym4tuQeCvvbnQ2w==$qJzg+6iw7y3Vsmsy867QzdmhLhGBv8t1QTQhTXKhsYM=', 'active', '2026-01-01 08:00:00');

INSERT INTO `venues` (`id`, `public_id`, `owner_id`, `name`, `address`, `phone`, `status`, `image_url`, `created_at`)
VALUES
  (1, 'northside', 1, 'Tagum Pickleball Hub', 'Pioneer Avenue, Magugpo Poblacion, Tagum City', '(084) 218-2231', 'active', 'https://picsum.photos/seed/tagum-hub/800/500', '2026-01-10 08:00:00'),
  (2, 'riverside', 2, 'Apokon Rally Courts', 'Apokon Road, Barangay Apokon, Tagum City', '(084) 218-4471', 'active', 'https://picsum.photos/seed/apokon-rally/800/500', '2026-01-10 08:10:00'),
  (3, 'central', 3, 'Mankilam Court Club', 'Mankilam Road, Barangay Mankilam, Tagum City', '(084) 218-7782', 'inactive', 'https://picsum.photos/seed/mankilam-club/800/500', '2026-01-10 08:20:00'),
  (4, 'visayan-village', 2, 'Visayan Village Pickleball Center', 'National Highway, Barangay Visayan Village, Tagum City', '(084) 218-3194', 'active', 'https://picsum.photos/seed/visayan-village-center/800/500', '2026-01-10 08:30:00'),
  (5, 'magugpo-east', 1, 'Magugpo East Sports Hall', 'Rizal Street, Magugpo East, Tagum City', '(084) 218-6405', 'active', 'https://picsum.photos/seed/magugpo-east-hall/800/500', '2026-01-10 08:40:00'),
  (6, 'madaum', 2, 'Madaum Paddle and Pickle', 'Madaum Road, Barangay Madaum, Tagum City', '(084) 218-9026', 'active', 'https://picsum.photos/seed/madaum-paddle-pickle/800/500', '2026-01-10 08:50:00'),
  (7, 'canocotan', 1, 'Canocotan Pickleball Arena', 'Canocotan Road, Barangay Canocotan, Tagum City', '(084) 218-5178', 'active', 'https://picsum.photos/seed/canocotan-arena/800/500', '2026-01-10 09:00:00');

INSERT INTO `venue_booking_settings` (`id`, `venue_id`, `whole_gym_enabled`, `whole_gym_price_per_hour`, `whole_gym_notes`, `created_at`)
VALUES
  (1, 1, 1, 34.00, 'Best for company sports days, school events, or private club sessions.', '2026-01-10 09:15:00'),
  (2, 2, 0, NULL, NULL, '2026-01-10 09:16:00'),
  (3, 3, 0, NULL, NULL, '2026-01-10 09:17:00'),
  (4, 4, 0, NULL, NULL, '2026-01-10 09:18:00'),
  (5, 5, 1, 40.00, 'Available for private training camps and barangay sports events.', '2026-01-10 09:19:00'),
  (6, 6, 0, NULL, NULL, '2026-01-10 09:20:00'),
  (7, 7, 0, NULL, NULL, '2026-01-10 09:21:00');

INSERT INTO `venue_available_slots` (`venue_id`, `slot_label`, `sort_order`)
VALUES
  (1, '8:00 AM', 1), (1, '10:00 AM', 2), (1, '1:00 PM', 3), (1, '4:00 PM', 4), (1, '7:00 PM', 5),
  (5, '8:00 AM', 1), (5, '11:00 AM', 2), (5, '2:00 PM', 3), (5, '5:00 PM', 4);

INSERT INTO `venue_payment_methods` (`id`, `venue_id`, `provider`, `display_name`, `account_name`, `account_number`, `instructions`, `qr_code_image_url`, `qr_code_file_name`, `is_active`, `created_at`)
VALUES
  (1, 1, 'GCash', 'Tagum Hub GCash', 'Priya Nair', '09171234567', 'Send the exact amount and upload a clear screenshot of the receipt.', 'data:image/svg+xml;placeholder,tagum-hub-gcash', 'tagum-hub-gcash-qr.png', 1, '2026-01-10 10:00:00'),
  (2, 1, 'Bank Transfer', 'Tagum Hub BPI', 'Priya Nair', 'BPI 1122 3344 5566', 'Use the booking date as your transfer note.', 'data:image/svg+xml;placeholder,tagum-hub-bpi', 'tagum-hub-bpi-qr.png', 1, '2026-01-10 10:02:00'),
  (3, 2, 'Bank Transfer', 'Apokon Rally BDO', 'Marcus Diaz', 'BDO 0199 0044 8832', 'Include the court date in your transfer note before uploading proof.', 'data:image/svg+xml;placeholder,apokon-rally-bank', 'apokon-rally-bank-qr.png', 1, '2026-01-10 10:05:00'),
  (4, 2, 'GCash', 'Apokon Rally GCash', 'Marcus Diaz', '09174445566', 'Upload the GCash screenshot after payment.', 'data:image/svg+xml;placeholder,apokon-rally-gcash', 'apokon-rally-gcash-qr.png', 1, '2026-01-10 10:07:00'),
  (5, 3, 'Maya', 'Mankilam Maya', 'Mika Santos', 'maya.me/mankilamclub', 'Upload the full Maya receipt with the transaction reference.', 'data:image/svg+xml;placeholder,mankilam-maya', 'mankilam-maya-qr.png', 1, '2026-01-10 10:10:00'),
  (6, 4, 'GCash', 'Visayan Village GCash', 'Marcus Diaz', '09179876543', 'For doubles bookings, pay the full amount in one transfer.', 'data:image/svg+xml;placeholder,visayan-village-gcash', 'visayan-village-gcash-qr.png', 1, '2026-01-10 10:15:00'),
  (7, 4, 'Other', 'Visayan Village MariBank', 'Marcus Diaz', 'MariBank 9988776655', 'Use your name as the transfer remark for MariBank payments.', 'data:image/svg+xml;placeholder,visayan-village-maribank', 'visayan-village-maribank-qr.png', 1, '2026-01-10 10:17:00'),
  (8, 5, 'Other', 'Magugpo East Counter QR', 'Magugpo East Sports Hall', 'Counter payment QR', 'Use this venue QR and keep the screenshot visible when uploading proof.', 'data:image/svg+xml;placeholder,magugpo-east-qr', 'magugpo-east-qr.png', 1, '2026-01-10 10:20:00'),
  (9, 6, 'GCash', 'Madaum GCash', 'Marcus Diaz', '09175550011', 'Upload the receipt right after payment to hold the slot for review.', 'data:image/svg+xml;placeholder,madaum-gcash', 'madaum-gcash-qr.png', 1, '2026-01-10 10:25:00'),
  (10, 6, 'Bank Transfer', 'Madaum MariBank', 'Marcus Diaz', 'MariBank 1234 5678 90', 'MariBank transfers are accepted for this venue as well.', 'data:image/svg+xml;placeholder,madaum-maribank', 'madaum-maribank-qr.png', 1, '2026-01-10 10:27:00'),
  (11, 7, 'Bank Transfer', 'Canocotan BPI', 'Priya Nair', 'BPI 2231 8850 9021', 'Send proof with the booking reference number after paying.', 'data:image/svg+xml;placeholder,canocotan-bank', 'canocotan-bank-qr.png', 1, '2026-01-10 10:30:00'),
  (12, 7, 'GCash', 'Canocotan GCash', 'Priya Nair', '09176667788', 'GCash is also supported for faster approval.', 'data:image/svg+xml;placeholder,canocotan-gcash', 'canocotan-gcash-qr.png', 1, '2026-01-10 10:32:00');

INSERT INTO `courts` (`id`, `public_id`, `venue_id`, `name`, `surface`, `capacity_label`, `price_per_hour`, `status`, `booking_mode`, `open_play_capacity`, `image_url`, `created_at`)
VALUES
  (1, 'northside-a', 1, 'Court A', 'Indoor cushioned', 'Singles or doubles', 12.00, 'available', 'private', NULL, 'https://picsum.photos/seed/tagum-hub-a/480/320', '2026-01-12 08:00:00'),
  (2, 'northside-b', 1, 'Court B', 'Indoor cushioned', 'Doubles preferred', 12.00, 'available', 'private', NULL, 'https://picsum.photos/seed/tagum-hub-b/480/320', '2026-01-12 08:05:00'),
  (3, 'northside-c', 1, 'Court C', 'Indoor premium', 'Training court', 16.00, 'maintenance', 'private', NULL, 'https://picsum.photos/seed/tagum-hub-c/480/320', '2026-01-12 08:10:00'),
  (4, 'riverside-main', 2, 'Main Court', 'Outdoor acrylic', 'Singles or doubles', 12.00, 'available', 'private', NULL, 'https://picsum.photos/seed/apokon-rally-main/480/320', '2026-01-12 08:15:00'),
  (5, 'central-1', 3, 'Court 1', 'Indoor hard court', 'Doubles preferred', 14.00, 'available', 'private', NULL, 'https://picsum.photos/seed/mankilam-club-1/480/320', '2026-01-12 08:20:00'),
  (6, 'central-2', 3, 'Court 2', 'Indoor hard court', 'Singles or doubles', 14.00, 'available', 'private', NULL, 'https://picsum.photos/seed/mankilam-club-2/480/320', '2026-01-12 08:25:00'),
  (7, 'visayan-village-1', 4, 'Court 1', 'Indoor cushioned', 'Singles or doubles', 13.00, 'available', 'private', NULL, 'https://picsum.photos/seed/visayan-village-1/480/320', '2026-01-12 08:30:00'),
  (8, 'visayan-village-2', 4, 'Court 2', 'Indoor cushioned', 'Doubles preferred', 13.00, 'available', 'open_play', 10, 'https://picsum.photos/seed/visayan-village-2/480/320', '2026-01-12 08:35:00'),
  (9, 'magugpo-east-1', 5, 'Hall Court', 'Indoor hard court', 'Singles or doubles', 15.00, 'available', 'private', NULL, 'https://picsum.photos/seed/magugpo-east-1/480/320', '2026-01-12 08:40:00'),
  (10, 'magugpo-east-2', 5, 'Training Court', 'Indoor hard court', 'Training court', 15.00, 'maintenance', 'private', NULL, 'https://picsum.photos/seed/magugpo-east-2/480/320', '2026-01-12 08:45:00'),
  (11, 'madaum-1', 6, 'Court A', 'Outdoor acrylic', 'Singles or doubles', 11.00, 'available', 'open_play', 10, 'https://picsum.photos/seed/madaum-1/480/320', '2026-01-12 08:50:00'),
  (12, 'canocotan-1', 7, 'Arena Court 1', 'Indoor premium', 'Doubles preferred', 16.00, 'available', 'private', NULL, 'https://picsum.photos/seed/canocotan-1/480/320', '2026-01-12 08:55:00'),
  (13, 'canocotan-2', 7, 'Arena Court 2', 'Indoor premium', 'Singles or doubles', 16.00, 'available', 'open_play', 10, 'https://picsum.photos/seed/canocotan-2/480/320', '2026-01-12 09:00:00');

INSERT INTO `court_available_slots` (`court_id`, `slot_label`, `sort_order`)
VALUES
  (1, '8:00 AM', 1), (1, '9:30 AM', 2), (1, '1:00 PM', 3), (1, '5:30 PM', 4),
  (2, '10:00 AM', 1), (2, '2:30 PM', 2), (2, '4:00 PM', 3), (2, '7:00 PM', 4),
  (3, '11:30 AM', 1), (3, '3:00 PM', 2), (3, '6:30 PM', 3),
  (4, '7:30 AM', 1), (4, '12:00 PM', 2), (4, '3:30 PM', 3), (4, '6:00 PM', 4),
  (5, '8:30 AM', 1), (5, '11:00 AM', 2), (5, '2:00 PM', 3),
  (6, '9:00 AM', 1), (6, '1:30 PM', 2), (6, '5:00 PM', 3), (6, '8:00 PM', 4),
  (7, '6:30 AM', 1), (7, '9:00 AM', 2), (7, '4:30 PM', 3), (7, '7:30 PM', 4),
  (8, '8:00 AM', 1), (8, '10:30 AM', 2), (8, '3:00 PM', 3), (8, '6:00 PM', 4),
  (9, '7:00 AM', 1), (9, '11:00 AM', 2), (9, '2:30 PM', 3), (9, '5:00 PM', 4),
  (10, '1:00 PM', 1), (10, '4:00 PM', 2),
  (11, '6:00 AM', 1), (11, '8:30 AM', 2), (11, '3:30 PM', 3), (11, '6:30 PM', 4),
  (12, '7:30 AM', 1), (12, '10:00 AM', 2), (12, '1:30 PM', 3), (12, '6:00 PM', 4),
  (13, '9:00 AM', 1), (13, '12:30 PM', 2), (13, '4:30 PM', 3), (13, '8:00 PM', 4),
  (13, '5:00 PM', 5);

INSERT INTO `rental_items` (`id`, `public_id`, `venue_id`, `name`, `category`, `price_per_session`, `quantity_available`, `status`, `description`, `created_at`)
VALUES
  (1, 'northside-paddle-std', 1, 'Recreational paddle', 'paddle', 3.00, 12, 'available', 'Composite paddle with cushioned grip. Good for first-timers.', '2026-01-12 10:00:00'),
  (2, 'northside-paddle-pro', 1, 'Carbon fiber paddle', 'paddle', 6.00, 4, 'available', 'Tournament-grade paddle for players who want more control.', '2026-01-12 10:02:00'),
  (3, 'northside-balls', 1, 'Outdoor ball set (3 pcs)', 'ball', 2.00, 20, 'available', NULL, '2026-01-12 10:04:00'),
  (4, 'northside-shoes', 1, 'Court shoes', 'shoes', 4.00, 8, 'available', 'Sizes 6-11 available. Ask the front desk on arrival.', '2026-01-12 10:06:00'),
  (5, 'visayan-village-paddle', 4, 'Community paddle', 'paddle', 3.00, 10, 'available', 'Basic paddle for open play sessions.', '2026-01-12 10:08:00'),
  (6, 'canocotan-ball-bucket', 7, 'Ball bucket', 'ball', 5.00, 6, 'available', 'Training balls for drills and club sessions.', '2026-01-12 10:10:00');

INSERT INTO `bookings` (`id`, `public_id`, `player_id`, `original_player_id`, `venue_id`, `court_id`, `booking_type`, `booking_date`, `participant_count`, `status`, `payment_status`, `booked_by_name_snapshot`, `booked_by_email_snapshot`, `owner_name_snapshot`, `owner_email_snapshot`, `base_amount`, `rental_amount`, `total_amount`, `created_at`)
VALUES
  (1, 'PB-1042', 1, 1, 1, 2, 'private', '2026-08-24', 1, 'confirmed', 'paid', 'Jordan Alcaraz', 'jordan.alcaraz@example.com', 'Priya Nair', 'priya@northsidepb.com', 24.00, 0.00, 24.00, '2026-08-19 09:14:00'),
  (2, 'PB-1043', 2, 2, 3, 6, 'private', '2026-08-26', 1, 'pending', 'paid', 'Mika Santos', 'mika.santos@example.com', 'Mika Santos', 'mika@courtclubpb.com', 28.00, 4.00, 32.00, '2026-08-20 14:02:00'),
  (3, 'PB-1019', 3, 3, 2, 4, 'private', '2026-08-14', 1, 'completed', 'paid', 'Leo Fontanilla', 'leo.fontanilla@example.com', 'Marcus Diaz', 'marcus@riversidesports.com', 12.00, 0.00, 12.00, '2026-08-01 08:30:00'),
  (4, 'PB-1058', 4, 4, 4, 7, 'private', '2026-08-24', 1, 'confirmed', 'paid', 'Ava Reyes', 'ava.reyes@example.com', 'Marcus Diaz', 'marcus@riversidesports.com', 26.00, 0.00, 26.00, '2026-08-20 10:15:00'),
  (5, 'PB-1062', 7, 7, 7, 13, 'private', '2026-08-25', 1, 'confirmed', 'paid', 'Ethan Bautista', 'ethan.bautista@example.com', 'Priya Nair', 'priya@northsidepb.com', 16.00, 0.00, 16.00, '2026-08-20 14:30:00'),
  (6, 'PB-1066', 8, 8, 1, NULL, 'whole_gym', '2026-08-27', 24, 'pending', 'paid', 'Apex Systems Sports Club', 'events@apexsystems.example.com', 'Priya Nair', 'priya@northsidepb.com', 68.00, 0.00, 68.00, '2026-08-21 17:18:00'),
  (7, 'PB-1063', 2, 2, 4, 8, 'open_play', '2026-08-22', 5, 'confirmed', 'paid', 'Mika Santos', 'mika.santos@example.com', 'Marcus Diaz', 'marcus@riversidesports.com', 32.50, 0.00, 32.50, '2026-08-21 09:20:00'),
  (8, 'PB-1064', 4, 4, 6, 11, 'open_play', '2026-08-23', 3, 'confirmed', 'paid', 'Ava Reyes', 'ava.reyes@example.com', 'Marcus Diaz', 'marcus@riversidesports.com', 16.50, 0.00, 16.50, '2026-08-21 10:10:00'),
  (9, 'PB-1065', 7, 7, 7, 13, 'open_play', '2026-08-24', 7, 'pending', 'paid', 'Ethan Bautista', 'ethan.bautista@example.com', 'Priya Nair', 'priya@northsidepb.com', 73.50, 0.00, 73.50, '2026-08-21 15:42:00'),
  (10, 'PB-1051', 4, 4, 1, 1, 'private', '2026-08-28', 1, 'pending', 'unpaid', 'Ava Reyes', 'ava.reyes@example.com', 'Priya Nair', 'priya@northsidepb.com', 12.00, 0.00, 12.00, '2026-08-21 11:45:00'),
  (11, 'PB-1038', 5, 5, 3, 5, 'private', '2026-07-09', 1, 'cancelled', 'refunded', 'Noah Villareal', 'noah.villareal@example.com', 'Mika Santos', 'mika@courtclubpb.com', 24.00, 0.00, 24.00, '2026-07-04 16:20:00'),
  (12, 'PB-1027', 6, 6, 2, 4, 'private', '2026-06-29', 1, 'completed', 'paid', 'Sofia Cruz', 'sofia.cruz@example.com', 'Marcus Diaz', 'marcus@riversidesports.com', 12.00, 0.00, 12.00, '2026-06-24 10:10:00');

INSERT INTO `booking_slots` (`booking_id`, `slot_label`, `sort_order`)
VALUES
  (1, '10:00 AM', 1), (1, '2:30 PM', 2),
  (2, '5:00 PM', 1), (2, '8:00 PM', 2),
  (3, '7:30 AM', 1),
  (4, '4:30 PM', 1), (4, '7:30 PM', 2),
  (5, '8:00 PM', 1),
  (6, '4:00 PM', 1), (6, '7:00 PM', 2),
  (7, '6:00 PM', 1),
  (8, '5:30 PM', 1),
  (9, '5:00 PM', 1),
  (10, '9:30 AM', 1),
  (11, '11:00 AM', 1), (11, '2:00 PM', 2),
  (12, '3:30 PM', 1);

INSERT INTO `booking_payments` (`id`, `booking_id`, `venue_payment_method_id`, `amount`, `payment_method_label`, `review_status`, `payment_status`, `reference_number`, `sender_account_name`, `receipt_file_name`, `receipt_image_url`, `receipt_uploaded_at`, `review_note`, `approved_by_owner_id`, `approved_at`, `rejected_at`, `created_at`)
VALUES
  (1, 1, 1, 24.00, 'GCash QR payment', 'approved', 'paid', 'GCASH-20260819-1042', 'Jordan Alcaraz', 'tagum-hub-booking-1042.png', 'data:image/svg+xml;placeholder,booking-1042-receipt', '2026-08-19 09:10:00', NULL, 1, '2026-08-19 09:16:00', NULL, '2026-08-19 09:10:00'),
  (2, 2, 5, 32.00, 'Maya QR payment', 'pending', 'paid', 'MAYA-20260820-1043', 'Mika Santos', 'mankilam-prototype-receipt.png', 'data:image/svg+xml;placeholder,booking-1043-receipt', '2026-08-20 22:18:00', NULL, NULL, NULL, NULL, '2026-08-20 22:18:00'),
  (3, 3, 3, 12.00, 'Bank Transfer QR payment', 'approved', 'paid', 'BANK-20260801-1019', 'Leo Fontanilla', 'apokon-completed-receipt.png', 'data:image/svg+xml;placeholder,booking-1019-receipt', '2026-08-01 08:25:00', NULL, 2, '2026-08-01 08:35:00', NULL, '2026-08-01 08:25:00'),
  (4, 4, 6, 26.00, 'GCash QR payment', 'approved', 'paid', 'GCASH-20260820-1058', 'Ava Reyes', 'visayan-village-booking-1058.png', 'data:image/svg+xml;placeholder,booking-1058-receipt', '2026-08-20 10:10:00', NULL, 2, '2026-08-20 10:20:00', NULL, '2026-08-20 10:10:00'),
  (5, 5, 11, 16.00, 'Bank Transfer QR payment', 'approved', 'paid', 'BANK-20260820-1062', 'Ethan Bautista', 'canocotan-booking-1062.png', 'data:image/svg+xml;placeholder,booking-1062-receipt', '2026-08-20 14:20:00', NULL, 1, '2026-08-20 14:35:00', NULL, '2026-08-20 14:20:00'),
  (6, 6, 2, 68.00, 'Bank Transfer QR payment', 'pending', 'paid', 'BANK-20260821-1066', 'Apex Systems Sports Club', 'whole-gym-booking-1066.png', 'data:image/svg+xml;placeholder,booking-1066-receipt', '2026-08-21 17:18:00', 'Awaiting owner review for full venue block.', NULL, NULL, NULL, '2026-08-21 17:18:00'),
  (7, 7, 7, 32.50, 'MariBank QR payment', 'approved', 'paid', 'MBANK-20260821-1063', 'Mika Santos', 'open-play-1063.png', 'data:image/svg+xml;placeholder,booking-1063-receipt', '2026-08-21 09:15:00', NULL, 2, '2026-08-21 09:25:00', NULL, '2026-08-21 09:15:00'),
  (8, 8, 9, 16.50, 'GCash QR payment', 'approved', 'paid', 'GCASH-20260821-1064', 'Ava Reyes', 'open-play-1064.png', 'data:image/svg+xml;placeholder,booking-1064-receipt', '2026-08-21 10:05:00', NULL, 2, '2026-08-21 10:15:00', NULL, '2026-08-21 10:05:00'),
  (9, 9, 12, 73.50, 'GCash QR payment', 'pending', 'paid', 'GCASH-20260821-1065', 'Ethan Bautista', 'open-play-1065.png', 'data:image/svg+xml;placeholder,booking-1065-receipt', '2026-08-21 15:42:00', NULL, NULL, NULL, NULL, '2026-08-21 15:42:00'),
  (10, 10, 1, 12.00, 'GCash QR payment', 'pending', 'unpaid', 'GCASH-20260821-1051', 'Ava Reyes', 'tagum-hub-prototype-receipt.png', 'data:image/svg+xml;placeholder,booking-1051-receipt', '2026-08-21 19:45:00', NULL, NULL, NULL, NULL, '2026-08-21 19:45:00'),
  (11, 11, 5, 24.00, 'Maya QR payment', 'approved', 'refunded', 'MAYA-20260704-1038', 'Noah Villareal', 'mankilam-refund-receipt.png', 'data:image/svg+xml;placeholder,booking-1038-receipt', '2026-07-04 16:15:00', 'Refund issued after cancellation.', 3, '2026-07-04 16:30:00', NULL, '2026-07-04 16:15:00'),
  (12, 12, 3, 12.00, 'Bank Transfer QR payment', 'approved', 'paid', 'BANK-20260624-1027', 'Sofia Cruz', 'apokon-completed-receipt-1027.png', 'data:image/svg+xml;placeholder,booking-1027-receipt', '2026-06-24 10:05:00', NULL, 2, '2026-06-24 10:12:00', NULL, '2026-06-24 10:05:00');

INSERT INTO `booking_rentals` (`booking_id`, `rental_item_id`, `item_name_snapshot`, `category_snapshot`, `price_per_session_snapshot`, `quantity`)
VALUES
  (2, 4, 'Court shoes', 'shoes', 4.00, 1);

INSERT INTO `transactions` (`id`, `public_id`, `booking_id`, `player_id`, `venue_id`, `court_id`, `booking_type`, `amount`, `payment_method_label`, `payment_status`, `status`, `created_at`)
VALUES
  (1, 'PB-1042', 1, 1, 1, 2, 'private', 24.00, 'GCash QR payment', 'paid', 'confirmed', '2026-08-19 09:14:00'),
  (2, 'PB-1043', 2, 2, 3, 6, 'private', 32.00, 'Maya QR payment', 'paid', 'pending', '2026-08-20 14:02:00'),
  (3, 'PB-1019', 3, 3, 2, 4, 'private', 12.00, 'Bank Transfer QR payment', 'paid', 'completed', '2026-08-01 08:30:00'),
  (4, 'PB-1058', 4, 4, 4, 7, 'private', 26.00, 'GCash QR payment', 'paid', 'confirmed', '2026-08-20 10:15:00'),
  (5, 'PB-1062', 5, 7, 7, 13, 'private', 16.00, 'Bank Transfer QR payment', 'paid', 'confirmed', '2026-08-20 14:30:00'),
  (6, 'PB-1066', 6, 8, 1, NULL, 'whole_gym', 68.00, 'Bank Transfer QR payment', 'paid', 'pending', '2026-08-21 17:18:00'),
  (7, 'PB-1063', 7, 2, 4, 8, 'open_play', 32.50, 'MariBank QR payment', 'paid', 'confirmed', '2026-08-21 09:20:00'),
  (8, 'PB-1064', 8, 4, 6, 11, 'open_play', 16.50, 'GCash QR payment', 'paid', 'confirmed', '2026-08-21 10:10:00'),
  (9, 'PB-1065', 9, 7, 7, 13, 'open_play', 73.50, 'GCash QR payment', 'paid', 'pending', '2026-08-21 15:42:00'),
  (10, 'PB-1051', 10, 4, 1, 1, 'private', 12.00, 'GCash QR payment', 'unpaid', 'pending', '2026-08-21 11:45:00'),
  (11, 'PB-1038', 11, 5, 3, 5, 'private', 24.00, 'Maya QR payment', 'refunded', 'cancelled', '2026-07-04 16:20:00'),
  (12, 'PB-1027', 12, 6, 2, 4, 'private', 12.00, 'Bank Transfer QR payment', 'paid', 'completed', '2026-06-24 10:10:00');

INSERT INTO `pasalo_offers` (`id`, `booking_id`, `seller_player_id`, `asking_price`, `note`, `status`, `offered_at`)
VALUES
  (1, 4, 4, 24.00, 'Selling both slots together because our doubles group had to cancel.', 'open', '2026-08-20 10:15:00'),
  (2, 5, 7, 16.00, 'Late evening slot available. Please send GCash proof after claiming.', 'pending', '2026-08-20 14:30:00');

INSERT INTO `pasalo_claims` (`id`, `pasalo_offer_id`, `claimant_player_id`, `reference_number`, `sender_account_name`, `receipt_file_name`, `receipt_image_url`, `review_note`, `status`, `claimed_at`, `reviewed_by_owner_id`, `reviewed_at`)
VALUES
  (1, 2, 1, 'GCASH-PASALO-20260821-2001', 'Jordan Alcaraz', 'pasalo-claim-2001.png', 'data:image/svg+xml;placeholder,pasalo-claim-2001', 'Waiting for owner validation before transfer.', 'pending', '2026-08-21 16:10:00', NULL, NULL);

INSERT INTO `owner_settlements` (`id`, `owner_id`, `period_start`, `period_end`, `gross_revenue`, `system_share`, `owner_total_profit`, `payment_status`, `locked_at`, `paid_at`, `note`, `created_at`)
VALUES
  (1, 1, '2026-08-01', '2026-08-31', 193.50, 23.22, 170.28, 'unpaid', NULL, NULL, 'Current month settlement pending platform remittance.', '2026-08-24 08:00:00'),
  (2, 2, '2026-08-01', '2026-08-31', 71.00, 8.52, 62.48, 'paid', NULL, '2026-08-20 18:00:00', NULL, '2026-08-24 08:05:00'),
  (3, 3, '2026-08-01', '2026-08-31', 32.00, 3.84, 28.16, 'unpaid', '2026-08-22 09:00:00', NULL, 'Owner access locked until settlement is paid.', '2026-08-24 08:10:00');

INSERT INTO `notifications` (`id`, `player_id`, `booking_id`, `title`, `message`, `is_read`, `created_at`)
VALUES
  (1, 2, 2, 'Payment submitted', 'Your booking PB-1043 is waiting for owner approval after receipt upload.', 0, '2026-08-20 22:20:00'),
  (2, 4, 10, 'Booking pending approval', 'Your Tagum Pickleball Hub booking is pending manual owner verification.', 0, '2026-08-21 19:50:00'),
  (3, 1, 1, 'Booking confirmed', 'Your court booking at Tagum Pickleball Hub has been confirmed.', 1, '2026-08-19 09:18:00'),
  (4, 7, 9, 'Open Play pending review', 'Your Open Play booking is waiting for payment verification.', 0, '2026-08-21 15:50:00'),
  (5, 1, 5, 'Pasalo claim submitted', 'Your Pasalo claim is waiting for owner review before the booking can be transferred.', 0, '2026-08-21 16:12:00');

SET FOREIGN_KEY_CHECKS = 1;
