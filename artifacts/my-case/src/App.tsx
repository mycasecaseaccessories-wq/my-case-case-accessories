import { Route, Router, Switch } from "wouter";
import StorefrontPage from "./pages/storefront";
import AdminHomePage from "./pages/admin/home";
import AdminLoginPage from "./pages/admin/login";
import AdminDashboardPage from "./pages/admin/dashboard";
import AdminCatalogPage from "./pages/admin/catalog";
import AdminInventoryPage from "./pages/admin/inventory";
import PosPage from "./pages/pos";
import MiniAppPage from "./pages/mini/page";
import NotFound from "./pages/not-found";

export default function App() {
  return (
    <Router base={(import.meta.env.BASE_URL || "/").replace(/\/$/, "")}>
      <Switch>
        <Route path="/" component={StorefrontPage} />
        <Route path="/admin" component={AdminHomePage} />
        <Route path="/admin/login" component={AdminLoginPage} />
        <Route path="/admin/dashboard" component={AdminDashboardPage} />
        <Route path="/admin/catalog" component={AdminCatalogPage} />
        <Route path="/admin/inventory" component={AdminInventoryPage} />
        <Route path="/pos" component={PosPage} />
        <Route path="/mini-app" component={MiniAppPage} />
        <Route component={NotFound} />
      </Switch>
    </Router>
  );
}