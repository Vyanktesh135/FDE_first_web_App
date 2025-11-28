import { Link } from "react-router";
export async function clientLoader({params}) {
    const res = await fetch(`/api/job-boards/${params.jobBoardId}/job-posts`);
    const jobPosts = await res.json()
    return {jobPosts}
}

export default function JobPosts({loaderData}) {
    return (
        <div>
            { loaderData.jobPosts.map((jobPost) =>
                <div>
                    <h2 key={jobPost.id}>
                        <Link 
                        to={`/job-application/new/${jobPost.id}`}>
                        {jobPost.title}
                        </Link>
                    </h2>
                    <p>{jobPost.description}</p>
                </div>
            )}
        </div>
    )
}