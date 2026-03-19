import api from "./api";

export const loginUser = async ({ email, password }) => {
  const response = await api.post(
    `/users/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
  );
  return response.data;
};

export const getAllUsers = async () => {
  const response = await api.get("/users");
  return response.data;
};

export const getMe = async () => {
  const response = await api.get("/users/me");
  return response.data;
};

export const updateProfile = async (data) => {
  const response = await api.put("/users/UpdateProfile", data);
  return response.data;
};

export const deleteProfile = async () => {
  const response = await api.delete("/users/deleteProfile");
  return response.data;
};