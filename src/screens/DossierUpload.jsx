import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getEntrepriseById } from "../services/entreprise.service";
import { getDossierById } from "../services/dossier.service";
import { uploadFiles } from "../services/upload";

const DossierUpload = () => {
  const { id, dossierId } = useParams();
  const inputRef = useRef(null);

  const [entreprise, setEntreprise] = useState(null);
  const [dossier, setDossier] = useState(null);

  const [loadingPage, setLoadingPage] = useState(true);
  const [pageError, setPageError] = useState("");

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);

  const formatBackendError = (error, fallback) => {
    const detail = error?.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          const field = item?.loc?.[item.loc.length - 1];
          return field ? `${field} : ${item.msg}` : item.msg;
        })
        .join(" | ");
    }

    if (typeof detail === "string") {
      return detail;
    }

    return fallback;
  };

  const loadPageData = async () => {
    try {
      setLoadingPage(true);
      setPageError("");

      const [entrepriseData, dossierData] = await Promise.all([
        getEntrepriseById(id),
        getDossierById(dossierId),
      ]);

      setEntreprise(entrepriseData);
      setDossier(dossierData);
    } catch (error) {
      console.error("Erreur chargement page upload :", error);
      setPageError(
        formatBackendError(error, "Impossible de charger le dossier.")
      );
    } finally {
      setLoadingPage(false);
    }
  };

  useEffect(() => {
    if (!id || !dossierId) return;
    loadPageData();
  }, [id, dossierId]);

  const addFiles = (newFiles) => {
    if (!newFiles || newFiles.length === 0) return;

    const validFiles = newFiles.filter(
      (file) =>
        file.type === "application/pdf" ||
        file.type === "image/jpeg" ||
        file.type === "image/png" ||
        file.name.toLowerCase().endsWith(".pdf") ||
        file.name.toLowerCase().endsWith(".jpg") ||
        file.name.toLowerCase().endsWith(".jpeg") ||
        file.name.toLowerCase().endsWith(".png")
    );

    setSelectedFiles((prevFiles) => {
      const mergedFiles = [...prevFiles, ...validFiles];

      return mergedFiles.filter(
        (file, index, self) =>
          index ===
          self.findIndex(
            (f) =>
              f.name === file.name &&
              f.size === file.size &&
              f.lastModified === file.lastModified
          )
      );
    });

    setMessage("");
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    addFiles(files);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);

    const files = Array.from(e.dataTransfer.files || []);
    addFiles(files);
  };

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((prevFiles) =>
      prevFiles.filter((_, index) => index !== indexToRemove)
    );
  };

  const handleAnalyse = async () => {
    if (selectedFiles.length === 0) {
      setMessage("Ajoute au moins un fichier.");
      return;
    }

    try {
      setIsUploading(true);
      setMessage("Envoi en cours...");

      const formData = new FormData();

      // IMPORTANT :
      // On envoie exactement les noms attendus par le backend.
      formData.append("dossierId", dossierId);
      formData.append("entrepriseId", id);

      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });

      const data = await uploadFiles(formData);

      setMessage(
        data?.message
          ? `${data.message} (${data.count || 0} fichier(s))`
          : "Upload réussi."
      );
      setSelectedFiles([]);
    } catch (error) {
      console.error("Erreur upload :", error);

      const backendMessage = formatBackendError(
        error,
        "Erreur pendant l’envoi."
      );

      // petit message plus honnête vu ton backend actuel
      if (
        backendMessage.toLowerCase().includes("dossierid") ||
        backendMessage.toLowerCase().includes("entrepriseid") ||
        error?.response?.status === 422
      ) {
        setMessage(
          `${backendMessage} — Le backend semble attendre des IDs numériques alors que l’application utilise des IDs Mongo.`
        );
      } else {
        setMessage(backendMessage);
      }
    } finally {
      setIsUploading(false);
    }
  };

  if (loadingPage) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Chargement du dossier...
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (pageError || !entreprise || !dossier) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6">
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-300">
              {pageError || "Dossier introuvable"}
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <div className="mb-4 flex items-center gap-2 text-sm text-zinc-500">
            <Link to="/entreprises" className="hover:text-white">
              Entreprises
            </Link>
            <span>&gt;</span>
            <Link to={`/entreprises/${entreprise.id}`} className="hover:text-white">
              {entreprise.denomination_sociale || "Entreprise"}
            </Link>
            <span>&gt;</span>
            <span className="text-zinc-300">{dossier.nom}</span>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">{dossier.nom}</h1>
            <p className="mt-1 text-sm text-zinc-400">
              Dépose ici les documents du dossier
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <div className="grid gap-6">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
                  isDragActive
                    ? "border-green-400 bg-green-500/20"
                    : "border-green-500/30 bg-green-500/10 hover:bg-green-500/15"
                }`}
              >
                <p className="text-base font-medium text-white">
                  Glisse-dépose tes fichiers ici
                </p>
                <p className="mt-2 text-sm text-zinc-400">
                  ou clique pour sélectionner plusieurs documents
                </p>
                <p className="mt-2 text-xs text-zinc-500">
                  Formats acceptés : PDF, JPG, JPEG, PNG
                </p>

                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf,image/png,image/jpeg"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                />

                <button
                  type="button"
                  className="mt-5 rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    inputRef.current?.click();
                  }}
                >
                  Choisir des fichiers
                </button>
              </div>

              {selectedFiles.length > 0 && (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
                  <h3 className="mb-4 text-sm font-semibold text-white">
                    Fichiers sélectionnés
                  </h3>

                  <div className="space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={`${file.name}-${file.size}-${file.lastModified}`}
                        className="flex items-center justify-between rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-300"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-white">{file.name}</p>
                          <p className="text-xs text-zinc-500">
                            {(file.size / 1024 / 1024).toFixed(2)} Mo
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleRemoveFile(index)}
                          className="ml-3 shrink-0 text-red-400 transition hover:text-red-300"
                        >
                          Supprimer
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-2xl border border-green-500/20 bg-green-500/10 p-4">
                <p className="text-sm text-zinc-300">
                  Nombre total de fichiers ajoutés :{" "}
                  <span className="font-semibold text-white">
                    {selectedFiles.length}
                  </span>
                </p>
              </div>

              <div>
                <button
                  onClick={handleAnalyse}
                  disabled={isUploading}
                  className="rounded-xl bg-green-500 px-5 py-2.5 text-sm font-medium text-black transition hover:bg-green-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isUploading ? "Envoi..." : "Analyser"}
                </button>
              </div>

              {message && (
                <div className="rounded-xl bg-zinc-800 px-4 py-3 text-sm text-zinc-300">
                  {message}
                </div>
              )}
            </div>
          </div>

          <div className="mt-8">
            <h2 className="mb-4 text-xl font-semibold text-white">
              Documents récents
            </h2>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Aucun endpoint de listing des documents n’a été fourni ici, donc
              cette section reste en attente de branchement backend.
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DossierUpload;