import { BrowserRouter, Route, Routes } from "react-router-dom";
import RequireAdmin from "./components/RequireAdmin.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import ComingSoon from "./pages/ComingSoon.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* The real per-product entry page (product dropdown, name +
            email/CNIC) replaces this placeholder in the next phase. */}
        <Route path="/" element={<ComingSoon />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminDashboard />
            </RequireAdmin>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
