import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./screens/Login";

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
    </Routes>
    );
};

export default Router;