import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getSilverDocument, getSilverDocumentImage, validateSilverDocument } from "../services/storage.service";

const DocumentDetails = () => {
  const { id, dossierId, documentId } = useParams();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState(null);
  const [imageSrc, setImageSrc] = useState(null);
  const [imageType, setImageType] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        setLoading(true);
        const docData = await getSilverDocument(documentId);
        setDocument(docData);
        
        try {
          const imgData = await getSilverDocumentImage(documentId);
          if (imgData.file_data) {
            setImageSrc(`data:${imgData.content_type || 'image/jpeg'};base64,${imgData.file_data}`);
            setImageType(imgData.content_type || 'image/jpeg');
          }
        } catch (imgErr) {
          console.warn("Pas d'image trouvée pour ce doc", imgErr);
        }
      } catch (err) {
        console.error("Erreur chargement document", err);
      } finally {
        setLoading(false);
      }
    };
    if (documentId) fetchDoc();
  }, [documentId]);

  const handleValidate = async () => {
    try {
      setValidating(true);
      await validateSilverDocument(documentId);
      navigate("/anomalies");
    } catch (err) {
      console.error("Erreur validation", err);
      alert("Erreur lors de la validation");
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex">
        <Sidebar />
        <main className="flex-1 p-6 text-zinc-400">Chargement du document...</main>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-black text-white flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <h2 className="text-2xl font-bold">Document introuvable (API)</h2>
        </main>
      </div>
    );
  }

  const isAnomalie = document.status === "EN_ATTENTE_SUPERVISION";
  const extraction = document.extracted_fields || {};

  return (
    <div className="min-h-screen bg-black text-white flex">
      <Sidebar />

      <main className="flex-1 p-6">
        <div className="mb-4 flex items-center gap-2 text-sm text-zinc-500">
          <Link to="/entreprises" className="hover:text-white">
            Entreprises
          </Link>
          <span>&gt;</span>
          <Link to={`/entreprises/${id}`} className="hover:text-white">
            ID: {id}
          </Link>
          <span>&gt;</span>
          <Link
            to={`/entreprises/${id}/dossiers/${dossierId}/upload`}
            className="hover:text-white"
          >
            Dossier {dossierId}
          </Link>
          <span>&gt;</span>
          <span className="text-zinc-300">{document.filename}</span>
        </div>

        <div className="mb-6 flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white hover:bg-zinc-700"
          >
            ← Retour
          </button>

          <span
            className={`rounded-md px-2 py-1 text-xs font-medium ${
              document.status === "VALIDE"
                ? "bg-green-500/20 text-green-400"
                : isAnomalie
                ? "bg-orange-500/20 text-orange-400"
                : "bg-yellow-500/20 text-yellow-400"
            }`}
          >
            {document.status}
          </span>

          <span className="rounded-md bg-blue-500/20 px-2 py-1 text-xs font-medium text-blue-400 uppercase">
            {document.document_type || "INCONNU"}
          </span>

          {isAnomalie && (
            <button
              onClick={handleValidate}
              disabled={validating}
              className="ml-auto rounded-lg bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-500 disabled:opacity-50"
            >
              {validating ? "Validation..." : "Forcer la Validation"}
            </button>
          )}
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 flex flex-col">
            <h2 className="mb-4 text-lg font-semibold text-white">
              Aperçu du document
            </h2>
            <div className="flex-1 rounded-xl bg-zinc-950 p-2 overflow-auto flex items-center justify-center min-h-[500px]">
              {imageSrc ? (
                imageType === "application/pdf" ? (
                  <object
                    data={imageSrc}
                    type="application/pdf"
                    className="h-full w-full rounded-md"
                  >
                    <p className="text-zinc-500">Aperçu PDF non supporté par votre navigateur.</p>
                  </object>
                ) : (
                  <img src={imageSrc} alt="Document uploadé" className="max-h-full max-w-full rounded-md object-contain" />
                )
              ) : (
                <p className="text-zinc-500 text-sm">Image non disponible dans la base.</p>
              )}
            </div>
          </div>

          <div className="space-y-5">


            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Données d'identification extraites
              </h2>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Entreprise (Nom)</span>
                  <span className="text-white">{extraction.company?.nom || "--"}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">SIRET/SIREN Entreprise</span>
                  <span className="text-green-400 font-semibold">{extraction.company?.siret || "--"}</span>
                </div>
                
                {extraction.date_facture && (
                  <div className="flex justify-between gap-4 mt-2">
                    <span className="text-zinc-400">Date du Document</span>
                    <span className="text-white">{extraction.date_facture}</span>
                  </div>
                )}
                {extraction.date_expiration && (
                  <div className="flex justify-between gap-4 mt-2">
                    <span className="text-zinc-400">Date d'Expiration</span>
                    <span className="text-white bg-orange-500/10 px-2 py-0.5 rounded text-orange-300 font-medium">{extraction.date_expiration}</span>
                  </div>
                )}
                
                {extraction.client && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <div className="flex justify-between gap-4 py-1">
                      <span className="text-zinc-400">Client (Nom)</span>
                      <span className="text-white">{extraction.client?.nom || "--"}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-zinc-400">SIRET/SIREN Client</span>
                      <span className="text-green-400 font-semibold">{extraction.client?.siret || "--"}</span>
                    </div>
                  </div>
                )}

                {(extraction.montant_ht || extraction.montant_ttc) && (
                   <div className="mt-4 pt-4 border-t border-zinc-800">
                     <div className="flex justify-between gap-4 py-1">
                       <span className="text-zinc-400">Montant HT</span>
                       <span className="text-white">{extraction.montant_ht || "--"}</span>
                     </div>
                     <div className="flex justify-between gap-4 py-1">
                       <span className="text-zinc-400">TVA Calculée</span>
                       <span className="text-green-400">{extraction.tva ? (extraction.tva * 100).toFixed(1) + "%" : "--"}</span>
                     </div>
                     <div className="flex justify-between gap-4 py-1">
                       <span className="text-zinc-400">Montant TTC</span>
                       <span className="text-white font-semibold">{extraction.montant_ttc || "--"}</span>
                     </div>
                   </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Rapport de conformité
              </h2>

              <div className="space-y-3 text-sm">
                {document.alertes && document.alertes.length > 0 ? (
                  document.alertes.map((item, index) => (
                    <div key={index} className="flex items-start justify-between gap-4 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <span className="text-red-300 font-semibold flex-shrink-0">Refusé</span>
                      <span className="text-zinc-300 text-right">{item.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center justify-between p-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <span className="text-zinc-300">Aucune anomalie signalée par l'IA.</span>
                    <span className="text-green-400 font-semibold">OK</span>
                  </div>
                )}
              </div>
            </div>
            
          </div>
        </div>
      </main>
    </div>
  );
};

export default DocumentDetails;