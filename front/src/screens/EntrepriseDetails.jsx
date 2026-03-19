import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import DossierCard from "../components/DossierCard";
import { getEntrepriseById } from "../services/entreprise.service";
import {
  createDossier,
  getDossiersByEntreprise,
} from "../services/dossier.service";

const EntrepriseDetails = () => {
  const { id } = useParams();

  const [entreprise, setEntreprise] = useState(null);
  const [dossiers, setDossiers] = useState([]);

  const [loadingEntreprise, setLoadingEntreprise] = useState(true);
  const [loadingDossiers, setLoadingDossiers] = useState(true);
  const [pageError, setPageError] = useState("");

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [modalError, setModalError] = useState("");

  const [formData, setFormData] = useState({
    nom: "",
    created_by: "admin",
  });

  const formatBackendError = (err, fallback) => {
    const detail = err?.response?.data?.detail;

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

  const loadEntreprise = async () => {
    try {
      setLoadingEntreprise(true);
      setPageError("");

      const data = await getEntrepriseById(id);
      setEntreprise(data);
    } catch (err) {
      console.error("Erreur chargement entreprise :", err);
      setPageError(
        formatBackendError(err, "Impossible de charger l’entreprise.")
      );
    } finally {
      setLoadingEntreprise(false);
    }
  };

  const loadDossiers = async () => {
    try {
      setLoadingDossiers(true);

      const data = await getDossiersByEntreprise(id);
      setDossiers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Erreur chargement dossiers :", err);
      setDossiers([]);
    } finally {
      setLoadingDossiers(false);
    }
  };

  useEffect(() => {
    if (!id) return;

    loadEntreprise();
    loadDossiers();
  }, [id]);

  const openModal = () => {
    setModalError("");
    setFormData({
      nom: "",
      created_by: "admin",
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    if (loadingCreate) return;
    setIsModalOpen(false);
    setModalError("");
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCreateDossier = async (e) => {
    e.preventDefault();
    setModalError("");

    if (!formData.nom.trim()) {
      setModalError("Le nom du dossier est obligatoire.");
      return;
    }

    try {
      setLoadingCreate(true);

      const payload = {
        entreprise_id: id,
        nom: formData.nom.trim(),
        created_by: formData.created_by.trim() || "admin",
      };

      const created = await createDossier(payload);
      console.log("Dossier créé :", created);

      closeModal();
      await loadEntreprise();
      await loadDossiers();
    } catch (err) {
      console.error("Erreur création dossier :", err);
      setModalError(
        formatBackendError(err, "Impossible de créer le dossier.")
      );
    } finally {
      setLoadingCreate(false);
    }
  };

  if (loadingEntreprise) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Chargement de l’entreprise...
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (pageError || !entreprise) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6">
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-300">
              {pageError || "Entreprise introuvable"}
            </div>
          </main>
        </div>
      </div>
    );
  }

  const sigle =
    entreprise.denomination_sociale
      ?.split(" ")
      .slice(0, 2)
      .map((word) => word[0])
      .join("")
      .toUpperCase() || "EN";

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <p className="mb-4 text-sm text-zinc-500">
            <Link to="/entreprises" className="hover:text-white">
              Entreprises
            </Link>{" "}
            &gt;{" "}
            <span className="text-zinc-300">
              {entreprise.denomination_sociale || "Entreprise"}
            </span>
          </p>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-zinc-700 text-lg font-bold text-white">
                  {sigle}
                </div>

                <div>
                  <h1 className="text-2xl font-bold text-white">
                    {entreprise.denomination_sociale || "Sans nom"}
                  </h1>

                  {entreprise.siret && (
                    <p className="text-sm text-zinc-400">
                      SIRET {entreprise.siret}
                    </p>
                  )}

                  {entreprise.siren && (
                    <p className="text-sm text-zinc-400">
                      SIREN {entreprise.siren}
                    </p>
                  )}

                  {entreprise.forme_juridique && (
                    <p className="text-sm text-zinc-400">
                      Forme juridique : {entreprise.forme_juridique}
                    </p>
                  )}

                  {entreprise.adresse_siege && (
                    <p className="text-sm text-zinc-500">
                      {entreprise.adresse_siege}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex gap-6">
                <div>
                  <p className="text-center text-xl font-bold text-white">
                    {dossiers.length}
                  </p>
                  <p className="text-xs text-zinc-400">Dossiers</p>
                </div>

                <div>
                  <p className="text-center text-xl font-bold text-white">0</p>
                  <p className="text-xs text-zinc-400">Documents</p>
                </div>

                <div>
                  <p className="text-center text-xl font-bold text-white">0</p>
                  <p className="text-xs text-zinc-400">Anomalies</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mb-4 mt-8 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Dossiers</h2>
              <p className="text-sm text-zinc-400">
                Dossiers liés à cette entreprise
              </p>
            </div>

            <button
              onClick={openModal}
              className="rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700"
            >
              + Nouveau dossier
            </button>
          </div>

          {loadingDossiers ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Chargement des dossiers...
            </div>
          ) : dossiers.length === 0 ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Aucun dossier à afficher pour le moment.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {dossiers.map((dossier) => (
                <DossierCard
                  key={dossier.id}
                  dossier={dossier}
                  entrepriseId={entreprise.id}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">
                  Nouveau dossier
                </h3>
                <p className="mt-1 text-sm text-zinc-400">
                  Ajoute un dossier à cette entreprise
                </p>
              </div>

              <button
                onClick={closeModal}
                className="text-sm text-zinc-400 transition hover:text-white"
              >
                Fermer
              </button>
            </div>

            <form onSubmit={handleCreateDossier} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Nom du dossier
                </label>
                <input
                  type="text"
                  name="nom"
                  value={formData.nom}
                  onChange={handleChange}
                  placeholder="Ex: Dossier fiscal 2026"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Créé par
                </label>
                <input
                  type="text"
                  name="created_by"
                  value={formData.created_by}
                  onChange={handleChange}
                  placeholder="Ex: admin"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                  required
                />
              </div>

              {modalError && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {modalError}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700"
                >
                  Annuler
                </button>

                <button
                  type="submit"
                  disabled={loadingCreate}
                  className="rounded-xl bg-green-500 px-4 py-2 text-sm font-semibold text-black transition hover:bg-green-400 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loadingCreate ? "Création..." : "Créer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EntrepriseDetails;