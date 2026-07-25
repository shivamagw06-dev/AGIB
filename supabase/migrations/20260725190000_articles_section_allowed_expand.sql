-- Expand articles.section check constraint for AGI Letters + Intelligence CMS.
-- Fixes: new row for relation "articles" violates check constraint "articles_section_allowed"

DO $$
DECLARE
  cname text;
BEGIN
  FOR cname IN
    SELECT con.conname
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
    WHERE nsp.nspname = 'public'
      AND rel.relname = 'articles'
      AND con.contype = 'c'
      AND (
        con.conname ILIKE '%section%'
        OR pg_get_constraintdef(con.oid) ILIKE '%section%'
      )
  LOOP
    EXECUTE format('ALTER TABLE public.articles DROP CONSTRAINT IF EXISTS %I', cname);
  END LOOP;
END $$;

ALTER TABLE public.articles
  DROP CONSTRAINT IF EXISTS articles_section_allowed;

ALTER TABLE public.articles
  ADD CONSTRAINT articles_section_allowed
  CHECK (
    section IS NULL
    OR section IN (
      -- Morning Brief
      'Pre-Market Update',
      'Morning Market Update',
      'Today''s Market Brief',
      'Market Opening Outlook',
      -- Markets / midday
      '12 PM Market Update',
      'Market News',
      'Research Reports',
      'Stock Analysis',
      'Company Updates',
      'IPOs',
      -- Evening Brief
      'Market Close Update',
      'Day Close Update',
      'Market Close Summary',
      -- Macro
      'Macro Intelligence',
      'Economy',
      'Global Markets',
      'Commodities',
      -- Private intelligence / general
      'Intelligence',
      'AGI Intelligence',
      'Research',
      'Opinions & Editorials',
      'Deal Tracker'
    )
  );

-- Ensure categories exist for the new letter names.
INSERT INTO public.article_categories (name, slug, description, sort_order)
VALUES
  ('Pre-Market Update', 'pre-market-update', 'AGI Morning Brief — everything before the opening bell', 1),
  ('Market Close Update', 'market-close-update', 'AGI Evening Brief — what moved markets today and why', 5),
  ('Macro Intelligence', 'macro-intelligence', 'AGI Macro — policy, inflation, rates, FX, geopolitics', 7),
  ('Intelligence', 'intelligence', 'Private AGI Intelligence notes (not public website)', 20)
ON CONFLICT (slug) DO NOTHING;
