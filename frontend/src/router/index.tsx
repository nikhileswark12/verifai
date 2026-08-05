
import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "../components/layout/MainLayout";
import { Home } from "../pages/Home";
import { Research } from "../pages/Research";
import { Report } from "../pages/Report";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: "research",
        element: <Research />,
      },
      {
        path: "report/:jobId",
        element: <Report />,
      },
    ],
  },
]);
