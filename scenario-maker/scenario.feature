Feature: Validation automatique et détection d'anomalies sur les documents administratifs
    En tant qu'utilisateur de la plateforme d'automatisation de la validation des dossiers administratifs,
    Je veux analyser les dossiers et fichiers uploadés (Factures fournisseurs, Devis, Attestation SIRET, Attestation de vigilance URSSAF, Extrait Kbis, RIB)
    Afin de classifier automatiquement les dossiers et fichiers (Légitime, Falsifié, Incomplet, Non-Conforme) et détecter les fraudes potentielles.

    # Scénarios idéaux de validation
    Scenario: Validation d'un dossier complet et parfaitement légitime
        Given un utilisateur upload un dossier complet (Facture, Devis, Kbis, URSSAF, RIB, SIRET)
        And la qualité de l'image est "Nette"
        And le format des fichiers est "PDF" 
        And le "siret" et le "nom" (identite_entreprise) sont strictement identiques sur tous les documents
        And l'attribut "iban" lu sur la facture correspond exactement à l'"iban" du RIB fourni
        And la somme des "total_ht_prestations" de "lignes_facture" correspond au "total_ht" de la facture
        And le Devis possède l'attribut "bon_pour_accord_signe" à True
        And l'attestation URSSAF indique "est_a_jour_obligations" à True
        When le système analyse le dossier complet
        Then le statut final du dossier doit être "Légitime"
        And aucune alerte d'anomalie ne doit être levée

    Scenario: Validation d'une facture fournisseur seule avec données cohérentes
        Given un utilisateur upload une "Facture fournisseur" seule
        And la qualité de l'image est "Nette"
        And le format du fichier est "PDF"
        And les données extraites (identite_entreprise, identite_client, total_ht) sont cohérentes et complètes
        When le système analyse la facture seule
        Then le statut final du document doit être "Légitime"
        And aucune alerte d'anomalie ne doit être levée

    Scenario: Validation d'un Devis seul avec données cohérentes
        Given un utilisateur upload un "Devis" seul
        And la qualité de l'image est "Nette"
        And le format du fichier est "PDF"
        And le champ "montant_total_ht" et "montant_total_ttc" sont extraits avec succès
        And le Devis possède l'attribut "bon_pour_accord_signe" à True
        When le système analyse le Devis seul
        Then le statut final du document doit être "Légitime"

    Scenario: Validation d'un Extrait Kbis seul avec données cohérentes
        Given un utilisateur upload un "Extrait Kbis" seul
        And les données extraites (immatriculation_rcs, denomination_sociale) sont complètes
        And le "code_verification_infogreffe" est validé avec succès via l'API officielle
        When le système analyse le Kbis seul
        Then le statut final du document doit être "Légitime"

    Scenario: Validation d'une Attestation de vigilance URSSAF seule avec données cohérentes
        Given un utilisateur upload une "Attestation de vigilance URSSAF" seule
        And le champ "est_a_jour_obligations" est détecté comme True
        And le "code_securite" est validé avec succès via l'API URSSAF officielle
        When le système analyse l'attestation URSSAF seule
        Then le statut final du document doit être "Légitime"

    Scenario: Validation d'une Attestation SIRET (INPI) seule avec données cohérentes
        Given un utilisateur upload une "Attestation SIRET" seule
        And les données extraites (siren, denomination, forme_juridique) sont extraites
        And le statut "etat_administratif" ou la présence d'au moins un établissement actif est vérifié
        When le système analyse l'attestation SIRET seule
        Then le statut final du document doit être "Légitime"

    Scenario: Validation d'un RIB seul avec données cohérentes
        Given un utilisateur upload un "RIB" seul
        And les données extraites (titulaire_compte, iban, bic) sont cohérentes
        And la structure de l'"iban" est conforme à la norme internationale
        When le système analyse le RIB seul
        Then le statut final du document doit être "Légitime"

    # Falsification ou fraude
    Scenario: Détection d'une falsification par usurpation (Incohérence SIRET)
        Given un utilisateur upload un dossier contenant une "Facture fournisseur" et une "Attestation SIRET"
        And la qualité de l'image est "Nette"
        But le "siret" extrait sur la facture est incohérent par rapport au "siren" ou au "siret" des établissements de l'attestation SIRET
        When le système compare les entités "identite_entreprise"
        Then une erreur spécifique "SIRET différent entre facture et attestation" doit être générée
        And le statut final du dossier doit être "Falsifié"

    Scenario: Falsification des montants sur les lignes de facturation
        Given un utilisateur upload une "Facture fournisseur"
        And la qualité de l'image est "Nette"
        And les informations d'identité de l'entreprise sont correctes
        But la somme des attributs de la liste "total_ht_prestations" dans "lignes_facture" ne correspond pas au "total_ht" déclaré en pied de facture
        When le système recompte les lignes de la facture
        Then une erreur spécifique "Incohérence: Total HT vs Somme des lignes" doit être générée
        And le statut final du dossier doit être "Falsifié"

    Scenario: Tentative de surfacturation entre le Devis et la Facture
        Given un utilisateur upload un "Devis" signé et une "Facture fournisseur"
        But le champ "total_ht" de la facture est strictement supérieur au "montant_total_ht" du devis validé
        When le système confronte les données de facturation aux engagements
        Then une alerte "Montant facture supérieur au devis" doit être générée
        And le statut final du dossier doit être "Falsifié"

    Scenario: Détection d'une tentative de fraude bancaire (Incohérence RIB)
        Given un utilisateur upload un dossier contenant une "Facture fournisseur", un "Extrait Kbis" et un "RIB"
        But le "titulaire_compte" sur le RIB ne correspond ni à la "denomination_sociale" du Kbis, ni au "nom" des dirigeants ("MandataireKbis")
        When le système vérifie la cohérence des données de paiement
        Then une erreur spécifique "Titulaire du compte bancaire suspect" doit être générée
        And le statut final du dossier doit être "Falsifié"

    Scenario: Faux document URSSAF généré numériquement
        Given un utilisateur upload une "Attestation de vigilance URSSAF"
        But le champ "code_securite" interrogé via l'API URSSAF retourne un document appartenant à une autre entreprise (SIREN différent)
        When le module de validation API contrôle les métadonnées de sécurité
        Then une erreur de sécurité critique "Fausse attestation URSSAF - Code de sécurité invalide" doit être générée
        And le statut final du dossier doit être "Falsifié"

    # A voir avec les réponses au questions du team leader
    # Faisable avec l'api https://entreprise.api.gouv.fr/developpeurs/openapi#tag/Informations-generales/paths/~1v3~1infogreffe~1rcs~1unites_legales~1%7Bsiren%7D~1extrait_kbis/get
    Scenario: Utilisation d'un faux document généré (Code Infogreffe invalide)
        Given un utilisateur upload un "Extrait Kbis"
        And la qualité de l'image est "Nette"
        But le champ "code_verification_infogreffe" interrogé via l'API officielle retourne une erreur ou une autre entreprise
        When le module de validation API contrôle les métadonnées de sécurité
        Then une erreur de sécurité critique "Faux Kbis détecté - Code de vérification invalide" doit être générée
        And le statut final du dossier doit être "Falsifié"

    # Problème de conformité et de date dépassée
    Scenario: Non-conformité légale d'une facture fournisseur (Mentions manquantes)
        Given un utilisateur upload une "Facture fournisseur"
        But les champs légaux "penalite_absence_reglement", "taux_penalite_from", ou "conditions_escompte" ne sont pas détectés
        When le système vérifie la structure complète "FactureFournisseur"
        Then une alerte "Mentions légales manquantes: Pénalités ou Escompte" doit être levée
        And le statut final du dossier doit être "Non-Conforme"

    Scenario: Incohérence temporelle dans l'exécution de la prestation
        Given un utilisateur upload une "Facture fournisseur"
        But le champ "date_execution" est détecté comme étant postérieur à la "date_reglement" (échéance)
        When le système vérifie la logique temporelle de la transaction
        Then une alerte "Date d'exécution incohérente avec l'échéance de paiement" doit être générée
        And le statut final du dossier doit être "Non-Conforme"

    Scenario: Rejet d'un Devis non approuvé
        Given un utilisateur upload un "Devis" associé à une facture
        But le champ "bon_pour_accord_signe" est évalué à False (aucune signature reconnue)
        When le système vérifie l'engagement juridique
        Then une alerte "Devis non signé" doit être générée
        And le statut final du dossier doit être "Non-Conforme"

    Scenario: Rejet d'un Devis expiré lors de la facturation
        Given un utilisateur upload un "Devis" et une "Facture fournisseur"
        But la date "date_emission" de la facture est ultérieure à la date limite du devis (date_emission_devis + date_validite_jours)
        When le système valide la conformité temporelle
        Then une alerte "Devis expiré à la date de facturation" doit être générée
        And le statut final du dossier doit être "Non-Conforme"

    Scenario: Rejet d'un dossier avec entreprise défaillante auprès de l'URSSAF
        Given un utilisateur upload une "Attestation de vigilance URSSAF"
        But le champ "est_a_jour_obligations" est détecté comme False
        When le système lit les données sociales déclarées ("AttestationVigilanceUrssaf")
        Then une erreur critique "Entreprise non à jour de ses cotisations sociales" doit être générée
        And le statut final du dossier doit être "Rejeté"

    Scenario: Rejet d'un dossier administratif avec un Kbis périmé
        Given un utilisateur upload un "Extrait Kbis"
        But la "date_mise_a_jour" de l'Extrait Kbis date de plus de 3 mois par rapport à la date du jour de contrôle
        When le système valide la conformité temporelle
        Then une erreur spécifique "Extrait Kbis périmé (plus de 3 mois)" doit être générée
        And le statut final du dossier doit être "Non-Conforme"

    Scenario: Rejet pour pièce de vigilance obligatoire manquante (> 5000 euros)
        Given un utilisateur upload une "Facture fournisseur"
        And le montant "total_ht" est strictement supérieur à 5000 euros
        But le dossier ne contient ni "Extrait Kbis" ni "Attestation de vigilance URSSAF"
        When le système analyse la complétude du dossier selon les règles légales de seuil
        Then une erreur spécifique "Documents de vigilance obligatoires manquants (Seuil > 5000€)" doit être générée
        And le statut final du dossier doit être "Incomplet"

    #   Matrice de tests
    Scenario Outline: Matrice de tests globale pour le pipeline d'ingestion documentaire
        Given un dossier contenant "<composition>"
        And la qualité de l'image est "<qualite>"
        And le format des documents est "<format>"
        And le dossier présente la caractéristique suivante : "<caracteristique>"
        When le pipeline traite les documents et mappe les entités
        Then le système doit classifier le dossier comme "<statut>"
        And l'alerte retournée doit être "<alerte_attendue>"

    Examples:
        | composition                                  | format   | qualite   | caracteristique                                                 | statut       | alerte_attendue                                        |
        | Facture seule                                | PDF      | Nette     | Données exactes, total < 5000€, toutes mentions présentes       | Légitime     | Aucune                                                 |
        | Facture + SIRET                              | PDF      | Nette     | Les numéros de SIRET/SIREN ne correspondent pas                 | Falsifié     | SIRET différent                                        |
        | Facture + Kbis                               | PDF      | Nette     | La 'forme_juridique' diffère (ex SASU vs SARL)                  | Falsifié     | Incohérence forme juridique                            |
        | Facture + Devis                              | PDF      | Flouté    | La somme des 'total_ht_prestations' est fausse                  | Falsifié     | Incohérence - Total HT vs Somme des lignes             |
        | Facture + Devis                              | PDF      | Nette     | 'total_ht' facture > 'montant_total_ht' devis                   | Falsifié     | Montant facture supérieur au devis                     |
        | Facture + Kbis + URSSAF                      | PDF      | Pixelisée | `est_a_jour_obligations` de l'URSSAF est à False                | Rejeté       | Entreprise non à jour de ses cotisations               |
        | Facture > 5000€ seule                        | PDF      | Nette     | L'attestation URSSAF n'est pas fournie                          | Incomplet    | Documents obligatoires manquants                       |
        | Facture + RIB + Kbis                         | PDF      | Nette     | `titulaire_compte` RIB est différent du Kbis                    | Falsifié     | Titulaire du compte bancaire suspect                   |
        | Facture + Devis + Kbis + URSSAF + RIB + SIRET| PDF      | Nette     | Toutes les données de tous les schémas coïncident parfaitement  | Légitime     | Aucune                                                 |
        | Devis seul                                   | PDF      | Nette     | `bon_pour_accord_signe` est à False                             | Non-Conforme | Devis non signé                                        |
        | Extrait Kbis seul                            | PDF      | Nette     | Le `code_verification_infogreffe` est inconnu de l'API          | Falsifié     | Faux Kbis détecté - Code de vérification invalide      |
        | Attestation URSSAF seule                     | PDF      | Nette     | Le `code_securite` est attribué à un autre SIREN                | Falsifié     | Fausse attestation URSSAF - Code de sécurité invalide  |