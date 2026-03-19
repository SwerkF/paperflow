import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import { Link } from "react-router-dom";
import { getSilverDocuments } from "../services/storage.service";

const getStatusClasses = (statut) => {
  if (statut === "VALIDE") {
    return "bg-green-500/20 text-green-400";
  }
  if (statut === "EN_ATTENTE_SUPERVISION" || statut === "Anomalie") {
    return "bg-orange-500/20 text-orange-400";
  }
  return "bg-zinc-700 text-white";
};

const getScoreBarColor = (score) => {
  if (score === null || score === "--") return "bg-zinc-500";
  const num = parseInt(score);
  if (num >= 90) return "bg-green-500";
  if (num >= 75) return "bg-orange-500";
  return "bg-red-500";
};

const HistoriqueUploads = () => {
  const [documentsHistory, setDocumentsHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination simplifiée
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        // On récupère depuis la collection Silver (qui a déjà passé l'OCR)
        const docs = await getSilverDocuments();
        const formattedDocs = docs.map(doc => ({
          id: doc.id,
          nom: doc.filename || "Document inconnu",
          auteur: "Système",
          type: doc.document_type || "inconnu",
          score: doc.ocr_confidence ? (doc.ocr_confidence * 100).toFixed(0) : null,
          statut: doc.status === "EN_ATTENTE_SUPERVISION" ? "Anomalie" : doc.status,
          traiteLe: doc.processed_at ? new Date(doc.processed_at).toLocaleString("fr-FR") : "-",
          entrepriseId: doc.entrepriseId || "0",
          dossierId: doc.dossierId || "0",
        })).reverse(); // Les plus récents en premier
        
        setDocumentsHistory(formattedDocs);
      } catch (err) {
        console.error("Erreur de chargement de l'historique", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const totalPages = Math.ceil(documentsHistory.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentItems = documentsHistory.slice(startIndex, startIndex + itemsPerPage);

  const goToPrevious = () => { if (currentPage > 1) setCurrentPage(prev => prev - 1); };
  const goToNext = () => { if (currentPage < totalPages) setCurrentPage(prev => prev + 1); };

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
              {documentsHistory.length} documents traités au total par l'IA
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">
            <div className="grid grid-cols-[2fr_1.5fr_1.5fr_1.5fr_1fr] border-b border-zinc-800 px-4 py-3 text-xs uppercase tracking-wide text-zinc-400">
              <span>Fichier</span>
              <span>Type</span>
              <span>Statut</span>
              <span>Traité le</span>
              <span>Action</span>
            </div>

            {loading ? (
               <div className="p-8 text-center text-zinc-500">Chargement de l'historique depuis la base de données...</div>
            ) : documentsHistory.length === 0 ? (
               <div className="p-8 text-center text-zinc-500">Aucun document traité pour le moment.</div>
            ) : (
              currentItems.map((doc) => (
                <div
                  key={doc.id}
                  className="grid grid-cols-[2fr_1.5fr_1.5fr_1.5fr_1fr] items-center border-b border-zinc-800 px-4 py-4 text-sm last:border-b-0"
                >
                  <div className="flex items-start gap-3 min-w-0 pr-4">
                    <div className="min-w-0">
                      <p className="font-medium text-white truncate max-w-[200px]" title={doc.nom}>{doc.nom}</p>
                      <p className="text-xs text-zinc-500">
                        Ajouté par {doc.auteur}
                      </p>
                    </div>
                  </div>

                  <span className="text-zinc-300 uppercase">{doc.type}</span>

                  <div>
                    <span
                      className={`inline-block w-fit rounded-md px-2 py-1 text-xs font-medium uppercase ${getStatusClasses(
                        doc.statut
                      )}`}
                    >
                      {doc.statut}
                    </span>
                  </div>

                  <span className="text-zinc-300">{doc.traiteLe}</span>

                  <div>
                    <Link
                      to={`/entreprises/${doc.entrepriseId}/dossiers/${doc.dossierId}/documents/${doc.id}`}
                      className="inline-flex items-center rounded-lg bg-zinc-800 px-3 py-2 text-xs text-white transition hover:bg-zinc-700 hover:text-green-400"
                    >
                      Voir le doc
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>

          {!loading && documentsHistory.length > 0 && (
            <div className="mt-4 flex items-center justify-between text-sm text-zinc-400">
              <p>Affichage {startIndex + 1}-{Math.min(startIndex + itemsPerPage, documentsHistory.length)} sur {documentsHistory.length} documents</p>

              <div className="flex items-center gap-2">
                <button onClick={goToPrevious} disabled={currentPage === 1} className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700 disabled:opacity-50">
                  &lt; Précédent
                </button>
                <button onClick={goToNext} disabled={currentPage === totalPages} className="rounded bg-zinc-800 px-3 py-1 hover:bg-zinc-700 disabled:opacity-50">
                  Suivant &gt;
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default HistoriqueUploads;