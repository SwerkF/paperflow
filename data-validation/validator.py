from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime

_REGEX_SIRET = re.compile(r"^\d{14}$")
_REGEX_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REGEX_MONTANT = re.compile(r"^\d+(?:[.,]\d{1,2})?$")

class ServiceValidation:
    def __init__(self):
        self.documents_stockes = []
        self.entites_connues = {}

    def _push_alert(self, alertes, doc_id, message: str):
        """
        Ajoute une alerte à la liste des alertes.
        """
        alertes.append({"doc_id": doc_id, "message": message})

    def _clean_siret(self, siret):
        """
        Normalise le SIRET, c'est à dire que l'on retire les espaces et les caractères non numériques.
        """
        if siret is None:
            return None
        s = str(siret).strip().replace(" ", "")
        return s or None

    def _matches(self, valeur, regex: re.Pattern):
        """
        Vérifie si la valeur correspond au regex.
        """
        if valeur is None:
            return False
        return bool(regex.match(str(valeur).strip()))

    def _luhn_ok(self, numero: str) -> bool:
        """
        Vérifie si le numéro de SIRET est valide.
        """
        if not numero or not numero.isdigit():
            return False
        total = 0
        inverse = numero[::-1]
        for i, ch in enumerate(inverse):
            digit = int(ch)
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0

    def _check_entity(self, entite_data, doc_id, role_entite):
        """
        Vérifie si l'entité est valide.
        """
        alertes = []
        if not entite_data:
            return alertes

        siret = self._clean_siret(entite_data.get("siret"))
        nom = entite_data.get("nom")

        if siret:
            if not self._matches(siret, _REGEX_SIRET):
                self._push_alert(
                    alertes,
                    doc_id,
                    f"SIRET invalide pour {role_entite} : '{siret}' (14 chiffres attendus).",
                )
                return alertes

            if not self._luhn_ok(siret):
                self._push_alert(
                    alertes,
                    doc_id,
                    f"SIRET invalide pour {role_entite} : '{siret}'.",
                )
                return alertes

            if siret in self.entites_connues:
                entite_ref = self.entites_connues[siret]
                if nom and nom != entite_ref.get("nom"):
                    self._push_alert(
                        alertes,
                        doc_id,
                        (
                            f"Incohérence d'identité ({role_entite}) : le nom '{nom}' ne "
                            f"correspond pas au SIRET {siret} (attendu: '{entite_ref.get('nom')}')."
                        ),
                    )
            else:
                entite_normalisee = deepcopy(entite_data)
                entite_normalisee["siret"] = siret
                self.entites_connues[siret] = entite_normalisee

        return alertes

    def _warm_entity_cache(self):
        """
        Récupère les entités connues à partir des documents stockés.
        """
        for doc in self.documents_stockes:
            doc_id = doc.get("id", "Inconnu")
            for cle, role in (
                ("company", "Entreprise"),
                ("fournisseur", "Fournisseur"),
                ("client", "Client"),
            ):
                entite = doc.get(cle)
                self._check_entity(entite, doc_id, role)

    def _check_urssaf_dates(self, doc, doc_id, alertes_globales):
        type_doc = doc.get("type", "Inconnu")
        if type_doc != "urssaf" or "date_expiration" not in doc:
            return

        date_exp_raw = doc.get("date_expiration")
        if not self._matches(date_exp_raw, _REGEX_DATE_ISO):
            self._push_alert(
                alertes_globales,
                doc_id,
                f"Format de date invalide pour date_expiration : '{date_exp_raw}' (YYYY-MM-DD attendu).",
            )
            return

        try:
            date_exp = datetime.strptime(date_exp_raw, "%Y-%m-%d")
        except ValueError:
            self._push_alert(
                alertes_globales,
                doc_id,
                f"Date invalide pour date_expiration : '{date_exp_raw}'.",
            )
            return

        if date_exp < datetime.now():
            self._push_alert(
                alertes_globales,
                doc_id,
                f"L'attestation est expirée depuis le {date_exp_raw}.",
            )

    def _parse_amount(self, valeur):
        if isinstance(valeur, str) and self._matches(valeur, _REGEX_MONTANT):
            return float(valeur.replace(",", "."))
        return valeur

    def _check_invoice_math(self, doc, doc_id, alertes_globales):
        type_doc = doc.get("type", "Inconnu")
        if type_doc != "facture":
            return

        for champ in ("montant_ht", "montant_ttc"):
            v = doc.get(champ)
            if isinstance(v, str) and v.strip() and not self._matches(v, _REGEX_MONTANT):
                self._push_alert(
                    alertes_globales,
                    doc_id,
                    f"Format invalide pour {champ} : '{v}' (ex: 1234.56 ou 1234,56).",
                )

        montant_ht = self._parse_amount(doc.get("montant_ht"))
        montant_ttc = self._parse_amount(doc.get("montant_ttc"))
        tva = doc.get("tva")

        if None not in (montant_ht, montant_ttc, tva):
            calcul_ttc = montant_ht * (1 + tva)
            if abs(calcul_ttc - montant_ttc) > 0.05:
                self._push_alert(
                    alertes_globales,
                    doc_id,
                    (
                        f"Calcul faux : HT({montant_ht}) + TVA({tva*100}%) = "
                        f"{calcul_ttc}, mais l'OCR a lu TTC({montant_ttc})."
                    ),
                )

    def valider_lot_documents(self, nouveaux_documents):
        alertes_globales = []

        self._warm_entity_cache()

        for doc in nouveaux_documents:
            doc_id = doc.get("id", "Inconnu")
            type_doc = doc.get("type", "Inconnu")

            if type_doc == "facture":
                alertes_globales.extend(
                    self._check_entity(doc.get("fournisseur"), doc_id, "Fournisseur")
                )
                alertes_globales.extend(
                    self._check_entity(doc.get("client"), doc_id, "Client")
                )
            else:
                alertes_globales.extend(
                    self._check_entity(doc.get("company"), doc_id, "Entreprise")
                )

            self._check_urssaf_dates(doc, doc_id, alertes_globales)
            self._check_invoice_math(doc, doc_id, alertes_globales)

            self.documents_stockes.append(doc)

        return alertes_globales