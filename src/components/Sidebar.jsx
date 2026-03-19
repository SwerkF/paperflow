import {Link,useLocation,useNavigate} from "react-router-dom";


const Sidebar =() =>{
    const location = useLocation();
    const navItems =[
        {label: "Entreprises",path:"/entreprises"},
        {label:"Historique des uploads", path:"/uploads"},
        {label: "Anomalies",path:"/anomalies"},
    ];

    const navigate = useNavigate();

            const handleLogout = () => {

            localStorage.removeItem("token");

            navigate("/login");
            };

    const isActive = (path)=> location.pathname.startsWith(path);
   
   return (
    <aside className="flex min-h-screen w-64 flex-col justify-between border-r border-zinc-800 bg-zinc-950 px-4 py-6">
      <div>
        <div className="mb-8 px-2">
          <h1 className="text-2xl font-bold text-white">PaperFlow</h1>
          <p className="mt-1 text-sm text-zinc-400">Gestion documentaire</p>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`block rounded-xl px-4 py-3 text-sm transition ${
                isActive(item.path)
                  ? "bg-green-500 text-black font-semibold"
                  : "text-zinc-300 hover:bg-zinc-900 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

                <div className="border-t border-zinc-800 pt-4 space-y-2">
            
                    <Link
                        to="/profil"
                        className="flex items-center gap-3 rounded-xl px-3 py-3 transition hover:bg-zinc-900"
                         >
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500 font-bold text-black">
                        M
                        </div>
                        <div>
                        <p className="text-sm font-medium text-white">Mon profil</p>
                        <p className="text-xs text-zinc-400">Voir mon espace</p>
                        </div>
                    </Link>

                            <button
                                onClick={handleLogout}
                                className="w-full rounded-xl px-3 py-3 text-left text-sm text-red-400 transition hover:bg-red-500/10"
                            >
                                Se déconnecter
                            </button>

            </div>
    </aside>
  );
};

export default Sidebar;