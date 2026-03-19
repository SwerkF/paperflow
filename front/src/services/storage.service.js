import api from "./api";

export const getSilverDocuments = async () => {
  const { data } = await api.get("/storage/silver");
  return data;
};

export const getSilverDocument = async (docId) => {
  const { data } = await api.get(`/storage/silver/${docId}`);
  return data;
};

export const getSilverDocumentImage = async (docId) => {
  const { data } = await api.get(`/storage/silver/${docId}/image`);
  return data;
};

export const validateSilverDocument = async (docId) => {
  const { data } = await api.patch(`/storage/silver/${docId}/validate`);
  return data;
};

export const getGoldDocuments = async () => {
  const { data } = await api.get("/storage/gold");
  return data;
};
