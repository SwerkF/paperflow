# Projet PaperFlow - Hackathon 2026
Ce projet repose sur Flask pour le routage HTTP et utilise PaddleOCR pour la reconnaissance de caractères.

## Objectifs
L'objectif de cette API est de transformer des images ou des scans de documents ("données non structurées") en objets JSON précis et exploitables ("données structurées").

Un OCR léger (PaddleOCR) pour extraire le texte brut et sa position dans l'espace.

Un moteur d'heuristiques "métier" (Expressions Régulières et Algorithmes géométriques) pour classifier et structurer les données.

## Archtecture Technique et "Design Patterns"

L'architecture a été conçue pour maximiser les performances et limiter l'empreinte mémoire

### 1. Séparation OCR / Métier

Dans les premières versions, chaque classe de document chargeait et exécutait son propre modèle OCR. Cette approche saturait la RAM et ralentissait considérablement le serveur.

Actuellement, e fichier principal `api.py` agit gère l'ensemble des algorithmes. Il charge le modèle une seule fois au démarrage du serveur.

Lorsqu'une requête arrive, `api.py` exécute l'OCR, extrait le texte brut et ses coordonnées, devine le type de document, puis passe le relais à la classe métier correspondante.

Les classes métiers (*AnalyzeFacture*, *AnalyzeRIB*, *AnalyzeDevis*, *AnalyzeKBIS*, *AnalyzeSIRET*, *AnalyzeURRSAF*) sont devenues des classes logique (RegEx et algorithmes de formatage).

### 2. Le Lazy Loading des Configurations

Les règles d'extraction (Expressions Régulières) de chaque document sont stockées dans des fichiers JSON externes (analyse/facture.json, etc.).

Lors du démarrage de Flask, les classes Python sont instanciées et pré-chargent ces configurations JSON en mémoire (ainsi que la pré-compilation des RegEx globales). Ainsi, lors d'une requête API, le serveur n'a pas beson de faire d'opérations de lecture sur le disque dur, garantissent un temps de réponse minimal.

### 3. La Gestion de la Concurrence via TemporaryDirectory

Afin de parser les résultats de PaddleOCR, la bibliothèque exige d'écrire des fichiers temporaires.

Pour éviter que les requêtes simultanées de plusieurs utilisateurs ne s'écrasent mutuellement, l'API utilise la librairie tempfile de Python.

```python
with tempfile.TemporaryDirectory() as temp_dir:
    # Traitement isolé...
```

Ce bloc crée un dossier unique et aléatoire pour chaque requête HTTP. 

De plus, il garantit la suppression automatique des fichiers dès la fin de la requête, évitant toute fuite de données (RGPD).

### 4. Flexibilité des Entrées (Fichier physique vs Base64)

L'API est conçue pour s'adapter à divers clients (Frontend web, autres serveurs, requêtes Postman) :

Elle accepte l'envoi classique de fichiers (*multipart/form-data*).

Elle accepte l'envoi de la chaîne de l'image encodée en *Base64* (application/json), ce qui permet des transferts plus rapides et directs de serveur à serveur sans manipulation de fichiers physiques.

## Requête

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."}'
```

## Répose

```json
{
    "data": {
        "bloc_bic": {
            "description": "Bloc BIC / SWIFT",
            "full_match": "BNPSFRTTOSA",
            "groups": {
                "bic_swift": "BNPSFRTTOSA"
            },
            "matched": true,
            "regex": "heuristic_bic"
        },
        "bloc_domiciliation": {
            "description": "Bloc de domiciliation bancaire",
            "full_match": "de I'agence et la ville où elle se situe Code banque Code Guichet Numero de compte Cle RIB RIB 12345 00300 09876543210 19",
            "groups": {
                "domiciliation": "de I'agence et la ville où elle se situe Code banque Code Guichet Numero de compte Cle RIB RIB 12345 00300 09876543210 19"
            },
            "matched": true,
            "regex": "heuristic_domiciliation"
        },
        "bloc_iban": {
            "description": "Bloc IBAN",
            "full_match": "FR12345003000987654321019",
            "groups": {
                "iban_segment_1": "FR12",
                "iban_segment_2": "3450",
                "iban_segment_3": "0300",
                "iban_segment_4": "0987",
                "iban_segment_5": "6543",
                "iban_segment_6": "2101",
                "iban_segment_7": "9"
            },
            "matched": true,
            "regex": "heuristic_iban"
        },
        "bloc_intro_en": {
            "description": "Paragraphe explicatif en anglais",
            "full_match": null,
            "groups": {},
            "matched": false,
            "regex": "This document is intended to be delivered[\\s\\S]+?invoice payments, etc\\.\\)"
        },
        "bloc_intro_fr": {
            "description": "Paragraphe explicatif en français",
            "full_match": null,
            "groups": {},
            "matched": false,
            "regex": "Ce relev[ée] est destin[ée] à [\\s\\S]+?\\(virements, paiements de quittances, etc\\.\\)"
        },
        "bloc_partie_reservee": {
            "description": "Mention de la partie réservée au destinataire",
            "full_match": null,
            "groups": {},
            "matched": false,
            "regex": "Partie r[ée]serv[ée]e au destinataire du relev[ée]"
        },
        "bloc_rib_national": {
            "description": "Bloc identifiant national RIB",
            "full_match": "Domiciliation bancaire : Nom de votre banque, de I'agence et la ville où elle se situe Code banque Code Guichet Numero de compte Cle RIB RIB 12345 00300 09876543210 19",
            "groups": {
                "cle_rib": "19",
                "code_banque": "12345",
                "code_guichet": "00300",
                "devise": "RIB",
                "domiciliation": "Domiciliation bancaire : Nom de votre banque, de I'agence et la ville où elle se situe",
                "nom_banque": "WorldRemit",
                "numero_compte": "09876543210"
            },
            "matched": true,
            "regex": "heuristic_rib_national"
        },
        "bloc_titulaire_compte": {
            "description": "Bloc titulaire du compte",
            "full_match": "WorldRemit Domiciliation bancaire : Nom de votre banque, de I'agence et la ville où elle se situe Code banque Code Guichet Numero de compte Cle RIB RIB 12345 00300 09876543210 19 IBAN FR12345003000987654321019 BIC/SWIFT BNPSFRTTOSA",
            "groups": {
                "adresse_titulaire": "12345",
                "nom_titulaire": "MME XXX"
            },
            "matched": true,
            "regex": "heuristic_account_holder"
        },
        "document_type": {
            "description": "Type de document",
            "full_match": "Relevé d'identité bancaire",
            "groups": {
                "1": "Relevé d'identité bancaire"
            },
            "matched": true,
            "regex": "(Relev[ée]\\s+d[’']Identit[ée]\\s+Bancaire|RIB)"
        }
    },
    "document_type": "rib",
    "status": "success"
}
```

## Utilisation

Créer et activer un environnement virtuel Python :

```bash
python -m venv venv
source venv/bin/activate
```

Installer les dépendances :

```python
pip install -r requirements.txt
```

### Lancer le serveur Flask :

```bash
python api.py
```

L'API sera disponible sur http://127.0.0.1:8000