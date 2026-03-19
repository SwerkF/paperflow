import api from "./api";

export const createDossier = async (payload) => {
  const response = await api.post("/dossiers/", payload);
  return response.data;
};

export const getDossiersByEntreprise = async (entrepriseId) => {
  const response = await api.get(`/dossiers/entreprise/${entrepriseId}`);
  return response.data;
};

export const getDossierById = async (dossierId) => {
  const response = await api.get(`/dossiers/${dossierId}`);
  return response.data;
};