import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";

const Conformite = () => {
  const checks = [
    { label: "SIRET valide", value: "OK", status: "ok" },
    { label: "TVA cohérente", value: "OK", status: "ok" },
    { label: "Attestation non expirée", value: "OK", status: "ok" },
    { label: "KBIS présent", value: "OK", status: "ok" },
    { label: "RIB disponible", value: "À vérifier", status: "warning" },
  ];

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
            <span className="text-zinc-300">Outil conformité</span>
          </div>

          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Outil conformité
              </h1>
              <p className="mt-1 text-sm text-zinc-400">
                Contrôle automatique des pièces et de leur cohérence
              </p>
            </div>

            <span className="rounded-xl bg-green-500/20 px-4 py-2 text-sm font-medium text-green-400">
              Conforme
            </span>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
              <h2 className="mb-4 text-lg font-semibold text-white">
                Résultat des contrôles
              </h2>

              <div className="space-y-3">
                {checks.map((check, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-xl bg-zinc-950 px-4 py-4"
                  >
                    <span className="text-zinc-300">{check.label}</span>
                    <span
                      className={
                        check.status === "ok"
                          ? "font-medium text-green-400"
                          : "font-medium text-yellow-400"
                      }
                    >
                      {check.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Synthèse
                </h2>

                <div className="space-y-4">
                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Entreprise</p>
                    <p className="mt-1 font-medium text-white">ACME SAS</p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Niveau de risque</p>
                    <p className="mt-1 font-medium text-yellow-400">Faible</p>
                  </div>

                  <div className="rounded-xl bg-zinc-950 p-4">
                    <p className="text-sm text-zinc-400">Décision</p>
                    <p className="mt-1 font-medium text-green-400">
                      Validation possible
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <h2 className="mb-4 text-lg font-semibold text-white">
                  Commentaire
                </h2>

                <p className="rounded-xl bg-zinc-950 px-4 py-4 text-sm text-zinc-300">
                  Les documents principaux sont cohérents. Un contrôle manuel du
                  RIB peut être effectué avant validation finale.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Conformite;