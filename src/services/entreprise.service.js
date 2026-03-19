import api from "./api";

export const createEntreprise = async (data) => {
  const response = await api.post("/entreprises/", data);
  return response.data;
};

export const getEntreprises = async () => {
  const response = await api.get("/entreprises/");
  return response.data;
};

export const getEntrepriseById = async (entrepriseId) => {
  const response = await api.get(`/entreprises/${entrepriseId}`);
  return response.data;
};

export const getEntrepriseDossiers = async (entrepriseId) => {
  const response = await api.get(`/entreprises/${entrepriseId}/dossiers`);
  return response.data;
};