import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import { Link } from "react-router-dom";
import { getSilverDocuments } from "../services/storage.service";

const getBadgeClass = (niveau) => {
  if (niveau === "Critique") {
    return "bg-red-500/20 text-red-400";
  }

  if (niveau === "Avertissement") {
    return "bg-orange-500/20 text-orange-400";
  }

  return "bg-zinc-700 text-white";
};

const Anomalies = () => {
  const [anomaliesData, setAnomaliesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const docs = await getSilverDocuments();
        const flatAnomalies = [];
        docs.forEach((doc) => {
          if (doc.status === "EN_ATTENTE_SUPERVISION" && Array.isArray(doc.alertes)) {
            doc.alertes.forEach((alerte, index) => {
              const msg = alerte.message || "";
              const isCritique = msg.toLowerCase().includes("introuvable") || msg.toLowerCase().includes("vide");
              flatAnomalies.push({
                id: `${doc.id}-${index}`,
                type: msg,
                description: "Validation IA",
                document: doc.filename || "Inconnu",
                comparaison: `Ref Validation: ${alerte.doc_id || "BATCH"}`,
                detail: `Doc ID: ${doc.id.substring(0,6)}...`,
                date: doc.processed_at ? new Date(doc.processed_at).toLocaleString("fr-FR") : "-",
                niveau: isCritique ? "Critique" : "Avertissement",
                entrepriseId: doc.entrepriseId,
                dossierId: doc.dossierId,
                documentId: doc.id,
              });
            });
          }
        });
        setAnomaliesData(flatAnomalies.reverse());
      } catch (err) {
        console.error("Erreur appel API Silver", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const itemsPerPage = 6;

  const erreursCritiques = anomaliesData.filter(
    (item) => item.niveau === "Critique"
  ).length;

  const avertissements = anomaliesData.filter(
    (item) => item.niveau === "Avertissement"
  ).length;

  const totalPages = Math.ceil(anomaliesData.length / itemsPerPage);

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;

  const currentItems = anomaliesData.slice(startIndex, endIndex);

  const goToPage = (page) => {
    setCurrentPage(page);
  };

  const goToPrevious = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  const goToNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">
              Anomalies détectées
            </h1>
            <p className="mt-1 text-sm text-zinc-400">
              Incohérences identifiées par l'IA (Collection Silver)
            </p>
          </div>

          {loading ? (
            <div className="text-zinc-400 text-sm">Chargement depuis la base...</div>
          ) : anomaliesData.length === 0 ? (
            <div className="text-green-400 text-sm font-semibold p-4 bg-green-900/20 border border-green-800 rounded-lg">Aucune anomalie détectée ! Tous les documents sont conformes.</div>
          ) : (
            <>
              <div className="mb-8 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <div className="flex items-center gap-3">
                
                <div>
                  <p className="text-2xl font-bold text-red-400">
                    {erreursCritiques}
                  </p>
                  <p className="text-sm text-zinc-300">Erreurs critiques</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <div className="flex items-center gap-3">
               
                <div>
                  <p className="text-2xl font-bold text-orange-400">
                    {avertissements}
                  </p>
                  <p className="text-sm text-zinc-300">Avertissements</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mb-5">
            <h2 className="text-xl font-semibold text-white">
              Liste des anomalies
            </h2>

            <div className="mt-4 flex flex-wrap gap-3">
              <button className="rounded-lg bg-zinc-700 px-3 py-2 text-sm text-white hover:bg-zinc-600">
                Toutes
              </button>
              <button className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white hover:bg-zinc-700">
                Critiques
              </button>
              <button className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white hover:bg-zinc-700">
                Avertissements
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {currentItems.map((item) => (
              <div
                key={item.id}
                className="grid gap-4 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 md:grid-cols-[1.3fr_1.3fr_1.3fr_auto_auto]"
              >
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">
                    Anomalie
                  </p>
                  <p
                    className={`font-semibold ${
                      item.niveau === "Critique"
                        ? "text-red-400"
                        : "text-orange-400"
                    }`}
                  >
                    {item.type}
                  </p>
                  <p className="mt-1 text-sm text-zinc-400">
                    {item.description}
                  </p>
                </div>

                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">
                    Document
                  </p>
                  <p className="font-medium text-white">{item.document}</p>
                  <p className="mt-1 text-sm text-zinc-400">
                    {item.comparaison}
                  </p>
                </div>

                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">
                    Détail
                  </p>
                  <p className="font-medium text-white">{item.detail}</p>
                  <p className="mt-1 text-sm text-zinc-400">{item.date}</p>
                </div>

                <div className="flex items-center">
                  <span
                    className={`inline-block rounded-md px-3 py-1 text-xs font-medium ${getBadgeClass(
                      item.niveau
                    )}`}
                  >
                    {item.niveau}
                  </span>
                </div>

                <div className="flex items-center">
                  <Link
                    to={`/entreprises/${item.entrepriseId}/dossiers/${item.dossierId}/documents/${item.documentId}`}
                    className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white transition hover:bg-zinc-700"
                  >
                    Voir le doc
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between text-sm text-zinc-400">
            <p>
              Affichage {startIndex + 1}-
              {Math.min(endIndex, anomaliesData.length)} sur {anomaliesData.length} anomalies
            </p>

            <div className="flex items-center gap-2">
              <button
                onClick={goToPrevious}
                disabled={currentPage === 1}
                className="rounded bg-zinc-800 px-3 py-1 text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                &lt;
              </button>

              {Array.from({ length: totalPages }, (_, index) => index + 1).map(
                (page) => (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`rounded px-3 py-1 text-white ${
                      currentPage === page
                        ? "bg-blue-500"
                        : "bg-zinc-800 hover:bg-zinc-700"
                    }`}
                  >
                    {page}
                  </button>
                )
              )}

              <button
                onClick={goToNext}
                disabled={currentPage === totalPages}
                className="rounded bg-zinc-800 px-3 py-1 text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                &gt;
              </button>
            </div>
          </div>
          </>)}
        </main>
      </div>
    </div>
  );
};

export default Anomalies;