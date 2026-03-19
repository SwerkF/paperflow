import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./screens/Login";
import Entreprises from "./screens/Entreprises";
import EntrepriseDetails from "./screens/EntrepriseDetails";
import HistoriqueUploads from "./screens/HistoriqueUploads";
import Anomalies from "./screens/Anomalies";
import Profil_user from "./screens/Profile_user";
import DossierUpload from "./screens/DossierUpload";
import DocumentDetails from "./screens/DocumentDetails";
import Crm from "./screens/Crm"
const Router = () => {
    return (
    <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
         <Route
          path="/login"
          element={
          
              <Login/>
         
          }
        />
        <Route path="/entreprises" element={<Entreprises />} />
          <Route path="/crm" element={<Crm/>} />
      <Route path="/entreprises/:id" element={<EntrepriseDetails />} />
      <Route path="/profil" element={<Profil_user />} />
      <Route path="/uploads" element={<HistoriqueUploads />} />
      <Route path="/anomalies" element={<Anomalies />} />
            <Route
        path="/entreprises/:id/dossiers/:dossierId/upload"
        element={<DossierUpload />}
        />
        <Route
  path="/entreprises/:id/dossiers/:dossierId/documents/:documentId"
  element={<DocumentDetails />}
/>
    </Routes>
    );
};

export default Router;