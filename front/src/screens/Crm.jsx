import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";

const Crm = () => {
  const fournisseur = {
    raisonSociale: "ACME SAS",
    siret: "83241567800012",
    tva: "FR83241567800",
    adresse: "12 Rue de la Paix, 75001 Paris",
    email: "contact@acme.fr",
    telephone: "+33 1 45 67 89 10",
    contact: "Jean Dupont",
    statut: "Actif",
    categorie: "Fournisseur stratégique",
  };

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
            <span className="text-zinc-300">CRM</span>
          </div>

          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">CRM fournisseur</h1>
              <p className="mt-1 text-sm text-zinc-400">
                Fiche fournisseur pré-remplie après analyse documentaire
              </p>
            </div>

            <button className="rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white hover:bg-zinc-700">
              Enregistrer
            </button>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Informations fournisseur
              </h2>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">Raison sociale</p>
                  <p className="mt-1 font-medium text-white">
                    {fournisseur.raisonSociale}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">SIRET</p>
                  <p className="mt-1 font-medium text-green-400">
                    {fournisseur.siret}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">N° TVA</p>
                  <p className="mt-1 font-medium text-green-400">
                    {fournisseur.tva}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">Contact</p>
                  <p className="mt-1 font-medium text-white">
                    {fournisseur.contact}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4 sm:col-span-2">
                  <p className="text-sm text-zinc-400">Adresse</p>
                  <p className="mt-1 font-medium text-white">
                    {fournisseur.adresse}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">Email</p>
                  <p className="mt-1 font-medium text-white">
                    {fournisseur.email}
                  </p>
                </div>

                <div className="rounded-xl bg-zinc-950 p-4">
                  <p className="text-sm text-zinc-400">Téléphone</p>
                  <p className="mt-1 font-medium text-white">
                    {fournisseur.telephone}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Statut CRM
                </h2>

                <div className="space-y-4">
                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Statut fournisseur</p>
                    <p className="mt-1 font-medium text-green-400">
                      {fournisseur.statut}
                    </p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Catégorie</p>
                    <p className="mt-1 font-medium text-white">
                      {fournisseur.categorie}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Source des données
                </h2>

                <div className="space-y-3 text-sm text-zinc-300">
                  <p className="rounded-xl bg-zinc-950 px-4 py-3">
                    Données extraites depuis la facture fournisseur
                  </p>
                  <p className="rounded-xl bg-zinc-950 px-4 py-3">
                    Vérification croisée avec l’attestation et le KBIS
                  </p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Crm;