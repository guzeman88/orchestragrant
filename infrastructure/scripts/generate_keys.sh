#!/usr/bin/env bash
# generate_keys.sh — Generate RS256 key pair for JWT signing
# Usage: bash generate_keys.sh [--bits 4096] [--out ./secrets]
#
# Outputs:
#   private.pem   — RSA private key (keep secret, load as JWT_PRIVATE_KEY)
#   public.pem    — RSA public key  (safe to share, load as JWT_PUBLIC_KEY)
#   .env.keys     — Env file with both keys in single-line format (use in .env)

set -euo pipefail

BITS=4096
OUT_DIR="./secrets"

while [[ $# -gt 0 ]]; do
  case $1 in
    --bits)  BITS="$2"; shift 2 ;;
    --out)   OUT_DIR="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

echo "Generating ${BITS}-bit RSA key pair..."

# Generate private key
openssl genrsa -out "${OUT_DIR}/private.pem" "$BITS" 2>/dev/null
chmod 600 "${OUT_DIR}/private.pem"

# Extract public key
openssl rsa -in "${OUT_DIR}/private.pem" -pubout -out "${OUT_DIR}/public.pem" 2>/dev/null
chmod 644 "${OUT_DIR}/public.pem"

# Write single-line versions for .env
PRIVATE_SINGLE=$(awk 'NF {printf "%s\\n", $0}' "${OUT_DIR}/private.pem")
PUBLIC_SINGLE=$(awk 'NF {printf "%s\\n", $0}' "${OUT_DIR}/public.pem")

cat > "${OUT_DIR}/.env.keys" <<EOF
# RS256 JWT key pair — generated $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Copy these into your .env file
JWT_PRIVATE_KEY="${PRIVATE_SINGLE}"
JWT_PUBLIC_KEY="${PUBLIC_SINGLE}"
EOF
chmod 600 "${OUT_DIR}/.env.keys"

echo ""
echo "Keys written to ${OUT_DIR}/"
echo "  private.pem  → JWT_PRIVATE_KEY  (keep secret)"
echo "  public.pem   → JWT_PUBLIC_KEY   (safe to share)"
echo "  .env.keys    → copy these lines into your .env file"
echo ""
echo "To add to AWS SSM Parameter Store (prod):"
echo "  aws ssm put-parameter \\"
echo "    --name '/orchestragrant/prod/JWT_PRIVATE_KEY' \\"
echo "    --value \"\$(cat ${OUT_DIR}/private.pem)\" \\"
echo "    --type SecureString"
echo "  aws ssm put-parameter \\"
echo "    --name '/orchestragrant/prod/JWT_PUBLIC_KEY' \\"
echo "    --value \"\$(cat ${OUT_DIR}/public.pem)\" \\"
echo "    --type String"
