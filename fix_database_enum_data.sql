-- Fix PrintJob enum data mismatch
-- Run this SQL directly on your database to fix existing lowercase enum values

-- Step 1: Convert status column to text to allow updates
ALTER TABLE printjob ALTER COLUMN status TYPE text;

-- Step 2: Update all existing values to uppercase
UPDATE printjob 
SET status = CASE 
    WHEN LOWER(status) = 'queued' THEN 'QUEUED'
    WHEN LOWER(status) = 'assigned' THEN 'ASSIGNED'
    WHEN LOWER(status) = 'printing' THEN 'PRINTING'
    WHEN LOWER(status) = 'completed' THEN 'COMPLETED'
    WHEN LOWER(status) = 'failed' THEN 'FAILED'
    WHEN LOWER(status) = 'cancelled' THEN 'CANCELLED'
    ELSE 'QUEUED'
END
WHERE status IS NOT NULL;

-- Step 3: Drop and recreate the enum type
DROP TYPE IF EXISTS printjobstatus;
CREATE TYPE printjobstatus AS ENUM ('QUEUED', 'ASSIGNED', 'PRINTING', 'COMPLETED', 'FAILED', 'CANCELLED');

-- Step 4: Convert column back to enum type
ALTER TABLE printjob ALTER COLUMN status TYPE printjobstatus USING status::printjobstatus;

-- Verify the fix
SELECT status, COUNT(*) FROM printjob GROUP BY status; 