import { Link } from "react-router";

export default function Home({}){
    return(
        <main>
            <h1 className="text-3xl font-medium">Welcome to Jobify</h1>
            <p className="md"><Link to='/job-boards'>You can search your next job stop here ..!</Link></p>
        </main>
    )
}