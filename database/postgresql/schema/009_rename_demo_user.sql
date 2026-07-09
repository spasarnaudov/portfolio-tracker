UPDATE users
SET username = 'demo'
WHERE LOWER(username) = LOWER('demo')
    AND username <> 'demo';
