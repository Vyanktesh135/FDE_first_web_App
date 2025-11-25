import { Link } from "react-router";

export async function clientLoader(){
    const res = await fetch("/api/job_board");
    const job_boards = await res.json();
    return {job_boards}
}

export default function JobBoards({loaderData}) {
  return (
    <>
    <div>
      {loaderData.job_boards.map(
        (jobBoard) => 
            <div
              style={{
                fontWeight: "bolder",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                width: 150,
                gap: 8,  // optional spacing
              }}
            >
              <Link to={`/job-boards/${jobBoard.id}/job-posts`}>
                {jobBoard.slug}
              </Link>

              <img
                src={`/${jobBoard.logo}`}
                alt="Logo"
                style={{ width: 70, height: 70, objectFit: "contain" }}
              />
              {/* <button>Update Logo</button>
              <button>Delete JobBoard</button> */}
            </div>
      )}
    </div>
    {/* <button>Add JobBoards</button> */}
    
    <div>
      
    </div>
    </>
  )
}