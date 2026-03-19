import { Link } from "react-router-dom";

const EntrepriseCard = ({ entreprise }) => {
  const dossiers = entreprise.dossiers || [];

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 transition hover:border-zinc-700">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">
          {entreprise.denomination_sociale}
        </h3>
        <p className="mt-1 text-sm text-zinc-400">
          SIRET : {entreprise.siret}
        </p>
        <p className="mt-1 text-sm text-zinc-500">
          SIREN : {entreprise.siren}
        </p>
      </div>

      <div className="mb-4 text-sm text-zinc-400">
        <p>Nombre de dossiers : {dossiers.length}</p>
      </div>

      <Link
        to={`/entreprises/${entreprise.id}`}
        className="inline-block rounded-xl bg-zinc-800 px-4 py-2 text-sm text-white transition hover:bg-zinc-700"
      >
        Voir détail
      </Link>
    </div>
  );
};

export default EntrepriseCard;