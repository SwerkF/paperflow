## Jeux de données (batch contextualisé)

### Scénarios

- `00_aucune_erreur.json`: facture + URSSAF valides
- `01_nom_different_siret_principal.json`: même SIRET principal, nom différent
- `02_hors_perimetre_siret_different.json`: document rattaché à un autre SIRET
- `03_siret_manquant.json`: SIRET absent/indéterminé
- `04_siret_invalide_format_et_luhn.json`: SIRET invalide (longueur) + invalide (Luhn)
- `05_facture_erreurs_montants.json`: incohérence HT/TVA/TTC + format montant invalide
- `06_urssaf_expiree_et_date_invalide.json`: attestation expirée + date invalide
- `07_nom_different_clair_microsoft_macrosoft.json`: SIRET identique, nom clairement différent
- `08_siret_different_1_chiffre.json`: nom identique, SIRET à 1 chiffre près

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/00_aucune_erreur.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/01_nom_different_siret_principal.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/02_hors_perimetre_siret_different.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/03_siret_manquant.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/04_siret_invalide_format_et_luhn.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/05_facture_erreurs_montants.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/06_urssaf_expiree_et_date_invalide.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/07_nom_different_clair_microsoft_macrosoft.json | jq

curl -sS -X POST "http://localhost:5030/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  --data-binary @data-validation/fixtures/batch-contextualise/08_siret_different_1_chiffre.json | jq