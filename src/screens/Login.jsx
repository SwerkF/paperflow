import {useState,useContext} from "react";
import {useNavigate,Link} from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";

const Login = ()=>{
    const navigate = useNavigate();
    const {login} = useContext(AuthContext);


    const[formData,setFormData] = useState({
        email: "",
        password: "",
    });


    const [showPassword ,setShowPassword]= useState(false);
    const [loading,setLoading]= useState(false);
    const [error,setError] = useState("");

    const handleChange = (e) =>{
        setFormData((prev)=>({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };
    const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      setLoading(true);
      await login(formData);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err?.response?.data?.message ||
          "Connexion impossible. Vérifie tes identifiants."
      );
    } finally {
      setLoading(false);
    }
};
return (
  <div className="min-h-screen bg-black flex items-center justify-center px-4">
    <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-950 p-8 shadow-lg">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-white">Connexion</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Connecte-toi à ton espace PaperFlow
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="mb-2 block text-sm font-medium text-zinc-300">
            Adresse email
          </label>
          <input
            type="email"
            name="email"
            placeholder="exemple@mail.com"
            value={formData.email}
            onChange={handleChange}
            className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-white placeholder:text-zinc-500 outline-none transition focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
            required
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-zinc-300">
            Mot de passe
          </label>

          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 pr-16 text-white placeholder:text-zinc-500 outline-none transition focus:border-green-500 focus:ring-2 focus:ring-green-500/20"
              required
            />

            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-400 hover:text-green-400"
            >
              {showPassword ? "Masquer" : "Voir"}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-zinc-400">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-green-500 focus:ring-green-500"
            />
            Se souvenir de moi
          </label>

          <Link
            to="/forgot-password"
            className="text-green-400 hover:text-green-300"
          >
            Mot de passe oublié ?
          </Link>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-green-500 px-4 py-3 font-semibold text-black transition hover:bg-green-400 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-zinc-400">
        Pas encore de compte ?{" "}
        <Link
          to="/register"
          className="font-medium text-green-400 hover:text-green-300"
        >
          Créer un compte
        </Link>
      </p>
    </div>
  </div>
);
};

export default Login;