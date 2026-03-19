import { Link, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { entreprises } from "../data/mockData";

const DocumentDetails = () => {
  const { id, dossierId, documentId } = useParams();

  const entreprise = entreprises.find((item) => item.id === Number(id));
  const dossier = entreprise?.dossiers.find(
    (item) => item.id === Number(dossierId)
  );

  const documentsRecents = [
    {
      id: 1,
      nom: "facture_acme_2024_03.pdf",
      type: "Facture",
      score: "98%",
      statut: "Valide",
      extraction: {
        raisonSociale: "ACME SAS",
        siret: "83241567800012",
        tva: "FR83241567800",
        montantHT: "4 850,00 €",
        tvaMontant: "20%",
        montantTTC: "5 820,00 €",
        dateEmission: "15/03/2024",
        dateEcheance: "15/04/2024",
      },
      validations: [
        "SIRET valide",
        "TVA cohérente",
        "Calcul TTC correct",
        "Document non expiré",
      ],
    },
    {
      id: 2,
      nom: "attestation_vigilance.jpg",
      type: "Attestation",
      score: "91%",
      statut: "Valide",
      extraction: {
        raisonSociale: "ACME SAS",
        siret: "83241567800012",
        tva: "FR83241567800",
        montantHT: "--",
        tvaMontant: "--",
        montantTTC: "--",
        dateEmission: "10/03/2024",
        dateEcheance: "10/06/2024",
      },
      validations: [
        "SIRET valide",
        "Document lisible",
        "Attestation non expirée",
      ],
    },
    {
      id: 3,
      nom: "devis_fournisseur_2024.pdf",
      type: "Devis",
      score: "--",
      statut: "En attente",
      extraction: {
        raisonSociale: "Entreprise test",
        siret: "--",
        tva: "--",
        montantHT: "--",
        tvaMontant: "--",
        montantTTC: "--",
        dateEmission: "--",
        dateEcheance: "--",
      },
      validations: ["Analyse en attente"],
    },
    {
      id: 4,
      nom: "facture_doublon_fournisseur.pdf",
      type: "Facture",
      score: "76%",
      statut: "Anomalie",
      extraction: {
        raisonSociale: "ACME SAS",
        siret: "83241567800012",
        tva: "FR83241567800",
        montantHT: "2 000,00 €",
        tvaMontant: "20%",
        montantTTC: "2 400,00 €",
        dateEmission: "12/03/2024",
        dateEcheance: "12/04/2024",
      },
      validations: [
        "Possible doublon détecté",
        "Vérification manuelle recommandée",
      ],
    },
  ];

  const document = documentsRecents.find(
    (item) => item.id === Number(documentId)
  );

  if (!entreprise || !dossier || !document) {
    return (
      <div className="min-h-screen bg-black text-white flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <h2 className="text-2xl font-bold">Document introuvable</h2>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex">
      <Sidebar />

      <main className="flex-1 p-6">
        <div className="mb-4 flex items-center gap-2 text-sm text-zinc-500">
          <Link to="/entreprises" className="hover:text-white">
            Entreprises
          </Link>
          <span>&gt;</span>
          <Link to={`/entreprises/${entreprise.id}`} className="hover:text-white">
            {entreprise.nom}
          </Link>
          <span>&gt;</span>
          <Link
            to={`/entreprises/${entreprise.id}/dossiers/${dossier.id}/upload`}
            className="hover:text-white"
          >
            {dossier.titre}
          </Link>
          <span>&gt;</span>
          <span className="text-zinc-300">{document.nom}</span>
        </div>

        <div className="mb-6 flex items-center gap-3">
          <Link
            to={`/entreprises/${entreprise.id}/dossiers/${dossier.id}/upload`}
            className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white hover:bg-zinc-700"
          >
            ← Retour
          </Link>

          <span
            className={`rounded-md px-2 py-1 text-xs font-medium ${
              document.statut === "Valide"
                ? "bg-green-500/20 text-green-400"
                : document.statut === "Anomalie"
                ? "bg-red-500/20 text-red-400"
                : "bg-yellow-500/20 text-yellow-400"
            }`}
          >
            {document.statut}
          </span>

          <span className="rounded-md bg-blue-500/20 px-2 py-1 text-xs font-medium text-blue-400">
            {document.type}
          </span>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <h2 className="mb-4 text-lg font-semibold text-white">
              Aperçu du document
            </h2>

            <div className="rounded-xl bg-slate-700/60 p-5 text-sm text-zinc-200">
              <p className="mb-3 text-xl font-bold">ACME SAS</p>
              <p>12 Rue de la Paix, 75001 Paris - SIRET 83241567800012</p>

              <p className="mt-6 text-xl font-semibold">FACTURE N° 2024-0312</p>

              <div className="mt-6 grid grid-cols-2 gap-6 text-sm">
                <div>
                  <p className="mb-2 text-zinc-400">EMETTEUR</p>
                  <p>ACME SAS</p>
                  <p>83241567800012</p>
                  <p>FR83241567800</p>
                </div>

                <div>
                  <p className="mb-2 text-zinc-400">CLIENT</p>
                  <p>Entreprise Client SA</p>
                  <p>Date : 15/03/2024</p>
                  <p>Echéance : 15/04/2024</p>
                </div>
              </div>

              <div className="mt-8 border-t border-zinc-500 pt-4">
                <p>Total HT : 4 850,00 €</p>
                <p>TVA 20% : 970 €</p>
                <p className="font-semibold">TTC : 5 820,00 €</p>
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">Score OCR</h2>

              <div className="mb-3 flex items-center justify-between text-sm">
                <span className="text-zinc-300">Confiance d'extraction</span>
                <span className="font-semibold text-green-400">
                  {document.score === "--" ? "En attente" : document.score}
                </span>
              </div>

              <div className="h-3 w-full rounded-full bg-zinc-800">
                <div
                  className="h-3 rounded-full bg-green-500"
                  style={{
                    width: document.score === "--" ? "10%" : document.score,
                  }}
                ></div>
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Données extraites
              </h2>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Raison sociale</span>
                  <span className="text-white">{document.extraction.raisonSociale}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">SIRET</span>
                  <span className="text-green-400">{document.extraction.siret}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">N° TVA</span>
                  <span className="text-green-400">{document.extraction.tva}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Montant HT</span>
                  <span className="text-white">{document.extraction.montantHT}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">TVA</span>
                  <span className="text-green-400">{document.extraction.tvaMontant}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Montant TTC</span>
                  <span className="text-white">{document.extraction.montantTTC}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Date émission</span>
                  <span className="text-white">{document.extraction.dateEmission}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Date échéance</span>
                  <span className="text-white">{document.extraction.dateEcheance}</span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Validation automatique
              </h2>

              <div className="space-y-2 text-sm">
                {document.validations.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-zinc-400">{item}</span>
                    <span className="text-green-400">OK</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DocumentDetails;