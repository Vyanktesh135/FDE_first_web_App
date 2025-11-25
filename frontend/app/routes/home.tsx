import { Link } from "react-router";

export default function Home({}){
    return(
        <main>
            <h1>Welcome to Jobify</h1>
            <Link to='/job-boards'>Job Boards</Link>
        </main>
    )
}