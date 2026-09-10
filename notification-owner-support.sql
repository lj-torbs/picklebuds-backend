USE `picklebuddy`;

ALTER TABLE `notifications`
  DROP FOREIGN KEY `fk_notifications_player`;

ALTER TABLE `notifications`
  MODIFY `player_id` BIGINT UNSIGNED NULL,
  ADD COLUMN `recipient_type` ENUM('player', 'owner') NOT NULL DEFAULT 'player' AFTER `id`,
  ADD COLUMN `owner_id` BIGINT UNSIGNED NULL AFTER `player_id`,
  ADD COLUMN `action_url` VARCHAR(255) NULL AFTER `message`;

UPDATE `notifications`
SET `recipient_type` = 'player',
    `action_url` = COALESCE(`action_url`, '/my-bookings')
WHERE `recipient_type` = 'player';

ALTER TABLE `notifications`
  ADD KEY `idx_notifications_recipient_type` (`recipient_type`),
  ADD KEY `idx_notifications_owner_id` (`owner_id`),
  ADD CONSTRAINT `fk_notifications_player`
    FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  ADD CONSTRAINT `fk_notifications_owner`
    FOREIGN KEY (`owner_id`) REFERENCES `owners` (`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE;
