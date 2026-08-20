import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Energy from "./pages/Energy";
import Devices from "./pages/Devices";
import Prediction from "./pages/Prediction";
import Anomaly from "./pages/Anomaly";
import Strategy from "./pages/Strategy";
import Insights from "./pages/Insights";
import Assistant from "./pages/Assistant";
import Butler from "./pages/Butler";
import Life from "./pages/Life";
import Sources from "./pages/Sources";
import Models from "./pages/Models";
import Guide from "./pages/Guide";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/energy" element={<Energy />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/prediction" element={<Prediction />} />
        <Route path="/anomaly" element={<Anomaly />} />
        <Route path="/strategy" element={<Strategy />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/assistant" element={<Assistant />} />
        <Route path="/butler" element={<Butler />} />
        <Route path="/life" element={<Life />} />
        <Route path="/sources" element={<Sources />} />
        <Route path="/models" element={<Models />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
