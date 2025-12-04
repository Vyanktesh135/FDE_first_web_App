import { NavLink, Outlet, type ClientActionFunctionArgs } from "react-router";
import { userContext } from "~/context";

export async function clientLoader({context} :ClientActionFunctionArgs){
  const me = context.get(userContext)
  const isAdmin = me && me.is_admin
  console.log(isAdmin)
  return {isAdmin}
} 

export default function DefaultLayout({loaderData}) { 
  const navLinkStyle =
    ({isActive}) => {
      return {
        backgroundColor: isActive ? "yellow" : "inherit",
        padding: "6px 12px",
        borderRadius: "6px",
        textDecoration: "none",
        color: isActive ? "black" : "#333",
        fontSize: "14px",
        transition: "background-color .2s ease, color .2s ease",
        border: "1px solid transparent"
      }
    }

  return (
    <main style={{fontFamily: "Arial, sans-serif", padding: "20px"}}>
      <nav
        style={{
          fontWeight: "bolder",
          display: "flex",
          justifyContent: "space-between",
          
          width: "100%",
          maxWidth: "100%",
          padding: "10px 20px",

          background: "#f5f5f5",
          borderRadius: "8px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.1)"
        }}
      >
        <NavLink to="/" style={navLinkStyle}>Home</NavLink>
        <NavLink to="/job-boards" style={navLinkStyle}>JobBoards</NavLink>
        { loaderData.isAdmin ? (
          <NavLink to="/admin-logout"  style={navLinkStyle}>Logout</NavLink>
        ) : (
          <NavLink to="/admin-login" style={navLinkStyle}>Login</NavLink>
        )}
      </nav>

      <div style={{marginTop: "20px"}}>
        <Outlet/>
      </div>
    </main>
  );
}
