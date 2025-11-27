import { Outlet } from "react-router";
import './app.css';

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

