-- ============================================================
-- Row-Level Security policies for OrchestraGrant
-- Apply after running Alembic migrations.
--
-- All org-scoped tables enforce: sessions must set
--   SET LOCAL app.org_id = '<uuid>';
-- before any SELECT/INSERT/UPDATE/DELETE.
--
-- The API sets this at the start of every request via
-- SQLAlchemy event hooks (see database.py or middleware).
-- ============================================================

-- ── Helper function ───────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION current_org_id() RETURNS uuid AS $$
  SELECT current_setting('app.org_id', true)::uuid;
$$ LANGUAGE sql STABLE SECURITY DEFINER;


-- ── Organizations ─────────────────────────────────────────────────────────────

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations FORCE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON public.organizations
  USING (id = current_org_id());


-- ── Org Profiles ─────────────────────────────────────────────────────────────

ALTER TABLE public.org_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.org_profiles FORCE ROW LEVEL SECURITY;

CREATE POLICY org_profile_isolation ON public.org_profiles
  USING (org_id = current_org_id());


-- ── Board Members ─────────────────────────────────────────────────────────────

ALTER TABLE public.board_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.board_members FORCE ROW LEVEL SECURITY;

CREATE POLICY board_member_isolation ON public.board_members
  USING (org_id = current_org_id());


-- ── Auth Users ────────────────────────────────────────────────────────────────

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.users FORCE ROW LEVEL SECURITY;

-- Users can only see members of their own org
CREATE POLICY user_org_isolation ON auth.users
  USING (org_id = current_org_id());


-- ── Grant Watchlist ───────────────────────────────────────────────────────────

ALTER TABLE grants.grant_watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE grants.grant_watchlist FORCE ROW LEVEL SECURITY;

CREATE POLICY watchlist_isolation ON grants.grant_watchlist
  USING (org_id = current_org_id());


-- ── Applications ─────────────────────────────────────────────────────────────

ALTER TABLE applications.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications.applications FORCE ROW LEVEL SECURITY;

CREATE POLICY application_isolation ON applications.applications
  USING (org_id = current_org_id());


-- ── Application Sections ─────────────────────────────────────────────────────

ALTER TABLE applications.application_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications.application_sections FORCE ROW LEVEL SECURITY;

CREATE POLICY section_isolation ON applications.application_sections
  USING (
    application_id IN (
      SELECT id FROM applications.applications WHERE org_id = current_org_id()
    )
  );


-- ── Org Documents ─────────────────────────────────────────────────────────────

ALTER TABLE public.org_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.org_documents FORCE ROW LEVEL SECURITY;

CREATE POLICY document_isolation ON public.org_documents
  USING (org_id = current_org_id());


-- ── Deadlines ─────────────────────────────────────────────────────────────────

ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deadlines FORCE ROW LEVEL SECURITY;

CREATE POLICY deadline_isolation ON public.deadlines
  USING (org_id = current_org_id());


-- ── Awards ────────────────────────────────────────────────────────────────────

ALTER TABLE awards.awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE awards.awards FORCE ROW LEVEL SECURITY;

CREATE POLICY award_isolation ON awards.awards
  USING (org_id = current_org_id());


-- ── Narrative Atoms ───────────────────────────────────────────────────────────

ALTER TABLE ai.narrative_atoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.narrative_atoms FORCE ROW LEVEL SECURITY;

CREATE POLICY atom_isolation ON ai.narrative_atoms
  USING (org_id = current_org_id());


-- ── Grants (public read — no org isolation) ───────────────────────────────────
-- grants.grants are shared across all orgs; no RLS on public grant data.
-- funders likewise are public.


-- ── Discovery Scrape Runs (admin-only, no org scoping needed) ────────────────
-- discovery.scrape_runs are system-level; access controlled by app-layer auth.


-- ── API role: bypass RLS for system operations ───────────────────────────────
-- The application DB role should be granted BYPASSRLS only for migration
-- and background tasks. Regular request connections must always set app.org_id.
--
-- In practice, use a separate superuser role for migrations and a restricted
-- role (no BYPASSRLS) for the FastAPI connection pool.
