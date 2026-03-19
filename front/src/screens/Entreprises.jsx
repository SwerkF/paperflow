import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import EntrepriseCard from "../components/EntrepriseCard";
import {
  createEntreprise,
  getEntreprises,
} from "../services/entreprise.service";

const Entreprises = () => {
  const [entreprises, setEntreprises] = useState([]);
  const [loadingEntreprises, setLoadingEntreprises] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    siret: "",
    siren: "",
    denomination_sociale: "",
    forme_juridique: "",
    adresse_siege: "",
  });

  const loadEntreprises = async () => {
    try {
      setLoadingEntreprises(true);
      const data = await getEntreprises();
      setEntreprises(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Erreur chargement entreprises :", err);
      setError("Impossible de charger les entreprises.");
    } finally {
      setLoadingEntreprises(false);
    }
  };

  useEffect(() => {
    loadEntreprises();
  }, []);

  const openModal = () => {
    setIsModalOpen(true);
    setError("");
    setSuccessMessage("");
  };

  const closeModal = () => {
    if (loadingCreate) return;

    setIsModalOpen(false);
    setError("");
    setFormData({
      siret: "",
      siren: "",
      denomination_sociale: "",
      forme_juridique: "",
      adresse_siege: "",
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

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

  const handleCreateEntreprise = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (
      !formData.siret.trim() ||
      !formData.siren.trim() ||
      !formData.denomination_sociale.trim()
    ) {
      setError("Le SIRET, le SIREN et la dénomination sociale sont obligatoires.");
      return;
    }

    try {
      setLoadingCreate(true);

      // IMPORTANT :
      // On envoie seulement les champs que le backend accepte dans EntrepriseCreate
      const payload = {
        siret: formData.siret.trim(),
        siren: formData.siren.trim(),
        denomination_sociale: formData.denomination_sociale.trim(),
      };

      const data = await createEntreprise(payload);
      console.log("Entreprise créée :", data);

      setSuccessMessage("Entreprise créée avec succès.");
      closeModal();
      await loadEntreprises();
    } catch (err) {
      console.error("Erreur création entreprise :", err);
      setError(
        formatBackendError(
          err,
          "Erreur lors de la création de l’entreprise."
        )
      );
    } finally {
      setLoadingCreate(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Entreprises</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Liste des entreprises suivies
              </p>
            </div>

            <button
              onClick={openModal}
              className="rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700"
            >
              + Nouvelle entreprise
            </button>
          </div>

          {successMessage && (
            <div className="mb-6 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-green-300">
              {successMessage}
            </div>
          )}

          {error && !isModalOpen && (
            <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {loadingEntreprises ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Chargement des entreprises...
            </div>
          ) : entreprises.length === 0 ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              Aucune entreprise disponible.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {entreprises.map((entreprise) => (
                <EntrepriseCard
                  key={entreprise.id}
                  entreprise={entreprise}
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
                  Nouvelle entreprise
                </h3>
                <p className="mt-1 text-sm text-zinc-400">
                  Renseigne les informations de l’entreprise
                </p>
              </div>

              <button
                onClick={closeModal}
                className="text-sm text-zinc-400 transition hover:text-white"
              >
                Fermer
              </button>
            </div>

            <form onSubmit={handleCreateEntreprise} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  SIRET
                </label>
                <input
                  type="text"
                  name="siret"
                  value={formData.siret}
                  onChange={handleChange}
                  placeholder="Ex: 12345678900012"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  SIREN
                </label>
                <input
                  type="text"
                  name="siren"
                  value={formData.siren}
                  onChange={handleChange}
                  placeholder="Ex: 123456789"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Dénomination sociale
                </label>
                <input
                  type="text"
                  name="denomination_sociale"
                  value={formData.denomination_sociale}
                  onChange={handleChange}
                  placeholder="Ex: PaperFlow SAS"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Forme juridique
                </label>
                <input
                  type="text"
                  name="forme_juridique"
                  value={formData.forme_juridique}
                  onChange={handleChange}
                  placeholder="Ex: SAS, SARL, EURL..."
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Adresse du siège
                </label>
                <input
                  type="text"
                  name="adresse_siege"
                  value={formData.adresse_siege}
                  onChange={handleChange}
                  placeholder="Ex: 10 rue de Paris, 75001 Paris"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white outline-none transition placeholder:text-zinc-500 focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
                />
              </div>

              <p className="text-xs text-zinc-500">
                Les champs “forme juridique” et “adresse du siège” sont affichés
                dans l’interface, mais ne sont pas envoyés à l’API car le backend
                actuel ne les accepte pas à la création.
              </p>

              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {error}
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

export default Entreprises;