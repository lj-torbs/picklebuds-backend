USE `picklebuddy`;

UPDATE `notifications` AS `n`
JOIN `bookings` AS `b` ON `b`.`id` = `n`.`booking_id`
SET `n`.`action_url` = CONCAT('/owner/transactions?focus=', `b`.`public_id`)
WHERE `n`.`recipient_type` = 'owner'
  AND `n`.`action_url` = '/owner/transactions';
