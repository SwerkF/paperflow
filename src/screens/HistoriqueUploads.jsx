import Sidebar from "../components/Sidebar";
import { documentsHistory } from "../data/mockHistory";
import { Link } from "react-router-dom";

const getStatusClasses = (statut) => {
  switch (statut) {
    case "Valide":
      return "bg-green-500/20 text-green-400";
    case "Expiré":
      return "bg-orange-500/20 text-orange-400";
    case "SIRET incohérent":
      return "bg-red-500/20 text-red-400";
    case "TVA incohérente":
      return "bg-orange-500/20 text-orange-400";
    case "En cours":
      return "bg-blue-500/20 text-blue-400";
    default:
      return "bg-zinc-700 text-white";
  }
};

const getScoreBarColor = (score) => {
  if (score === null) return "bg-zinc-500";
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-orange-500";
  return "bg-red-500";
};

const HistoriqueUploads = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">
              Historique des documents
            </h1>
            <p className="mt-1 text-sm text-zinc-400">
              2 847 documents traités au total
            </p>
          </div>

          <div className="mb-6 flex flex-wrap gap-3">
            <select className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white outline-none">
              <option>Tous les types</option>
              <option>Facture</option>
              <option>Attestation</option>
              <option>Devis</option>
              <option>Contrat</option>
              <option>Kbis</option>
            </select>

            <select className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white outline-none">
              <option>Tous les statuts</option>
              <option>Valide</option>
              <option>Expiré</option>
              <option>En cours</option>
              <option>SIRET incohérent</option>
              <option>TVA incohérente</option>
            </select>

            <select className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white outline-none">
              <option>7 derniers jours</option>
              <option>30 derniers jours</option>
              <option>3 derniers mois</option>
            </select>
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">
            <div className="grid grid-cols-6 border-b border-zinc-800 px-4 py-3 text-xs uppercase tracking-wide text-zinc-400">
              <span>Fichier</span>
              <span>Type</span>
              <span>Score OCR</span>
              <span>Statut</span>
              <span>Traité le</span>
              <span>Action</span>
            </div>

            {documentsHistory.map((doc) => (
              <div
                key={doc.id}
                className="grid grid-cols-6 items-center border-b border-zinc-800 px-4 py-4 text-sm last:border-b-0"
              >
                <div className="flex items-start gap-3">
                 

                  <div>
                    <p className="font-medium text-white">{doc.nom}</p>
                    <p className="text-xs text-zinc-500">
                      Ajouté par {doc.auteur}
                    </p>
                  </div>
                </div>

                <span className="text-zinc-300">{doc.type}</span>

                <div className="flex items-center gap-3">
                  
                  <span className="text-zinc-300">
                    {doc.score === null ? "-- en attente" : `${doc.score}%`}
                  </span>
                </div>

                <span
                  className={`inline-block w-fit rounded-md px-2 py-1 text-xs font-medium ${getStatusClasses(
                    doc.statut
                  )}`}
                >
                  {doc.statut}
                </span>

                <span className="text-zinc-300">{doc.traiteLe}</span>

                <div>
                  <Link
                    to="/entreprises/1/dossiers/101/documents/1"
                    className="inline-flex items-center rounded-lg bg-zinc-800 px-3 py-2 text-xs text-white transition hover:bg-zinc-700"
                  >
                    Voir
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-zinc-400">
            <p>Affichage 1-7 sur 2 847 documents</p>

            <div className="flex items-center gap-2">
              <button className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700">
                &lt;
              </button>
              <button className="rounded bg-blue-500 px-3 py-1 text-white">
                1
              </button>
              <button className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700">
                2
              </button>
              <button className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700">
                3
              </button>
              <button className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700">
                407
              </button>
              <button className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700">
                &gt;
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default HistoriqueUploads;