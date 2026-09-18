import { BrowserRouter, Route, Routes } from "react-router-dom";
import RequireAdmin from "./components/RequireAdmin.jsx";
import AdminControls from "./pages/AdminControls.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import AdminProductDetail from "./pages/AdminProductDetail.jsx";
import AdminProductNew from "./pages/AdminProductNew.jsx";
import AdminProducts from "./pages/AdminProducts.jsx";
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
        <Route
          path="/admin/products"
          element={
            <RequireAdmin>
              <AdminProducts />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/products/new"
          element={
            <RequireAdmin>
              <AdminProductNew />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/products/:productId"
          element={
            <RequireAdmin>
              <AdminProductDetail />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/controls"
          element={
            <RequireAdmin>
              <AdminControls />
            </RequireAdmin>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
