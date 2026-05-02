output "domain"               { value = aws_ses_domain_identity.main.domain }
output "verification_token"   { value = aws_ses_domain_identity.main.verification_token }
output "dkim_tokens"          { value = aws_ses_domain_dkim.main.dkim_tokens }
