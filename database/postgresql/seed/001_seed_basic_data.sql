INSERT INTO asset_categories (name)
VALUES ('Gold')
ON CONFLICT (name) DO NOTHING;
