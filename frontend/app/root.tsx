import { Outlet } from "react-router";

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

