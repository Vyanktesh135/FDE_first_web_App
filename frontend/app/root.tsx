import { Outlet } from "react-router";
import './app.css';
import { authMiddleware } from "./middleware";
import type { Route } from "./+types/root";

export const clientMiddleware: Route.ClientMiddlewareFunction[] = [authMiddleware];
export default function App() {
  return (
    <html>
      <head>
        <title>Jobify</title>
      </head>
      <body>
        <Outlet></Outlet>
      </body>
    </html>
  )
}

