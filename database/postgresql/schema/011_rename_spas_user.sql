UPDATE users
SET username = 'spas'
WHERE LOWER(username) = LOWER('spas')
    AND username <> 'spas';
