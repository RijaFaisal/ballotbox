import { BrowserRouter, Route, Routes } from "react-router-dom";
import RequireAdmin from "./components/RequireAdmin.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import EntryForm from "./pages/EntryForm.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EntryForm />} />
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
