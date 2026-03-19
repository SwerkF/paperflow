import api from "./api";

export const uploadFiles = async (formData) => {
  const response = await api.post("/upload/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};