import { Link } from "react-router-dom";
const statusStyles = {
  valide: "border-green-500/40",
  anomalie: "border-red-500/40",
  en_cours: "border-blue-500/40",
};

const statusLabels = {
  valide: "Validé",
  anomalie: "Anomalie",
  en_cours: "En cours",
};

const badgeStyles = {
  valide: "bg-green-500/20 text-green-400",
  anomalie: "bg-red-500/20 text-red-400",
  en_cours: "bg-blue-500/20 text-blue-400",
};

const DossierCard = ({ dossier, entrepriseId }) => {
  return (
    <Link
      to={`/entreprises/${entrepriseId}/dossiers/${dossier.id}/upload`}
      className={`block rounded-2xl border bg-zinc-900 p-4 transition hover:-translate-y-0.5 hover:bg-zinc-800 ${
        statusStyles[dossier.statut] || "border-zinc-700"
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="text-2xl">📁</div>
        <span
          className={`rounded-lg px-2 py-1 text-xs font-medium ${
            badgeStyles[dossier.statut]
          }`}
        >
          {statusLabels[dossier.statut]}
        </span>
      </div>

      <h3 className="text-base font-semibold text-white">{dossier.titre}</h3>
      <p className="mt-1 text-sm text-zinc-400">{dossier.description}</p>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-zinc-300">{dossier.documents} documents</span>
        <span className="text-zinc-500">{dossier.date}</span>
      </div>
    </Link>
  );
};

export default DossierCard;