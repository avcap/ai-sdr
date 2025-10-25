-- Add document_type column to training_documents table
-- This column will store the type of document (sales_training, company_info, industry_knowledge, etc.)

ALTER TABLE public.training_documents 
ADD COLUMN IF NOT EXISTS document_type text DEFAULT 'general';

-- Add a comment to explain the column
COMMENT ON COLUMN public.training_documents.document_type IS 'Type of document: sales_training, company_info, industry_knowledge, general, etc.';

-- Update existing records to have a default document_type
UPDATE public.training_documents 
SET document_type = 'general' 
WHERE document_type IS NULL;

-- Make the column NOT NULL after setting defaults
ALTER TABLE public.training_documents 
ALTER COLUMN document_type SET NOT NULL;

-- Add an index for better query performance
CREATE INDEX IF NOT EXISTS idx_training_documents_document_type 
ON public.training_documents USING btree (document_type);
