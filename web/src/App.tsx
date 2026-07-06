import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { ProjectPage } from "./pages/Project";
import { DebatePage } from "./pages/Debate";
import { Rankings } from "./pages/Rankings";
import { About } from "./pages/About";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/project/:projectId" element={<ProjectPage />} />
        <Route path="/debate/:projectId" element={<DebatePage />} />
        <Route path="/rankings" element={<Rankings />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  );
}
