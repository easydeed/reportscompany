-- Fix reports stuck in 'processing' status
-- This can happen if the worker task fails after sending SMS but before updating status

UPDATE consumer_reports 
SET 
    status = 'sent',
    property_data = COALESCE(property_data, jsonb_build_object(
        'address', property_address,
        'city', property_city,
        'state', property_state,
        'zip', property_zip
    )),
    value_estimate = COALESCE(value_estimate, '{"low": 0, "mid": 0, "high": 0, "confidence": "pending"}'::jsonb),
    market_stats = COALESCE(market_stats, '{}'::jsonb),
    comparables = COALESCE(comparables, '[]'::jsonb)
WHERE status = 'processing'
AND created_at < NOW() - INTERVAL '5 minutes';

-- Also fix any stuck at 'pending' for more than 10 minutes
UPDATE consumer_reports 
SET status = 'failed', 
    error = 'Timed out waiting for processing'
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL '10 minutes';

