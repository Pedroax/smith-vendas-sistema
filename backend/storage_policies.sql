-- ============================================
-- POLÍTICAS RLS (Row Level Security)
-- Supabase Storage - Smith 2.0
-- ============================================
-- Execute este SQL no Supabase Dashboard > SQL Editor
-- Localização: https://supabase.com/dashboard/project/[seu-projeto]/sql
-- ============================================

-- Dropar políticas existentes (se houver)
DROP POLICY IF EXISTS "Service role full access - deliveries" ON storage.objects;
DROP POLICY IF EXISTS "Service role full access - approvals" ON storage.objects;
DROP POLICY IF EXISTS "Service role full access - payments" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload - deliveries" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload - payments" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can read - deliveries" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can read - approvals" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can read - payments" ON storage.objects;

-- Policy: Service role tem acesso total a deliveries
CREATE POLICY "Service role full access - deliveries"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'project-deliveries');

-- Policy: Service role tem acesso total a approvals
CREATE POLICY "Service role full access - approvals"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'project-approvals');

-- Policy: Service role tem acesso total a payments
CREATE POLICY "Service role full access - payments"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'payment-proofs');

-- Policy: Authenticated users podem fazer upload de deliveries
CREATE POLICY "Authenticated users can upload - deliveries"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'project-deliveries');

-- Policy: Authenticated users podem fazer upload de comprovantes
CREATE POLICY "Authenticated users can upload - payments"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'payment-proofs');

-- Policy: Authenticated users podem ler deliveries
CREATE POLICY "Authenticated users can read - deliveries"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'project-deliveries');

-- Policy: Authenticated users podem ler approvals
CREATE POLICY "Authenticated users can read - approvals"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'project-approvals');

-- Policy: Authenticated users podem ler comprovantes
CREATE POLICY "Authenticated users can read - payments"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'payment-proofs');

-- ============================================
-- Verificação de políticas criadas
-- ============================================
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename = 'objects'
  AND schemaname = 'storage'
ORDER BY policyname;
