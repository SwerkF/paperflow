from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

@dataclass
class IdentiteEntriprise:
    nom: str
    siret: str
    rcs: str
    adresse: str
    site_web: str

@dataclass
class IdentiteClient:
    nom: str
    adresse: str

@dataclass
class IdentiteEmetteurDevis:
    nom: str
    prenom: str
    fonction: str

@dataclass
class IdentiteClientDevis:
    nom: str
    prenom: str
    adresse: str

@dataclass
class DirigeantSiret:
    nom_prenoms: str
    qualite: str
    date_naissance_mm_aaaa: str
    commune_residence: str

@dataclass
class EtablissementSiret:
    type_etablissement: str
    date_debut_activite: str
    siret: str
    nom_commercial: str
    code_ape: str
    origine_fonds: str
    nature_etablissement: str
    activite_principale: str
    adresse: str

@dataclass
class LigneFacture:
    designation_prestations: List[str]
    quantite_prestations: List[Decimal]
    prix_unitaire_ht_prestations: List[Decimal]
    total_ht_prestations: List[Decimal]
    taux_tva_prestations: List[Decimal]

@dataclass
class MandataireKbis:
    """Regroupe les dirigeants."""
    fonction: str
    nom_prenoms_ou_denomination: str
    date_lieu_naissance: str
    nationalite: str
    domicile_ou_adresse: str

@dataclass
class EtablissementPrincipalKbis:
    """activité et à l'établissement principal."""
    adresse_etablissement: str
    activites_exercees: str
    date_commencement_activite: str
    origine_fonds_ou_activite: str
    mode_exploitation: str


"""
Schémas basés sur les documents trouvés sur les sites officiels.
"""
# FACTURE FOURNISSEUR
@dataclass
class Facture:
    """
    Champs obligatoires Facture.
    """
    identite_entreprise: IdentiteEntriprise
    identite_client: IdentiteClient
    
    numero_facture: str

    lignes_facture: List[LigneFacture]

    date_reglement: date
    date_execution: date
    taux_penalite_from: date

    penalite_absence_reglement: Decimal
    conditions_escompte: str

    total_ht: Decimal

# DEVIS
@dataclass
class Devis:
    """
    Champs obligatoires devis.
    """
    emetteur_devis: IdentiteEmetteurDevis
    client_devis: IdentiteClientDevis

    reference_devis: str
    date_emission: date
    date_validite: int

    identite_entreprise: IdentiteEntriprise
    identite_client: IdentiteClient
    montant_total_ht: Decimal
    montant_total_ttc: Decimal
    bon_pour_accord_signe: bool 

# ATTESTATION SIRET (INPI)
@dataclass
class AttestationSiret:
    """Attestation INPI """
    date_attestation: str
    
    # Identité de l'entreprise
    denomination: str
    siren: str
    date_immatriculation_rne: str
    date_debut_activite_entreprise: str
    date_fin_personne_morale: str
    nature_activite_principale: str
    forme_juridique: str
    associe_unique: bool
    activites_principales_objet_social: str
    code_ape_entreprise: str
    capital_social: str
    adresse_siege: str
    
    # Entités liées
    dirigeants: List[DirigeantSiret]
    etablissements: List[EtablissementSiret]

# VIGILANCE URSAF
@dataclass
class AttestationVigilanceUrssaf:
    """attestation de vigilance"""
    
    # émetteur
    organisme_emetteur: str
    lieu_emission: str
    date_emission: str
    directeur_signataire: str
    
    # identification
    code_securite: str
    nom_entreprise: str
    siren: str
    
    # Données sociales déclarées
    effectif_moyen_mensuel: int
    masse_salariale_euros: Decimal
    periode_reference: str
    
    # conformité
    est_a_jour_obligations: bool
    date_verification_obligations: str

# KBIS
@dataclass
class Kbis:
    """Schéma kbsi."""
    
    # En-tête et Méta-données
    greffe_immatriculation: str
    numero_gestion: str
    date_mise_a_jour: str
    code_verification_infogreffe: str
    
    # personne morale
    immatriculation_rcs: str
    date_immatriculation: str
    denomination_sociale: str
    forme_juridique: str
    capital_social_euros: Decimal
    adresse_siege: str
    duree_personne_morale: str
    date_cloture_exercice_social: str
    
    # Direction, Administration, Contrôle
    mandataires: List[MandataireKbis]
    
    # Activité et Établissement
    etablissement_principal: EtablissementPrincipalKbis

# RIB
@dataclass
class Rib:
    """
    Coordonnées bancaires.
    """
    titulaire_compte: str
    iban: str
    bic: str
    nom_banque: str