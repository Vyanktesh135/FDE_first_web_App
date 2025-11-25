import { NavLink, Outlet } from "react-router";

export default function DefaultLayout() { 
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
    </nav>
    <Outlet/>
  </main>);
}

 