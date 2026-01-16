-- Add job_title and website fields to users table
-- These are used in the new unified Settings > Profile page

ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS website VARCHAR(500);

COMMENT ON COLUMN users.job_title IS 'User job title (e.g., Real Estate Agent, Broker)';
COMMENT ON COLUMN users.website IS 'User personal or business website URL';

-- Create index for looking up users by job_title (useful for filtering/searching)
CREATE INDEX IF NOT EXISTS idx_users_job_title ON users(job_title) WHERE job_title IS NOT NULL;

