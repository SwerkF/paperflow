import Sidebar from "../components/Sidebar";

const Profil_user = () => {
  const user = {
    nom: "Dupont",
    prenom: "Jean",
    email: "jean.dupont@paperflow.fr",
    role: "Opérateur documentaire",
    telephone: "+33 6 12 34 56 78",
    entreprise: "PaperFlow",
    dateInscription: "12/02/2024",
  };

  const stats = [
    { label: "Documents traités", value: 248 },
    { label: "Dossiers créés", value: 19 },
    { label: "Anomalies détectées", value: 7 },
    { label: "Score OCR moyen", value: "92%" },
  ];

  const activites = [
    "Upload de facture_acme_2024_03.pdf",
    "Consultation du dossier Mars 2024",
    "Vérification d’une anomalie SIRET",
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex">
        <Sidebar />

        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">Mon profil</h1>
            <p className="mt-1 text-sm text-zinc-400">
              Informations personnelles et aperçu de l’activité
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
            {/* Carte profil */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
              <div className="flex flex-col items-center text-center">
                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-green-500 text-3xl font-bold text-black">
                  JD
                </div>

                <h2 className="mt-4 text-xl font-semibold text-white">
                  {user.prenom} {user.nom}
                </h2>

                <p className="mt-1 text-sm text-zinc-400">{user.role}</p>
                <p className="mt-1 text-sm text-zinc-500">{user.email}</p>

                <button className="mt-5 rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700">
                  Modifier le profil
                </button>
              </div>

              <div className="mt-6 border-t border-zinc-800 pt-4 text-sm">
                <div className="mb-3 flex justify-between gap-4">
                  <span className="text-zinc-400">Téléphone</span>
                  <span className="text-white">{user.telephone}</span>
                </div>

                <div className="mb-3 flex justify-between gap-4">
                  <span className="text-zinc-400">Entreprise</span>
                  <span className="text-white">{user.entreprise}</span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-zinc-400">Inscrit depuis</span>
                  <span className="text-white">{user.dateInscription}</span>
                </div>
              </div>
            </div>

            {/* Partie droite */}
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {stats.map((stat, index) => (
                  <div
                    key={index}
                    className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5"
                  >
                    <p className="text-sm text-zinc-400">{stat.label}</p>
                    <p className="mt-2 text-2xl font-bold text-green-400">
                      {stat.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Infos détaillées */}
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Informations du compte
                </h2>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Prénom</p>
                    <p className="mt-1 font-medium text-white">{user.prenom}</p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Nom</p>
                    <p className="mt-1 font-medium text-white">{user.nom}</p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Email</p>
                    <p className="mt-1 font-medium text-white">{user.email}</p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Rôle</p>
                    <p className="mt-1 font-medium text-white">{user.role}</p>
                  </div>
                </div>
              </div>

              {/* Activité récente */}
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Activité récente
                </h2>

                <div className="space-y-3">
                  {activites.map((item, index) => (
                    <div
                      key={index}
                      className="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-300"
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Profil_user;