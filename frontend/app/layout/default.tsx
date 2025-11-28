import { NavLink, Outlet, type ClientActionFunctionArgs } from "react-router";
import { userContext } from "~/context";

export async function clientLoader({context} :ClientActionFunctionArgs){
  const me = context.get(userContext)
  const isAdmin = me && me.is_admin
  console.log(isAdmin)
  return {isAdmin}
} 
export default function DefaultLayout({loaderData}) { 
  const navLinkStyle=
    ({isActive}) => {
      return {backgroundColor: isActive ? "yellow" : "inherit"}
    }
  return (<main>
    <nav style={{fontWeight: 'bolder', 
                 display: 'flex', 
                 justifyContent: 'space-between', 
                 width: 150}}>
      <NavLink to="/" style={navLinkStyle}>Home</NavLink>
      <NavLink to="/job-boards" style={navLinkStyle}>JobBoards</NavLink>
      { loaderData.isAdmin ?
      <NavLink to="/admin-logout"  style={navLinkStyle} >Logout</NavLink>
      :<NavLink to="/admin-login"  style={navLinkStyle} >Login</NavLink>
      }
    </nav>
    <Outlet/>
  </main>);
}

 