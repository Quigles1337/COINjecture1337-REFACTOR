
-- COINjecture CID Encoding Migration Script
-- Converts all CIDs from base58 to base58btc encoding

-- Step 1: Add new column for base58btc CIDs
ALTER TABLE blocks ADD COLUMN cid_base58btc VARCHAR(46);

-- Step 2: Update all existing CIDs
-- This would need to be run with a Python script that converts each CID
UPDATE blocks SET cid_base58btc = convert_to_base58btc(cid);

-- Step 3: Drop old column and rename new one
ALTER TABLE blocks DROP COLUMN cid;
ALTER TABLE blocks RENAME COLUMN cid_base58btc TO cid;

-- Step 4: Add index for performance
CREATE INDEX idx_blocks_cid ON blocks(cid);

-- Step 5: Update any other tables that reference CIDs
-- (This would depend on your database schema)
