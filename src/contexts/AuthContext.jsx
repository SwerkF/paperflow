import { createContext, useState } from "react";
import { loginUser } from "../services/user.service";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const isExpired = Date.now() / 1000 > payload.exp;

      if (isExpired) {
        localStorage.removeItem("token");
        return null;
      }

      return payload;
    } catch {
      localStorage.removeItem("token");
      return null;
    }
  });

  const login = async (formData) => {
    const data = await loginUser(formData);
    localStorage.setItem("token", data.token);

    try {
      const payload = JSON.parse(atob(data.token.split(".")[1]));
      setUser(payload);
    } catch {
      setUser(data.user || null);
    }

    return data;
  };



  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};