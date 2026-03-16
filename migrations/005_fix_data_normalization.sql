-- Migration 005: Fix data normalization issues
-- 1. Fix 2-digit birth years (add 1900)
-- 2. Normalize has_kids / has_kids_w to consistent 'yes'/'no'
-- 3. Normalize chronic boolean values; migrate free-text disease names to other_diseases

BEGIN TRANSACTION;

-- Fix 2-digit birth years (64 → 1964, 72 → 1972, 76 → 1976)
UPDATE records
SET birth_year = birth_year + 1900
WHERE birth_year BETWEEN 1 AND 99;

-- Normalize has_kids: Arabic 'نعم'→'yes', Arabic 'لا'→'no', empty→NULL
UPDATE records SET has_kids = 'yes' WHERE has_kids = 'نعم';
UPDATE records SET has_kids = 'no'  WHERE has_kids = 'لا';
UPDATE records SET has_kids = NULL  WHERE has_kids = '';

-- Normalize has_kids_w: same pattern
UPDATE records SET has_kids_w = 'yes' WHERE has_kids_w = 'نعم';
UPDATE records SET has_kids_w = 'no'  WHERE has_kids_w = 'لا';
UPDATE records SET has_kids_w = NULL  WHERE has_kids_w = '';

-- Normalize chronic:
-- Step 1: where chronic contains free-text disease names (not a flag value),
--         move the value to other_diseases if other_diseases is empty
UPDATE records
SET other_diseases = chronic
WHERE chronic IS NOT NULL
  AND chronic NOT IN ('yes', 'no', 'نعم', 'لا', '')
  AND (other_diseases IS NULL OR other_diseases = '');

-- Step 2: mark those records as chronic = 'yes' (they have a listed condition)
UPDATE records
SET chronic = 'yes'
WHERE chronic IS NOT NULL
  AND chronic NOT IN ('yes', 'no', 'نعم', 'لا', '');

-- Step 3: normalize Arabic values to English
UPDATE records SET chronic = 'yes' WHERE chronic = 'نعم';
UPDATE records SET chronic = 'no'  WHERE chronic = 'لا';

-- Step 4: empty string → NULL
UPDATE records SET chronic = NULL WHERE chronic = '';

COMMIT;
